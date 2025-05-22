# orders/serializers.py

from rest_framework import serializers
from orders.models import Cart, CartItem, Order, OrderItem
from authentication.serializers import AddressSerializer
from rest_framework_mongoengine.serializers import DocumentSerializer
from discounts.serializers import DiscountSerializer


class CartItemSerializer(serializers.Serializer):
    product_id = serializers.CharField(max_length=24)  # MongoDB ObjectId length
    quantity = serializers.IntegerField(min_value=1)


class CartSerializer(serializers.Serializer):
    user = serializers.IntegerField()  # Django user ID
    items = CartItemSerializer(many=True)
    discount = DiscountSerializer(read_only=True, allow_null=True)

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        cart = Cart(**validated_data)
        cart.items = [CartItem(**item) for item in items_data]
        cart.save()
        return cart

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items')
        instance.user = validated_data.get('user', instance.user)
        instance.items = [CartItem(**item) for item in items_data]
        instance.save()
        return instance


class OrderItemSerializer(DocumentSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price']  # Adjust fields to your model


class OrderSerializer(DocumentSerializer):
    items = OrderItemSerializer(many=True)
    shipping_address = AddressSerializer(read_only=True)
    billing_address = AddressSerializer(read_only=True)
    discount = DiscountSerializer(read_only=True, allow_null=True)

    class Meta:
        model = Order
        fields = [
            'user',
            'items',
            'total_price',
            'shipping_cost',
            'tax_amount',
            'payment_intent_id',
            'status',
            'shipping_address',
            'billing_address',
            'created_at',
            'shipped_date',
            'discount_code',
            'discount_type',
            'discount_value',
            'discount_amount',
            'discount',
        ]
