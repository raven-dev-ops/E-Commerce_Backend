# payments/models.py

from django.db import models
from django.utils import timezone


class Invoice(models.Model):
    invoice_number = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    issued_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.customer_name}"


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('CC', 'Credit Card'),
        ('PP', 'PayPal'),
        ('BT', 'Bank Transfer'),
        ('CA', 'Cash'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateTimeField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=2, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Payment of {self.amount} for Invoice {self.invoice.invoice_number}"


class Transaction(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='transaction')
    status = models.CharField(max_length=50)  # e.g., 'Pending', 'Completed', 'Failed'
    processed_at = models.DateTimeField(default=timezone.now)
    response_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Transaction for Payment ID {self.payment.id} - Status: {self.status}"
