from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from audit.models import AuditLog


@override_settings(SECURE_SSL_REDIRECT=False)
class AuditLogApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            username="admin",
            password="pass",  # nosec B106
            is_staff=True,
        )
        self.user = user_model.objects.create_user(
            username="user",
            password="pass",  # nosec B106
        )
        AuditLog.objects.create(user=self.admin, path="/api/v1/orders/", method="GET")

    def test_admin_can_list_audit_logs(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("audit-log-list", kwargs={"version": "v1"})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload)
        self.assertEqual(payload[0]["path"], "/api/v1/orders/")

    def test_non_admin_forbidden(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("audit-log-list", kwargs={"version": "v1"})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
