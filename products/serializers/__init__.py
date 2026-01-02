from rest_framework import serializers

from products.models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    images = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = Product
        fields = [
            "id",
            "product_name",
            "slug",
            "description",
            "price",
            "currency",
            "inventory",
            "is_active",
            "publish_at",
            "unpublish_at",
            "category",
            "tags",
            "images",
            "average_rating",
            "rating_count",
            "erp_id",
            "created_at",
            "updated_at",
        ]


class ProductWriteSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        source="category", queryset=Category.objects.all(), write_only=True
    )
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    images = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = Product
        fields = [
            "id",
            "product_name",
            "slug",
            "description",
            "price",
            "currency",
            "inventory",
            "is_active",
            "publish_at",
            "unpublish_at",
            "category_id",
            "tags",
            "images",
            "erp_id",
        ]
        read_only_fields = ["id", "slug"]

    def validate(self, attrs):
        publish_at = attrs.get("publish_at", getattr(self.instance, "publish_at", None))
        unpublish_at = attrs.get(
            "unpublish_at", getattr(self.instance, "unpublish_at", None)
        )
        if publish_at and unpublish_at and unpublish_at <= publish_at:
            raise serializers.ValidationError(
                {"unpublish_at": "Unpublish time must be after publish time."}
            )
        return attrs


__all__ = ["CategorySerializer", "ProductSerializer", "ProductWriteSerializer"]
