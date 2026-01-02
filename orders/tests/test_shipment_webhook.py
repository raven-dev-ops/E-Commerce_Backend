import hashlib
import hmac
import json
import time

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from orders.models import Order, ShipmentWebhookEvent


def _sign_payload(secret, timestamp, payload_bytes):
    signed_payload = f"{timestamp}.".encode("utf-8") + payload_bytes
    return hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()


@override_settings(
    SECURE_SSL_REDIRECT=False,
    SHIPMENT_WEBHOOK_SECRET="ship_secret",
    SHIPMENT_WEBHOOK_TOLERANCE=300,
)
class ShipmentWebhookTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="buyer", password="pass"  # nosec B106
        )
        self.order = Order.objects.create(
            user=self.user,
            total_price="10.00",
        )
        self.client = APIClient()
        self.url = reverse("shipment-webhook", kwargs={"version": "v1"})

    def test_valid_signature_updates_order(self):
        payload = {
            "event_id": "evt_ship_1",
            "order_id": self.order.id,
            "status": "shipped",
            "shipped_date": "2025-01-01T12:00:00Z",
        }
        payload_json = json.dumps(payload)
        timestamp = int(time.time())
        signature = _sign_payload(
            "ship_secret", timestamp, payload_json.encode("utf-8")
        )

        response = self.client.post(
            self.url,
            data=payload_json,
            content_type="application/json",
            HTTP_X_WEBHOOK_SIGNATURE=signature,
            HTTP_X_WEBHOOK_TIMESTAMP=str(timestamp),
        )

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.SHIPPED)
        self.assertIsNotNone(self.order.shipped_date)
        self.assertTrue(
            ShipmentWebhookEvent.objects.filter(event_id="evt_ship_1").exists()
        )

    def test_invalid_signature_rejected(self):
        payload = {
            "event_id": "evt_ship_2",
            "order_id": self.order.id,
            "status": "shipped",
        }
        payload_json = json.dumps(payload)
        timestamp = int(time.time())
        signature = _sign_payload(
            "wrong_secret", timestamp, payload_json.encode("utf-8")
        )

        response = self.client.post(
            self.url,
            data=payload_json,
            content_type="application/json",
            HTTP_X_WEBHOOK_SIGNATURE=signature,
            HTTP_X_WEBHOOK_TIMESTAMP=str(timestamp),
        )

        self.assertEqual(response.status_code, 401)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertFalse(
            ShipmentWebhookEvent.objects.filter(event_id="evt_ship_2").exists()
        )

    def test_replay_rejected(self):
        payload = {
            "event_id": "evt_ship_3",
            "order_id": self.order.id,
            "status": "shipped",
        }
        payload_json = json.dumps(payload)
        timestamp = int(time.time()) - 1000
        signature = _sign_payload(
            "ship_secret", timestamp, payload_json.encode("utf-8")
        )

        response = self.client.post(
            self.url,
            data=payload_json,
            content_type="application/json",
            HTTP_X_WEBHOOK_SIGNATURE=signature,
            HTTP_X_WEBHOOK_TIMESTAMP=str(timestamp),
        )

        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertFalse(
            ShipmentWebhookEvent.objects.filter(event_id="evt_ship_3").exists()
        )

    def test_duplicate_event_id_ignored(self):
        payload = {
            "event_id": "evt_ship_4",
            "order_id": self.order.id,
            "status": "shipped",
        }
        payload_json = json.dumps(payload)
        timestamp = int(time.time())
        signature = _sign_payload(
            "ship_secret", timestamp, payload_json.encode("utf-8")
        )

        response = self.client.post(
            self.url,
            data=payload_json,
            content_type="application/json",
            HTTP_X_WEBHOOK_SIGNATURE=signature,
            HTTP_X_WEBHOOK_TIMESTAMP=str(timestamp),
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            self.url,
            data=payload_json,
            content_type="application/json",
            HTTP_X_WEBHOOK_SIGNATURE=signature,
            HTTP_X_WEBHOOK_TIMESTAMP=str(timestamp),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            ShipmentWebhookEvent.objects.filter(event_id="evt_ship_4").count(), 1
        )


@override_settings(
    SECURE_SSL_REDIRECT=False,
    SHIPMENT_WEBHOOK_SECRET="",
)
class ShipmentWebhookConfigTests(TestCase):
    def test_missing_configuration_returns_503(self):
        client = APIClient()
        url = reverse("shipment-webhook", kwargs={"version": "v1"})
        response = client.post(
            url,
            data=json.dumps({"event_id": "evt_ship_5"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 503)
