from django.test import TestCase
from .models import Invoice, Payment, Transaction
from django.utils import timezone
from decimal import Decimal

class PaymentsModelTests(TestCase):

    def setUp(self):
        self.invoice = Invoice.objects.create(
            invoice_number="INV1001",
            customer_name="John Doe",
            customer_email="john@example.com",
            amount_due=Decimal("150.00"),
            due_date=timezone.now().date()
        )

        self.payment = Payment.objects.create(
            invoice=self.invoice,
            amount=Decimal("150.00"),
            method='CC',
            transaction_id="TX123456"
        )

        self.transaction = Transaction.objects.create(
            payment=self.payment,
            status="Completed",
            response_message="Success"
        )

    def test_invoice_str(self):
        self.assertEqual(str(self.invoice), "Invoice INV1001 - John Doe")

    def test_payment_str(self):
        self.assertEqual(str(self.payment), "Payment of 150.00 for Invoice INV1001")

    def test_transaction_str(self):
        self.assertIn("Transaction for Payment ID", str(self.transaction))
        self.assertIn("Status: Completed", str(self.transaction))
