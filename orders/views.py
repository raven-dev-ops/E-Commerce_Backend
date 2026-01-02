# orders/views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import (
    action,
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.conf import settings
from django.db import transaction
from django.utils.dateparse import parse_datetime
import hashlib
import hmac
import logging
import time

from .tasks import send_order_confirmation_email
from .services import (
    create_order_from_cart,
    generate_invoice_pdf,
    transition_order_status,
)

from orders.models import Order, ShipmentWebhookEvent  # Django ORM
from backend.serializers.orders import OrderCreateSerializer, OrderSerializer

logger = logging.getLogger(__name__)


class OrderViewSet(viewsets.ViewSet):
    """
    Order endpoints (list, retrieve, create) using Django ORM.
    The backend validates cart contents and pricing.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        """List all orders for current user."""
        orders = (
            Order.objects.filter(user=request.user)
            .select_related("shipping_address", "billing_address")
            .prefetch_related("items")
            .order_by("-created_at")
        )
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        """Get a specific order by ID (must belong to user)."""
        order = get_object_or_404(
            Order.objects.select_related(
                "shipping_address", "billing_address"
            ).prefetch_related("items"),
            pk=pk,
            user=request.user,
        )
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="invoice")
    def invoice(self, request, pk=None, *args, **kwargs):
        """Download the invoice for the order as a PDF."""

        order = get_object_or_404(
            Order.objects.prefetch_related("items"), pk=pk, user=request.user
        )
        pdf_bytes = generate_invoice_pdf(order)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="invoice_{order.id}.pdf"'
        )
        return response

    def create(self, request, *args, **kwargs):
        """Checkout: Create an order from user's cart."""
        payload = request.data.copy()
        header_key = request.headers.get("Idempotency-Key")
        if header_key and "idempotency_key" not in payload:
            payload["idempotency_key"] = header_key

        serializer = OrderCreateSerializer(data=payload, context={"request": request})
        serializer.is_valid(raise_exception=True)

        try:
            order = create_order_from_cart(request.user, serializer.validated_data)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        created = getattr(order, "_created", True)
        order = (
            Order.objects.select_related("shipping_address", "billing_address")
            .prefetch_related("items")
            .get(pk=order.pk)
        )
        serializer = OrderSerializer(order)
        if created:
            send_order_confirmation_email.delay(order.id, request.user.email)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None, *args, **kwargs):
        """Cancel an order and restore reserved inventory."""
        order = get_object_or_404(
            Order.objects.select_related(
                "shipping_address", "billing_address"
            ).prefetch_related("items"),
            pk=pk,
            user=request.user,
        )
        if order.status not in {Order.Status.PENDING, Order.Status.PROCESSING}:
            return Response(
                {"detail": "Only pending or processing orders can be canceled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        transition_order_status(order, Order.Status.CANCELED)
        serializer = OrderSerializer(order)
        return Response(serializer.data)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def shipment_tracking_webhook(request, version):
    """Receive shipment tracking updates from external carriers."""
    secret = getattr(settings, "SHIPMENT_WEBHOOK_SECRET", "")
    if not secret:
        logger.error("Shipment webhook secret is not configured.")
        return Response(
            {"detail": "Webhook secret not configured."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    signature = request.headers.get("X-Webhook-Signature", "")
    timestamp = request.headers.get("X-Webhook-Timestamp", "")
    if not signature or not timestamp:
        return Response(
            {"detail": "Signature headers are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        timestamp_value = int(timestamp)
    except (TypeError, ValueError):
        return Response(
            {"detail": "Invalid timestamp."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    tolerance = getattr(settings, "SHIPMENT_WEBHOOK_TOLERANCE", 300)
    now = int(time.time())
    if abs(now - timestamp_value) > tolerance:
        return Response(
            {"detail": "Request timestamp outside allowed window."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    signed_payload = f"{timestamp_value}.".encode("utf-8") + request.body
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_signature, signature):
        return Response(
            {"detail": "Invalid signature."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    event_id = request.data.get("event_id")
    order_id = request.data.get("order_id")
    status_value = request.data.get("status")
    if not event_id:
        return Response(
            {"detail": "event_id is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not order_id or not status_value:
        return Response(
            {"detail": "order_id and status are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    valid_statuses = {choice[0] for choice in Order.STATUS_CHOICES}
    if status_value not in valid_statuses:
        return Response(
            {"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST
        )

    shipped_date = request.data.get("shipped_date")
    parsed = parse_datetime(shipped_date) if shipped_date else None

    try:
        with transaction.atomic():
            order = Order.all_objects.select_for_update().get(pk=order_id)
            _, created = ShipmentWebhookEvent.objects.get_or_create(
                event_id=event_id,
                defaults={"order": order, "status": status_value},
            )
            if not created:
                return Response({"detail": "Duplicate event."})
            transition_order_status(order, status_value, shipped_date=parsed)
    except Order.DoesNotExist:
        return Response(
            {"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND
        )

    return Response({"detail": "Shipment update received."})
