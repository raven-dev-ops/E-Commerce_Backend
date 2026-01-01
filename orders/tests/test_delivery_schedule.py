from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from orders.models import Order


@override_settings(SECURE_SSL_REDIRECT=False)
class PreferredDeliveryDateTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="deliveryuser",
            password="pass",  # nosec B106
        )
        self.client = APIClient()
        self.order = Order.objects.create(
            user=self.user,
            total_price=10,
            shipping_cost=0,
            tax_amount=0,
            status=Order.Status.PENDING,
        )

    def test_schedule_preferred_delivery_date(self):
        self.client.force_authenticate(user=self.user)
        url = reverse(
            "order-schedule-delivery",
            kwargs={"version": "v1", "pk": self.order.id},
        )
        preferred = (timezone.localdate() + timedelta(days=2)).isoformat()

        response = self.client.post(
            url, {"preferred_delivery_date": preferred}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.preferred_delivery_date.isoformat(), preferred)
        self.assertEqual(response.json()["preferred_delivery_date"], preferred)

    def test_schedule_rejects_past_date(self):
        self.client.force_authenticate(user=self.user)
        url = reverse(
            "order-schedule-delivery",
            kwargs={"version": "v1", "pk": self.order.id},
        )
        preferred = (timezone.localdate() - timedelta(days=1)).isoformat()

        response = self.client.post(
            url, {"preferred_delivery_date": preferred}, format="json"
        )

        self.assertEqual(response.status_code, 400)

    def test_schedule_requires_pending_or_processing(self):
        self.client.force_authenticate(user=self.user)
        self.order.status = Order.Status.SHIPPED
        self.order.save(update_fields=["status"])
        url = reverse(
            "order-schedule-delivery",
            kwargs={"version": "v1", "pk": self.order.id},
        )
        preferred = (timezone.localdate() + timedelta(days=2)).isoformat()

        response = self.client.post(
            url, {"preferred_delivery_date": preferred}, format="json"
        )

        self.assertEqual(response.status_code, 400)
