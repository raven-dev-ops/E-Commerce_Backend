from rest_framework import serializers

from products.models import Product
from reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    product_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "product_id",
            "user_id",
            "username",
            "rating",
            "title",
            "body",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user_id",
            "username",
            "status",
            "created_at",
            "updated_at",
        ]


class ReviewWriteSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        source="product", queryset=Product.objects.all()
    )

    class Meta:
        model = Review
        fields = [
            "id",
            "product_id",
            "rating",
            "title",
            "body",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if "status" in attrs and (not user or not user.is_staff):
            raise serializers.ValidationError(
                {"status": "Only admins can change review status."}
            )

        if self.instance and "product" in attrs:
            if attrs["product"].id != self.instance.product_id:
                raise serializers.ValidationError(
                    {"product_id": "Product cannot be changed."}
                )

        if not self.instance and user and user.is_authenticated:
            product = attrs.get("product")
            if product and Review.objects.filter(
                product=product, user=user
            ).exists():
                raise serializers.ValidationError(
                    {"product_id": "You have already reviewed this product."}
                )

        return attrs
