from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from orders.models import Order
from payments.models import StripeWebhookEvent


@override_settings(
    SECURE_SSL_REDIRECT=False,
    STRIPE_SECRET_KEY="sk_test_dummy",
    STRIPE_WEBHOOK_SECRET="whsec_test",
)
class StripeWebhookTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="buyer", password="pass"  # nosec B106
        )
        self.order = Order.objects.create(
            user=self.user,
            total_price=Decimal("20.00"),
            payment_intent_id="pi_123",
            currency="usd",
        )
        self.client = APIClient()
        self.url = reverse("stripe-webhook", kwargs={"version": "v1"})

    def test_missing_signature_returns_400(self):
        response = self.client.post(
            self.url, data=b"{}", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    @patch("payments.views.stripe.Webhook.construct_event")
    def test_payment_intent_succeeded_updates_order(self, mock_construct):
        mock_construct.return_value = {
            "id": "evt_123",
            "type": "payment_intent.succeeded",
            "livemode": False,
            "data": {
                "object": {
                    "id": "pi_123",
                    "amount": 2000,
                    "currency": "usd",
                }
            },
        }

        response = self.client.post(
            self.url,
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=abc",
        )

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PROCESSING)
        self.assertTrue(
            StripeWebhookEvent.objects.filter(event_id="evt_123").exists()
        )

        response = self.client.post(
            self.url,
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=abc",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            StripeWebhookEvent.objects.filter(event_id="evt_123").count(), 1
        )

    @patch("payments.views.stripe.Webhook.construct_event")
    def test_payment_intent_failed_marks_order_failed(self, mock_construct):
        self.order.status = Order.Status.PROCESSING
        self.order.save(update_fields=["status"])

        mock_construct.return_value = {
            "id": "evt_456",
            "type": "payment_intent.payment_failed",
            "livemode": False,
            "data": {
                "object": {
                    "id": "pi_123",
                    "amount": 2000,
                    "currency": "usd",
                }
            },
        }

        response = self.client.post(
            self.url,
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=abc",
        )

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.FAILED)

    @patch("payments.views.stripe.Webhook.construct_event")
    def test_amount_mismatch_does_not_update_status(self, mock_construct):
        mock_construct.return_value = {
            "id": "evt_789",
            "type": "payment_intent.succeeded",
            "livemode": False,
            "data": {
                "object": {
                    "id": "pi_123",
                    "amount": 2500,
                    "currency": "usd",
                }
            },
        }

        response = self.client.post(
            self.url,
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=abc",
        )

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)


@override_settings(
    SECURE_SSL_REDIRECT=False,
    STRIPE_SECRET_KEY="",
    STRIPE_WEBHOOK_SECRET="",
)
class StripeWebhookConfigTests(TestCase):
    def test_missing_configuration_returns_503(self):
        client = APIClient()
        url = reverse("stripe-webhook", kwargs={"version": "v1"})
        response = client.post(
            url, data=b"{}", content_type="application/json"
        )
        self.assertEqual(response.status_code, 503)
