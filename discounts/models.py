from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from orders.models import Order
from products.models import Category, Product


class Discount(models.Model):
    class Type(models.TextChoices):
        PERCENTAGE = "percentage", "Percentage"
        FIXED = "fixed", "Fixed"

    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=Type.choices)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(blank=True, null=True)
    ends_at = models.DateTimeField(blank=True, null=True)
    max_uses = models.PositiveIntegerField(blank=True, null=True)
    max_uses_per_user = models.PositiveIntegerField(blank=True, null=True)
    min_order_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    times_used = models.PositiveIntegerField(default=0)
    categories = models.ManyToManyField(
        Category, blank=True, related_name="discounts"
    )
    products = models.ManyToManyField(
        Product, blank=True, related_name="discounts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.code

    def save(self, *args, **kwargs) -> None:
        if self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def is_available(self, now=None) -> bool:
        if not self.is_active:
            return False
        current = now or timezone.now()
        if self.starts_at and current < self.starts_at:
            return False
        if self.ends_at and current > self.ends_at:
            return False
        if self.max_uses is not None and self.times_used >= self.max_uses:
            return False
        return True


class DiscountRedemption(models.Model):
    discount = models.ForeignKey(
        Discount, on_delete=models.CASCADE, related_name="redemptions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="discount_redemption"
    )
    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-redeemed_at"]

    def __str__(self) -> str:
        return f"{self.discount.code} - {self.order_id}"


__all__ = ["Discount", "DiscountRedemption"]
