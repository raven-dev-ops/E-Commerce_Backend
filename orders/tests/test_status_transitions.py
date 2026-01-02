from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TestCase

from orders.models import Order
from orders.services import transition_order_status


class OrderStatusTransitionTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="statususer",
            password="pass",  # nosec B106
            phone_number="+15555555555",
        )
        self.order = Order.objects.create(
            user=self.user,
            total_price=10,
            shipping_cost=0,
            tax_amount=0,
            status=Order.Status.PENDING,
        )

    @patch("orders.services.async_to_sync", side_effect=lambda func: func)
    @patch("orders.services.get_channel_layer")
    @patch("orders.services.send_order_status_sms")
    def test_transition_schedules_notifications_on_commit(
        self, mock_sms, mock_get_layer, _mock_async
    ):
        layer = Mock()
        mock_get_layer.return_value = layer

        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            with transaction.atomic():
                transition_order_status(self.order, Order.Status.PROCESSING)
                mock_sms.delay.assert_not_called()
                layer.group_send.assert_not_called()

        self.assertEqual(len(callbacks), 1)
        callbacks[0]()

        mock_sms.delay.assert_called_once_with(
            self.order.id,
            Order.Status.PROCESSING,
            self.user.phone_number,
        )
        layer.group_send.assert_called_once_with(
            f"order_{self.order.id}",
            {"type": "status.update", "status": Order.Status.PROCESSING},
        )

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PROCESSING)

    @patch("orders.services.async_to_sync", side_effect=lambda func: func)
    @patch("orders.services.get_channel_layer")
    @patch("orders.services.send_order_status_sms")
    def test_transition_same_status_no_callbacks(
        self, mock_sms, mock_get_layer, _mock_async
    ):
        layer = Mock()
        mock_get_layer.return_value = layer

        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            with transaction.atomic():
                transition_order_status(self.order, Order.Status.PENDING)

        self.assertEqual(len(callbacks), 0)
        mock_sms.delay.assert_not_called()
        mock_get_layer.assert_not_called()
        layer.group_send.assert_not_called()

    @patch("orders.services.release_reserved_inventory")
    @patch("orders.services.async_to_sync", side_effect=lambda func: func)
    @patch("orders.services.get_channel_layer")
    @patch("orders.services.send_order_status_sms")
    def test_transition_to_canceled_releases_inventory_after_commit(
        self, mock_sms, mock_get_layer, _mock_async, mock_release
    ):
        layer = Mock()
        mock_get_layer.return_value = layer

        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            with transaction.atomic():
                transition_order_status(self.order, Order.Status.CANCELED)
                mock_release.assert_not_called()

        self.assertEqual(len(callbacks), 1)
        callbacks[0]()

        mock_release.assert_called_once_with(self.order)
