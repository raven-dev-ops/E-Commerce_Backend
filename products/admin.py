# products/admin.py

from django_mongoengine import mongo_admin as admin

from .models import Product, Category


class ProductAdmin(admin.DocumentAdmin):
    pass


class CategoryAdmin(admin.DocumentAdmin):
    pass


admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
