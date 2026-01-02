from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from products.models import Category, Product


@override_settings(SECURE_SSL_REDIRECT=False)
class ProductAvailabilityTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Gadgets")
        self.product = Product.objects.create(
            product_name="Widget",
            price=25,
            inventory=5,
            category=self.category,
        )

    def test_availability_default_quantity(self):
        url = reverse(
            "product-availability",
            kwargs={"version": "v1", "slug": self.product.slug},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["available"])
        self.assertEqual(payload["requested_quantity"], 1)
        self.assertEqual(payload["inventory"], 5)

    def test_availability_insufficient_inventory(self):
        url = reverse(
            "product-availability",
            kwargs={"version": "v1", "slug": self.product.slug},
        )
        response = self.client.get(url, {"quantity": 10})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["available"])
        self.assertEqual(payload["requested_quantity"], 10)

    def test_availability_invalid_quantity(self):
        url = reverse(
            "product-availability",
            kwargs={"version": "v1", "slug": self.product.slug},
        )
        response = self.client.get(url, {"quantity": "nope"})

        self.assertEqual(response.status_code, 400)
