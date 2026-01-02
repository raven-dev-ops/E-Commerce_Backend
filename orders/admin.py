# orders/admin.py

from django.contrib import admin
from .models import Order, OrderItem, ShipmentWebhookEvent


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "status", "total_price")
    search_fields = ("user__username", "user__email", "status", "discount_code")
    list_filter = ("status", "created_at")
    ordering = ("-created_at",)
    inlines = [OrderItemInline]


@admin.register(ShipmentWebhookEvent)
class ShipmentWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "order", "status", "received_at")
    list_filter = ("status", "received_at")
    search_fields = ("event_id", "order__id")
    ordering = ("-received_at",)
