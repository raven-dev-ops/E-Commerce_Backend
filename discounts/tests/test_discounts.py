from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from discounts.models import Discount
from products.models import Category, Product


@override_settings(SECURE_SSL_REDIRECT=False)
class DiscountApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_superuser(
            username="admin", password="pass"  # nosec B106
        )
        self.user = user_model.objects.create_user(
            username="buyer", password="pass"  # nosec B106
        )
        self.category = Category.objects.create(name="Skincare")
        self.product = Product.objects.create(
            product_name="Sample Lotion",
            category=self.category,
            price="19.99",
            inventory=10,
        )
        self.client = APIClient()
        self.list_url = reverse("discount-list", kwargs={"version": "v1"})
        self.validate_url = reverse("discount-validate", kwargs={"version": "v1"})

    def test_admin_can_create_discount(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            self.list_url,
            {
                "code": "SAVE10",
                "name": "Save 10%",
                "discount_type": "percentage",
                "value": "10.00",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Discount.objects.filter(code="SAVE10").exists())

    def test_non_admin_cannot_create_discount(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.list_url,
            {
                "code": "SAVE10",
                "name": "Save 10%",
                "discount_type": "percentage",
                "value": "10.00",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_validate_discount_checks_min_order(self):
        Discount.objects.create(
            code="SAVE10",
            name="Save 10%",
            discount_type="percentage",
            value="10.00",
            min_order_amount="25.00",
            is_active=True,
        )
        response = self.client.post(
            self.validate_url,
            {"code": "SAVE10", "order_total": "20.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
