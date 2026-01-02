from django.contrib import admin

from discounts.models import Discount, DiscountRedemption


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "discount_type",
        "value",
        "is_active",
        "times_used",
        "starts_at",
        "ends_at",
    )
    list_filter = ("discount_type", "is_active", "starts_at", "ends_at")
    search_fields = ("code", "name")
    ordering = ("-created_at",)
    filter_horizontal = ("categories", "products")


@admin.register(DiscountRedemption)
class DiscountRedemptionAdmin(admin.ModelAdmin):
    list_display = ("discount", "order", "user", "redeemed_at")
    list_filter = ("redeemed_at",)
    search_fields = ("discount__code", "order__id", "user__username")
    ordering = ("-redeemed_at",)
