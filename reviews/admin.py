from django.contrib import admin

from reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "user", "rating", "status", "created_at")
    list_filter = ("status", "rating", "created_at")
    search_fields = ("product__product_name", "user__username", "user__email")
    ordering = ("-created_at",)
