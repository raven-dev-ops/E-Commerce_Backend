from decimal import Decimal, InvalidOperation

from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from backend.permissions import IsAdminOrReadOnly
from products.models import Product
from products.pagination import CustomProductPagination
from products.serializers import ProductSerializer, ProductWriteSerializer


class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = CustomProductPagination
    lookup_field = "slug"

    def get_queryset(self):
        queryset = Product.objects.select_related("category")
        if not self.request.user.is_staff:
            queryset = queryset.published()

        category = self.request.query_params.get("category")
        if category:
            if category.isdigit():
                queryset = queryset.filter(category_id=category)
            else:
                queryset = queryset.filter(
                    Q(category__slug=category) | Q(category__name__iexact=category)
                )

        min_price = self.request.query_params.get("min_price")
        if min_price:
            try:
                queryset = queryset.filter(price__gte=Decimal(min_price))
            except InvalidOperation:
                pass

        max_price = self.request.query_params.get("max_price")
        if max_price:
            try:
                queryset = queryset.filter(price__lte=Decimal(max_price))
            except InvalidOperation:
                pass

        query = self.request.query_params.get("q")
        if query:
            queryset = queryset.filter(
                Q(product_name__icontains=query) | Q(description__icontains=query)
            )

        ordering = self.request.query_params.get("ordering")
        allowed_ordering = {
            "product_name",
            "-product_name",
            "price",
            "-price",
            "created_at",
            "-created_at",
        }
        if ordering in allowed_ordering:
            queryset = queryset.order_by(ordering)

        return queryset

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return ProductWriteSerializer
        return ProductSerializer

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request, *args, **kwargs):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response([])
        queryset = self.get_queryset().filter(
            Q(product_name__icontains=query) | Q(description__icontains=query)
        )
        serializer = ProductSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="availability")
    def availability(self, request, *args, **kwargs):
        product = self.get_object()
        quantity_param = request.query_params.get("quantity")
        quantity = 1
        if quantity_param is not None:
            try:
                quantity = int(quantity_param)
            except (TypeError, ValueError):
                return Response(
                    {"detail": "quantity must be a positive integer."}, status=400
                )
            if quantity < 1:
                return Response(
                    {"detail": "quantity must be a positive integer."}, status=400
                )

        available = product.inventory >= quantity
        return Response(
            {
                "product_id": product.id,
                "inventory": product.inventory,
                "requested_quantity": quantity,
                "available": available,
            }
        )
