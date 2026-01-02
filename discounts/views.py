from decimal import Decimal, InvalidOperation

from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from backend.permissions import IsAdminOrReadOnly
from discounts.models import Discount, DiscountRedemption
from discounts.serializers import DiscountPublicSerializer, DiscountSerializer
from products.models import Category
from products.serializers import CategorySerializer


class DiscountViewSet(viewsets.ModelViewSet):
    serializer_class = DiscountSerializer
    permission_classes = [IsAdminUser]
    lookup_field = "code"
    lookup_value_regex = "[^/]+"

    def get_queryset(self):
        return Discount.objects.prefetch_related("categories", "products")


class DiscountValidateAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        code = (request.data.get("code") or "").strip().upper()
        if not code:
            return Response(
                {"detail": "code is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        discount = Discount.objects.filter(code=code).first()
        if not discount or not discount.is_available():
            return Response(
                {"detail": "Invalid or inactive discount."},
                status=status.HTTP_404_NOT_FOUND,
            )
        user = request.user if request.user.is_authenticated else None
        if discount.max_uses_per_user is not None and user:
            redemptions = DiscountRedemption.objects.filter(
                discount=discount, user=user
            ).count()
            if redemptions >= discount.max_uses_per_user:
                return Response(
                    {"detail": "Discount usage limit reached."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        order_total = request.data.get("order_total")
        if order_total is not None:
            try:
                total_value = Decimal(str(order_total))
            except (TypeError, ValueError, InvalidOperation):
                return Response(
                    {"detail": "order_total must be a number."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if total_value < discount.min_order_amount:
                return Response(
                    {"detail": "Order total does not meet minimum amount."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        serializer = DiscountPublicSerializer(discount)
        return Response(serializer.data)


class CategoryListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = Category.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset


class CategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    lookup_field = "pk"
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = Category.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset
