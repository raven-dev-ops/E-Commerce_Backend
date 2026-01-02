from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from products.models import Category


@override_settings(SECURE_SSL_REDIRECT=False, ALLOWED_HOSTS=["testserver"])
class CategoryApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="admin", password="pass", is_staff=True
        )  # nosec B106
        self.user = User.objects.create_user(
            username="buyer", password="pass"
        )  # nosec B106
        self.client = APIClient()
        self.list_url = reverse("category-list-create", kwargs={"version": "v1"})

    def test_list_categories(self):
        Category.objects.create(name="Skincare", description="Skincare products")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_non_admin_cannot_create_category(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            self.list_url, {"name": "Supplements", "description": "Supplements"}
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_category(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            self.list_url, {"name": "Supplements", "description": "Supplements"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Category.objects.filter(name="Supplements").exists())
