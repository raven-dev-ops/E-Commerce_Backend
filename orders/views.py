# orders/views.py

from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from datetime import datetime
import stripe
from .models import Cart, CartItem, Order, OrderItem
from products.models import Product
from authentication.models import Address
from .serializers import OrderSerializer

stripe.api_key = 'your_stripe_secret_key'  # Make sure to set this securely in settings

class OrderViewSet(ViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request):
        user = request.user

        shipping_address_id = request.data.get('shipping_address_id')
        billing_address_id = request.data.get('billing_address_id')

        # Get default addresses if none provided
        shipping_address = Address.objects.filter(user=user.id, is_default_shipping=True).first()
        billing_address = Address.objects.filter(user=user.id, is_default_billing=True).first()

        # Override with provided IDs if available
        if shipping_address_id:
            shipping_address = get_object_or_404(Address, id=shipping_address_id, user=user.id)
        if billing_address_id:
            billing_address = get_object_or_404(Address, id=billing_address_id, user=user.id)

        if not shipping_address:
            return Response({"detail": "Shipping address is required (default or specified)."},
                            status=status.HTTP_400_BAD_REQUEST)
        if not billing_address:
            return Response({"detail": "Billing address is required (default or specified)."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Get user's cart
        cart = Cart.objects.filter(user=user.id).first()
        if not cart or not cart.items:
            return Response({"detail": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        order_items = []
        subtotal = 0

        for item in cart.items:
            try:
                product = Product.objects.get(id=item.product_id)
            except Product.DoesNotExist:
                return Response({"detail": f"Product with ID {item.product_id} not found."},
                                status=status.HTTP_404_NOT_FOUND)
            
            order_item = OrderItem(
                product=str(product.id),  # Store product ID as string
                quantity=item.quantity,
                price=product.price  # Use current product price
            )
            order_items.append(order_item)
            subtotal += product.price * item.quantity

        # Shipping and tax calculations (example values)
        shipping_cost = 5.00
        tax_rate = 0.08

        discount_amount = 0
        if cart.discount and cart.discount.is_free_shipping:
            shipping_cost = 0  # Free shipping discount

        discount_details = None
        if cart.discount:
            discount = cart.discount
            discount_details = {
                'code': discount.code,
                'type': discount.discount_type,
                'value': discount.value,
                'amount': 0
            }

            if discount.discount_type == 'percentage':
                discount_amount = (subtotal * discount.value) / 100
                discount_amount = min(discount_amount, subtotal)
            elif discount.discount_type == 'fixed':
                discount_amount = min(discount.value, subtotal)

            discount_details['amount'] = round(discount_amount, 2)
            subtotal -= discount_amount

            # Increase times used, will save after order is created
            discount.times_used += 1

        tax_amount = round(subtotal * tax_rate, 2)
        total_price = subtotal + shipping_cost + tax_amount

        # Payment method ID required for Stripe
        payment_method_id = request.data.get('payment_method_id')
        if not payment_method_id:
            return Response({"detail": "Payment method ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Process Stripe PaymentIntent
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(total_price * 100),  # Amount in cents
                currency='usd',
                payment_method=payment_method_id,
                confirmation_method='manual',
                confirm=True,
                metadata={'user_id': user.id}
            )
        except stripe.error.CardError as e:
            return Response({"detail": f"Payment failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Payment processing error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Payment succeeded, create the Order
        order = Order.objects.create(
            user=user.id,
            shipping_address=str(shipping_address.id),
            billing_address=str(billing_address.id),
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            total_price=total_price,
            discount_code=discount_details['code'] if discount_details else None,
            discount_type=discount_details['type'] if discount_details else None,
            discount_amount=round(discount_amount, 2)
        )

        # Save order items to the order
        for order_item in order_items:
            order_item.order = order
            order_item.save()

        # Save discount times_used increment
        if cart.discount:
            discount.save()

        # Clear user's cart after order placement
        cart.items = []
        cart.discount = None
        cart.save()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
