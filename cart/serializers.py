# cart/serializers.py

from rest_framework import serializers
from rest_framework_mongoengine.serializers import DocumentSerializer
from .models import Cart, CartItem
from products.models import Product  # Assuming MongoEngine Document Product

class ProductSerializer(DocumentSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class CartItemSerializer(DocumentSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.CharField(write_only=True)  # To create/update CartItem

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'product_id', 'quantity')

    def create(self, validated_data):
        product_id = validated_data.pop('product_id')
        product = Product.objects.get(id=product_id)
        return CartItem.objects.create(product=product, **validated_data)

class CartSerializer(DocumentSerializer):
    items = CartItemSerializer(many=True)

    class Meta:
        model = Cart
        fields = ('id', 'user', 'items')

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        cart = Cart.objects.create(**validated_data)
        for item_data in items_data:
            item_serializer = CartItemSerializer(data=item_data)
            item_serializer.is_valid(raise_exception=True)
            cart_item = item_serializer.save()
            cart.items.append(cart_item)
        cart.save()
        return cart

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items')
        # update user or other fields if needed
        instance.update(**validated_data)

        # Clear old items and add new ones for simplicity
        for item in instance.items:
            item.delete()
        instance.items = []

        for item_data in items_data:
            item_serializer = CartItemSerializer(data=item_data)
            item_serializer.is_valid(raise_exception=True)
            cart_item = item_serializer.save()
            instance.items.append(cart_item)
        instance.save()
        return instance
