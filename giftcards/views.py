from django.db import connection, transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import GiftCard
from backend.serializers.giftcards import (
    GiftCardPurchaseSerializer,
    GiftCardRedeemSerializer,
    GiftCardSerializer,
)


class GiftCardViewSet(viewsets.ModelViewSet):
    queryset = GiftCard.objects.all()
    serializer_class = GiftCardSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        admin_actions = {
            "list",
            "retrieve",
            "create",
            "update",
            "partial_update",
            "destroy",
        }
        if self.action in admin_actions:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_staff:
            return GiftCard.objects.all()
        return GiftCard.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = GiftCardPurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]
        card = GiftCard.objects.create(
            amount=amount, balance=amount, issued_by=request.user
        )
        output = GiftCardSerializer(card)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def redeem(self, request, *args, **kwargs):
        serializer = GiftCardRedeemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            queryset = GiftCard.objects.filter(
                code=serializer.validated_data["code"],
                is_active=True,
                balance__gt=0,
            )
            if connection.features.has_select_for_update:
                queryset = queryset.select_for_update()
                card = queryset.first()
                if not card:
                    return Response(
                        {"detail": "Gift card not found or already redeemed."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                card.is_active = False
                card.balance = 0
                card.redeemed_at = timezone.now()
                card.redeemed_by = request.user
                card.save(
                    update_fields=[
                        "is_active",
                        "balance",
                        "redeemed_at",
                        "redeemed_by",
                    ]
                )
            else:
                redeemed_at = timezone.now()
                updated = queryset.update(
                    is_active=False,
                    balance=0,
                    redeemed_at=redeemed_at,
                    redeemed_by=request.user,
                )
                if not updated:
                    return Response(
                        {"detail": "Gift card not found or already redeemed."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                card = GiftCard.objects.get(code=serializer.validated_data["code"])
        output = GiftCardSerializer(card)
        return Response(output.data)
