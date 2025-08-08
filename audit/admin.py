from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("user", "method", "path", "timestamp")
    search_fields = ("user__username", "path", "method")
