from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Payment, Transaction
from decimal import Decimal

class PaymentsModelTests(TestCase):

    def setUp(self):
        self.payment = Payment.objects.create(
            user=get_user_model().objects.create_user(username="test", password="pass"),
            invoice="INV1001",
            amount=Decimal("150.00"),
            method='CC'
        )

        self.transaction = Transaction.objects.create(
            payment=self.payment,
            status="Completed"
        )

    def test_payment_str(self):
        self.assertIn("Payment", str(self.payment))

    def test_transaction_str(self):
        self.assertIn("Transaction", str(self.transaction))
        self.assertIn("Completed", str(self.transaction))
