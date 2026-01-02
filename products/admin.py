from django.contrib import admin

from products.models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "updated_at")
    search_fields = ("name", "slug")
    list_filter = ("is_active",)
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "product_name",
        "slug",
        "price",
        "inventory",
        "is_active",
        "publish_at",
        "unpublish_at",
    )
    search_fields = ("product_name", "slug", "erp_id")
    list_filter = ("is_active", "category", "publish_at", "unpublish_at")
    ordering = ("-created_at",)
