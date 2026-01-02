from rest_framework import serializers

from discounts.models import Discount
from products.models import Category, Product


class DiscountSerializer(serializers.ModelSerializer):
    category_ids = serializers.PrimaryKeyRelatedField(
        source="categories",
        queryset=Category.objects.all(),
        many=True,
        required=False,
    )
    product_ids = serializers.PrimaryKeyRelatedField(
        source="products",
        queryset=Product.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Discount
        fields = [
            "id",
            "code",
            "name",
            "description",
            "discount_type",
            "value",
            "is_active",
            "starts_at",
            "ends_at",
            "max_uses",
            "max_uses_per_user",
            "min_order_amount",
            "times_used",
            "category_ids",
            "product_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["times_used", "created_at", "updated_at"]

    def validate(self, attrs):
        discount_type = attrs.get("discount_type") or getattr(
            self.instance, "discount_type", None
        )
        value = attrs.get("value") or getattr(self.instance, "value", None)
        if value is not None:
            if discount_type == Discount.Type.PERCENTAGE:
                if value <= 0 or value > 100:
                    raise serializers.ValidationError(
                        {"value": "Percentage discounts must be between 0 and 100."}
                    )
            elif discount_type == Discount.Type.FIXED:
                if value <= 0:
                    raise serializers.ValidationError(
                        {"value": "Fixed discounts must be greater than 0."}
                    )
        starts_at = attrs.get("starts_at") or getattr(self.instance, "starts_at", None)
        ends_at = attrs.get("ends_at") or getattr(self.instance, "ends_at", None)
        if starts_at and ends_at and starts_at >= ends_at:
            raise serializers.ValidationError(
                {"ends_at": "End date must be later than start date."}
            )
        min_order_amount = attrs.get("min_order_amount")
        if min_order_amount is not None and min_order_amount < 0:
            raise serializers.ValidationError(
                {"min_order_amount": "Minimum order amount must be zero or greater."}
            )
        return attrs


class DiscountPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = [
            "code",
            "name",
            "description",
            "discount_type",
            "value",
            "min_order_amount",
            "starts_at",
            "ends_at",
        ]
