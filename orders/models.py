# orders/models.py

from django.db import models
from django.conf import settings
from django.db.models import Q
from authentication.models import Address  # Adjust import if Address is elsewhere


class ActiveOrderManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending Payment"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELED = "canceled", "Canceled"
        FAILED = "failed", "Payment Failed"

    STATUS_CHOICES = Status.choices

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    payment_intent_id = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    idempotency_key = models.CharField(
        max_length=64, blank=True, null=True, unique=True
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=Status.PENDING, db_index=True
    )
    currency = models.CharField(max_length=3, default="usd")
    shipping_address = models.ForeignKey(
        Address,
        related_name="shipping_orders",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    billing_address = models.ForeignKey(
        Address,
        related_name="billing_orders",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    discount_code = models.CharField(max_length=50, blank=True, null=True)
    shipped_date = models.DateTimeField(null=True, blank=True)
    discount_type = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[("percentage", "Percentage"), ("fixed", "Fixed")],
    )
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    is_gift = models.BooleanField(default=False)
    gift_message = models.CharField(max_length=500, blank=True)
    is_deleted = models.BooleanField(default=False)

    objects = ActiveOrderManager()
    all_objects = models.Manager()

    class Meta:
        indexes = [
            models.Index(
                fields=["user", "-created_at"],
                name="idx_order_user_created_at",
                condition=Q(is_deleted=False),
            )
        ]

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.save(update_fields=["is_deleted"])

    def restore(self):
        self.is_deleted = False
        self.save(update_fields=["is_deleted"])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
        null=True,
        blank=True,
    )
    product_name = models.CharField(
        max_length=255
    )  # Or ForeignKey to a Product model if using Django ORM
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} (x{self.quantity})"


class ShipmentWebhookEvent(models.Model):
    event_id = models.CharField(max_length=255, unique=True, db_index=True)
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="shipment_webhook_events"
    )
    status = models.CharField(max_length=20)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ShipmentWebhookEvent {self.event_id} for order {self.order_id}"
