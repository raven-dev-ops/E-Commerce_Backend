from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models

from products.models import Product


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Cart for {self.user.username}"

    @property
    def total_price(self) -> Decimal:
        total = Decimal("0.00")
        for item in self.items.all():
            total += item.line_total
        return total

    def touch(self) -> None:
        self.save(update_fields=["updated_at"])


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"], name="uniq_cart_product"
            )
        ]
        ordering = ["-added_at"]

    def __str__(self) -> str:
        return f"{self.product.product_name} (x{self.quantity})"

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity


__all__ = ["Cart", "CartItem"]
