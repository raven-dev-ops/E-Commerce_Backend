from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


def _build_unique_slug(
    instance: models.Model,
    base: str,
    queryset: models.QuerySet,
    max_length: int,
) -> str:
    slug_base = slugify(base) or "item"
    slug = slug_base[:max_length]
    if not queryset.filter(slug=slug).exclude(pk=instance.pk).exists():
        return slug
    counter = 1
    while True:
        suffix = f"-{counter}"
        truncated = slug_base[: max_length - len(suffix)]
        candidate = f"{truncated}{suffix}"
        if not queryset.filter(slug=candidate).exclude(pk=instance.pk).exists():
            return candidate
        counter += 1


class ProductQuerySet(models.QuerySet):
    def published(self, now=None) -> models.QuerySet:
        now = now or timezone.now()
        return self.filter(is_active=True).filter(
            models.Q(publish_at__isnull=True) | models.Q(publish_at__lte=now),
            models.Q(unpublish_at__isnull=True) | models.Q(unpublish_at__gt=now),
        )


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = _build_unique_slug(self, self.name, Category.objects, 140)
        super().save(*args, **kwargs)


class Product(models.Model):
    product_name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="usd")
    inventory = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    publish_at = models.DateTimeField(null=True, blank=True, db_index=True)
    unpublish_at = models.DateTimeField(null=True, blank=True, db_index=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )
    tags = models.JSONField(default=list, blank=True)
    images = models.JSONField(default=list, blank=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField(default=0)
    erp_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product_name"], name="idx_product_name"),
            models.Index(fields=["price"], name="idx_product_price"),
        ]

    def __str__(self) -> str:
        return self.product_name

    def is_published(self, now=None) -> bool:
        now = now or timezone.now()
        if not self.is_active:
            return False
        if self.publish_at and self.publish_at > now:
            return False
        if self.unpublish_at and self.unpublish_at <= now:
            return False
        return True

    def clean(self) -> None:
        if self.publish_at and self.unpublish_at and self.unpublish_at <= self.publish_at:
            raise ValidationError(
                {"unpublish_at": "Unpublish time must be after publish time."}
            )

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = _build_unique_slug(self, self.product_name, Product.objects, 255)
        super().save(*args, **kwargs)


__all__ = ["Category", "Product"]
