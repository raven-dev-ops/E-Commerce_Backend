from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from cart.models import CartItem
from products.models import Category, Product


@override_settings(SECURE_SSL_REDIRECT=False, ALLOWED_HOSTS=["testserver"])
class CartApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="buyer", password="pass"
        )  # nosec B106
        self.client = APIClient()
        self.client.force_authenticate(self.user)

        self.category = Category.objects.create(name="Skincare")
        self.product = Product.objects.create(
            product_name="Sample Lotion",
            category=self.category,
            price="19.99",
            inventory=10,
        )
        self.url = reverse("cart", kwargs={"version": "v1"})

    def test_get_cart_returns_empty(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["items"], [])

    def test_add_item_to_cart(self):
        response = self.client.post(
            self.url, {"product_id": self.product.id, "quantity": 2}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data["items"]), 1)
        item = CartItem.objects.get(product=self.product)
        self.assertEqual(item.quantity, 2)

    def test_update_item_quantity(self):
        self.client.post(
            self.url, {"product_id": self.product.id, "quantity": 1}, format="json"
        )
        response = self.client.put(
            self.url, {"product_id": self.product.id, "quantity": 3}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        item = CartItem.objects.get(product=self.product)
        self.assertEqual(item.quantity, 3)

    def test_delete_item_from_cart(self):
        self.client.post(
            self.url, {"product_id": self.product.id, "quantity": 1}, format="json"
        )
        response = self.client.delete(
            self.url, {"product_id": self.product.id}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CartItem.objects.filter(product=self.product).exists())
