from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from products.models import Category, Product


@override_settings(SECURE_SSL_REDIRECT=False, ALLOWED_HOSTS=["testserver"])
class ProductApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="admin", password="pass", is_staff=True
        )  # nosec B106
        self.user = User.objects.create_user(
            username="buyer", password="pass"
        )  # nosec B106
        self.category = Category.objects.create(
            name="Skincare", description="Skincare products"
        )
        self.product = Product.objects.create(
            product_name="Sample Lotion",
            category=self.category,
            description="Demo product",
            price="19.99",
            inventory=25,
        )

    def test_list_products(self):
        url = reverse("product-list", kwargs={"version": "v1"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_retrieve_product_by_slug(self):
        url = reverse(
            "product-detail", kwargs={"version": "v1", "slug": self.product.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["product_name"], self.product.product_name)

    def test_filter_products_by_category_slug(self):
        url = reverse("product-list", kwargs={"version": "v1"})
        response = self.client.get(url, {"category": self.category.slug})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_list_products_respects_publish_window(self):
        now = timezone.now()
        Product.objects.create(
            product_name="Future Product",
            category=self.category,
            description="Not yet live",
            price="9.99",
            inventory=5,
            publish_at=now + timedelta(days=1),
        )
        Product.objects.create(
            product_name="Expired Product",
            category=self.category,
            description="No longer live",
            price="14.99",
            inventory=5,
            unpublish_at=now - timedelta(days=1),
        )
        url = reverse("product-list", kwargs={"version": "v1"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_admin_list_includes_scheduled_products(self):
        now = timezone.now()
        Product.objects.create(
            product_name="Future Admin Product",
            category=self.category,
            description="Scheduled",
            price="9.99",
            inventory=5,
            publish_at=now + timedelta(days=1),
        )
        Product.objects.create(
            product_name="Expired Admin Product",
            category=self.category,
            description="Scheduled",
            price="14.99",
            inventory=5,
            unpublish_at=now - timedelta(days=1),
        )
        self.client.force_authenticate(self.admin)
        url = reverse("product-list", kwargs={"version": "v1"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)

    def test_non_admin_cannot_create_product(self):
        self.client.force_authenticate(self.user)
        url = reverse("product-list", kwargs={"version": "v1"})
        payload = {
            "product_name": "Sample Cleanser",
            "price": "9.99",
            "currency": "usd",
            "inventory": 10,
            "category_id": self.category.id,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_product(self):
        self.client.force_authenticate(self.admin)
        url = reverse("product-list", kwargs={"version": "v1"})
        payload = {
            "product_name": "Sample Cleanser",
            "price": "9.99",
            "currency": "usd",
            "inventory": 10,
            "category_id": self.category.id,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Product.objects.filter(product_name="Sample Cleanser").exists()
        )

    def test_admin_cannot_set_invalid_publish_window(self):
        self.client.force_authenticate(self.admin)
        url = reverse("product-list", kwargs={"version": "v1"})
        now = timezone.now()
        payload = {
            "product_name": "Invalid Schedule",
            "price": "12.99",
            "currency": "usd",
            "inventory": 10,
            "category_id": self.category.id,
            "publish_at": (now + timedelta(days=2)).isoformat(),
            "unpublish_at": (now + timedelta(days=1)).isoformat(),
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        error_fields = {error.get("field") for error in response.data.get("errors", [])}
        self.assertIn("unpublish_at", error_fields)
