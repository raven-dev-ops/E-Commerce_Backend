from django.db import connection, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import Cart, CartItem
from cart.serializers import (
    CartItemDeleteSerializer,
    CartItemWriteSerializer,
    CartSerializer,
)
from products.models import Product


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def _for_update(self, queryset):
        if connection.features.has_select_for_update:
            return queryset.select_for_update()
        return queryset

    def _get_cart(self, user) -> Cart:
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart

    def _serialize_cart(self, cart: Cart) -> Response:
        cart = Cart.objects.prefetch_related("items__product").get(pk=cart.pk)
        return Response(CartSerializer(cart).data)

    def get(self, request, *args, **kwargs):
        cart = self._get_cart(request.user)
        return self._serialize_cart(cart)

    def post(self, request, *args, **kwargs):
        serializer = CartItemWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data["quantity"]

        with transaction.atomic():
            product = self._for_update(Product.objects).get(pk=product.pk)
            if not product.is_published():
                return Response(
                    {"detail": "Product is unavailable."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if quantity > product.inventory:
                return Response(
                    {"detail": "Insufficient inventory."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cart = self._get_cart(request.user)
            item, created = self._for_update(CartItem.objects).get_or_create(
                cart=cart,
                product=product,
                defaults={"quantity": quantity, "unit_price": product.price},
            )
            if not created:
                new_quantity = item.quantity + quantity
                if new_quantity > product.inventory:
                    return Response(
                        {"detail": "Insufficient inventory."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                item.quantity = new_quantity
                item.unit_price = product.price
                item.save(update_fields=["quantity", "unit_price", "updated_at"])
            cart.touch()

        response = self._serialize_cart(cart)
        response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return response

    def put(self, request, *args, **kwargs):
        serializer = CartItemWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data["quantity"]

        with transaction.atomic():
            product = self._for_update(Product.objects).get(pk=product.pk)
            if not product.is_published():
                return Response(
                    {"detail": "Product is unavailable."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if quantity > product.inventory:
                return Response(
                    {"detail": "Insufficient inventory."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cart = self._get_cart(request.user)
            item = get_object_or_404(CartItem, cart=cart, product=product)
            item.quantity = quantity
            item.unit_price = product.price
            item.save(update_fields=["quantity", "unit_price", "updated_at"])
            cart.touch()

        return self._serialize_cart(cart)

    def delete(self, request, *args, **kwargs):
        if request.data:
            serializer = CartItemDeleteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            product = serializer.validated_data["product"]
        else:
            product = None

        cart = self._get_cart(request.user)
        if product:
            CartItem.objects.filter(cart=cart, product=product).delete()
        else:
            cart.items.all().delete()
        cart.touch()
        return self._serialize_cart(cart)
