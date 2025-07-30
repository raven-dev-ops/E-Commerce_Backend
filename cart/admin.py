# cart/admin.py

from django_mongoengine import mongo_admin as admin

from .models import Cart, CartItem


class CartAdmin(admin.DocumentAdmin):
    pass


class CartItemAdmin(admin.DocumentAdmin):
    pass


admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
