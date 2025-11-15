from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from payments.models import Payment, Transaction


class PaymentsModelTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="john", password="pass"  # nosec B106
        )

        self.payment = Payment.objects.create(
            user=self.user,
            invoice="INV1001",
            amount=Decimal("150.00"),
            method="CC",
        )

        self.transaction = Transaction.objects.create(
            payment=self.payment,
            status="Completed",
        )

    def test_payment_str(self):
        self.assertEqual(
            str(self.payment), f"Payment {self.payment.id} - john - 150.00"
        )

    def test_transaction_str(self):
        text = str(self.transaction)
        self.assertIn("Transaction", text)
        self.assertIn("Completed", text)

