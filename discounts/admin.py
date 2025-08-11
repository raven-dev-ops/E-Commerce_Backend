"""Admin configuration for the discounts app."""

from django_mongoengine import mongo_admin

from .models import Discount
from django_mongoengine.mongo_admin.sites import DocumentMetaWrapper


class DiscountAdmin(mongo_admin.DocumentAdmin):
    """Admin configuration for managing discount rules."""

    list_display = (
        "code",
        "discount_type",
        "value",
        "is_active",
        "valid_from",
        "valid_to",
    )
    search_fields = ("code",)
    list_filter = ("discount_type", "is_active")
    ordering = ("-valid_from",)


Discount._meta = DocumentMetaWrapper(Discount)
mongo_admin.site.register(Discount, DiscountAdmin)
