from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True, allow_null=True)
    user_email = serializers.EmailField(
        source="user.email", read_only=True, allow_null=True
    )
    username = serializers.CharField(
        source="user.username", read_only=True, allow_null=True
    )

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user_id",
            "user_email",
            "username",
            "path",
            "method",
            "timestamp",
        ]
