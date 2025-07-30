# discounts/admin.py

from django_mongoengine import mongo_admin as admin

from .models import Discount


class DiscountAdmin(admin.DocumentAdmin):
    pass


admin.site.register(Discount, DiscountAdmin)
