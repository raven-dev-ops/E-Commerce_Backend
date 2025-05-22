# orders/admin.py

from django_mongoengine import mongo_admin
from .models import Order

class OrderAdmin(mongo_admin.DocumentAdmin):
    # Optional: list display fields
    list_display = ('user', 'created_at', 'status', 'total_price')
    # Optional: search fields
    search_fields = ('user', 'status', 'payment_intent_id')
    # Optional: filters for the status field
    list_filter = ('status',)

mongo_admin.site.register(Order, OrderAdmin)
