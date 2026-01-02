# payments/views.py

import logging
from decimal import Decimal, ROUND_HALF_UP

import stripe
from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from orders.models import Order
from orders.services import transition_order_status
from payments.models import StripeWebhookEvent

logger = logging.getLogger(__name__)


def _to_stripe_amount(total: Decimal) -> int:
    return int((total * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _payment_intent_matches_order(order: Order, payment_intent) -> bool:
    amount = payment_intent.get("amount")
    currency = payment_intent.get("currency")
    if amount is not None:
        expected_amount = _to_stripe_amount(order.total_price)
        if amount != expected_amount:
            logger.warning(
                "Stripe amount mismatch for order %s: expected %s got %s",
                order.id,
                expected_amount,
                amount,
            )
            return False
    if currency and currency.lower() != order.currency.lower():
        logger.warning(
            "Stripe currency mismatch for order %s: expected %s got %s",
            order.id,
            order.currency,
            currency,
        )
        return False
    return True


def _get_order_from_payment_intent(payment_intent):
    payment_intent_id = payment_intent.get("id")
    metadata = payment_intent.get("metadata") or {}
    order_id = metadata.get("order_id")
    if order_id:
        order = (
            Order.objects.select_for_update()
            .filter(id=order_id)
            .first()
        )
        if order and payment_intent_id and order.payment_intent_id:
            if order.payment_intent_id != payment_intent_id:
                logger.warning(
                    "Stripe payment_intent mismatch for order %s: %s vs %s",
                    order.id,
                    order.payment_intent_id,
                    payment_intent_id,
                )
                return None
        if order:
            return order
    if payment_intent_id:
        return (
            Order.objects.select_for_update()
            .filter(payment_intent_id=payment_intent_id)
            .first()
        )
    return None


@csrf_exempt
def stripe_webhook_view(request, *args, **kwargs):
    stripe_secret = getattr(settings, "STRIPE_SECRET_KEY", None)
    webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", None)
    if (
        not stripe_secret
        or stripe_secret == "dummy"
        or not webhook_secret
        or webhook_secret == "dummy"
    ):
        missing = []
        if not stripe_secret or stripe_secret == "dummy":
            missing.append("STRIPE_SECRET_KEY")
        if not webhook_secret or webhook_secret == "dummy":
            missing.append("STRIPE_WEBHOOK_SECRET")
        logger.error("Missing Stripe configuration: %s", ", ".join(missing))
        return HttpResponse(status=503)

    stripe.api_key = stripe_secret

    payload = request.body
    sig_header = request.headers.get("Stripe-Signature")
    if not sig_header:
        logger.warning("Missing Stripe-Signature header.")
        return HttpResponse(status=400)

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            webhook_secret,
            tolerance=getattr(settings, "STRIPE_WEBHOOK_TOLERANCE", 300),
        )
    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)

    event_id = event.get("id")
    event_type = event.get("type")
    if not event_id or not event_type:
        logger.warning("Stripe event missing id or type.")
        return HttpResponse(status=400)

    try:
        _, created = StripeWebhookEvent.objects.get_or_create(
            event_id=event_id,
            defaults={
                "event_type": event_type,
                "livemode": bool(event.get("livemode", False)),
            },
        )
    except IntegrityError:
        logger.info("Duplicate Stripe webhook event %s ignored.", event_id)
        return HttpResponse(status=200)
    if not created:
        logger.info("Duplicate Stripe webhook event %s ignored.", event_id)
        return HttpResponse(status=200)

    # Handle Stripe event types
    if event_type in {"payment_intent.succeeded", "payment_intent.payment_failed"}:
        payment_intent = event.get("data", {}).get("object", {})
        payment_intent_id = payment_intent.get("id")
        if not payment_intent_id:
            logger.warning("Stripe event missing payment_intent id.")
            return HttpResponse(status=400)
        with transaction.atomic():
            order = _get_order_from_payment_intent(payment_intent)
            if not order:
                logger.warning(
                    "Order with payment_intent_id %s not found", payment_intent_id
                )
                return HttpResponse(status=200)
            if not _payment_intent_matches_order(order, payment_intent):
                return HttpResponse(status=200)
            if event_type == "payment_intent.succeeded":
                if order.status == Order.Status.PENDING:
                    transition_order_status(order, Order.Status.PROCESSING)
                    logger.info("Order %s status updated to Processing", order.id)
            elif event_type == "payment_intent.payment_failed":
                if order.status in {Order.Status.PENDING, Order.Status.PROCESSING}:
                    transition_order_status(order, Order.Status.FAILED)
                    logger.info("Order %s status updated to Payment Failed", order.id)
    else:
        logger.info(
            "Unhandled Stripe webhook event type: %s (ID %s)",
            event_type,
            event_id,
        )

    return HttpResponse(status=200)
