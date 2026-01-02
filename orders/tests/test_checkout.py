from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from authentication.models import Address
from cart.models import Cart, CartItem
from discounts.models import Discount, DiscountRedemption
from orders.models import Order
from products.models import Category, Product


@override_settings(
    SECURE_SSL_REDIRECT=False,
    ALLOWED_HOSTS=["testserver"],
    STRIPE_SECRET_KEY="sk_test_dummy",
)
class CheckoutTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="buyer", password="pass"
        )  # nosec B106
        self.client = APIClient()
        self.client.force_authenticate(self.user)

        self.address = Address.objects.create(
            user=self.user,
            street="123 Main St",
            city="Springfield",
            state="IL",
            country="USA",
            zip_code="12345",
        )
        self.category = Category.objects.create(name="Skincare")
        self.product = Product.objects.create(
            product_name="Sample Lotion",
            category=self.category,
            price="19.99",
            inventory=10,
        )
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
            unit_price=self.product.price,
        )
        self.url = reverse("order-list", kwargs={"version": "v1"})

    @patch("orders.services.stripe.PaymentIntent.modify")
    @patch("orders.services.stripe.PaymentIntent.create")
    def test_checkout_creates_order_and_clears_cart(
        self, mock_create, mock_modify
    ):
        mock_create.return_value = SimpleNamespace(id="pi_123")

        response = self.client.post(
            self.url,
            {"shipping_address_id": self.address.id},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        order = Order.objects.get(id=response.data["id"])
        self.assertEqual(order.payment_intent_id, "pi_123")
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().product, self.product)
        self.assertFalse(CartItem.objects.filter(cart=self.cart).exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.inventory, 8)
        mock_modify.assert_called()

    @patch("orders.services.stripe.PaymentIntent.modify")
    @patch("orders.services.stripe.PaymentIntent.create")
    def test_idempotent_checkout_reuses_order(
        self, mock_create, mock_modify
    ):
        mock_create.return_value = SimpleNamespace(id="pi_456")
        response1 = self.client.post(
            self.url,
            {"shipping_address_id": self.address.id},
            format="json",
            HTTP_IDEMPOTENCY_KEY="checkout-123",
        )
        response2 = self.client.post(
            self.url,
            {"shipping_address_id": self.address.id},
            format="json",
            HTTP_IDEMPOTENCY_KEY="checkout-123",
        )

        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response1.data["id"], response2.data["id"])
        self.assertEqual(Order.objects.count(), 1)

    @patch("orders.services.stripe.PaymentIntent.modify")
    @patch("orders.services.stripe.PaymentIntent.create")
    def test_checkout_applies_discount_code(
        self, mock_create, mock_modify
    ):
        mock_create.return_value = SimpleNamespace(id="pi_789")
        discount = Discount.objects.create(
            code="SAVE10",
            name="Save 10%",
            discount_type="percentage",
            value="10.00",
            is_active=True,
        )

        response = self.client.post(
            self.url,
            {"shipping_address_id": self.address.id, "discount_code": "SAVE10"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        order = Order.objects.get(id=response.data["id"])
        self.assertEqual(order.discount_code, "SAVE10")
        self.assertEqual(order.discount_type, "percentage")
        self.assertEqual(str(order.discount_amount), "4.00")
        self.assertEqual(str(order.total_price), "35.98")
        discount.refresh_from_db()
        self.assertEqual(discount.times_used, 1)
        self.assertTrue(
            DiscountRedemption.objects.filter(discount=discount, order=order).exists()
        )
