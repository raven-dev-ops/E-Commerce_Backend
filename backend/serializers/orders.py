from rest_framework import serializers

from authentication.models import Address
from orders.models import Order, OrderItem
from backend.serializers.authentication import AddressSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product_id", "product_name", "quantity", "unit_price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address = AddressSerializer(read_only=True)
    billing_address = AddressSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "created_at",
            "total_price",
            "currency",
            "shipping_cost",
            "tax_amount",
            "payment_intent_id",
            "status",
            "shipping_address",
            "billing_address",
            "shipped_date",
            "discount_code",
            "discount_type",
            "discount_value",
            "discount_amount",
            "is_gift",
            "gift_message",
            "items",
        ]
        read_only_fields = [
            "id",
            "user",
            "created_at",
            "payment_intent_id",
            "status",
            "items",
            "currency",
        ]


class OrderCreateSerializer(serializers.Serializer):
    shipping_address_id = serializers.PrimaryKeyRelatedField(
        source="shipping_address",
        queryset=Address.objects.none(),
        required=False,
        allow_null=True,
    )
    billing_address_id = serializers.PrimaryKeyRelatedField(
        source="billing_address",
        queryset=Address.objects.none(),
        required=False,
        allow_null=True,
    )
    is_gift = serializers.BooleanField(required=False, default=False)
    gift_message = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=500
    )
    discount_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    currency = serializers.CharField(required=False, max_length=3, allow_blank=True)
    shipping_cost = serializers.DecimalField(
        required=False, max_digits=8, decimal_places=2
    )
    tax_amount = serializers.DecimalField(required=False, max_digits=8, decimal_places=2)
    idempotency_key = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            qs = Address.objects.filter(user=request.user)
            self.fields["shipping_address_id"].queryset = qs
            self.fields["billing_address_id"].queryset = qs

    def validate(self, attrs):
        if attrs.get("is_gift") and not attrs.get("gift_message"):
            raise serializers.ValidationError(
                {"gift_message": "Gift message is required for gift orders."}
            )
        for field in ("shipping_cost", "tax_amount"):
            value = attrs.get(field)
            if value is not None and value < 0:
                raise serializers.ValidationError(
                    {field: "Must be zero or greater."}
                )
        return attrs

