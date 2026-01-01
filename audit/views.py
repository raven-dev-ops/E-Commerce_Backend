from django.utils.dateparse import parse_datetime
from rest_framework import permissions, viewsets

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        queryset = AuditLog.objects.select_related("user").order_by("-timestamp")
        params = self.request.query_params

        user_id = params.get("user_id")
        if user_id and user_id.isdigit():
            queryset = queryset.filter(user_id=user_id)

        method = params.get("method")
        if method:
            queryset = queryset.filter(method__iexact=method)

        path = params.get("path")
        if path:
            queryset = queryset.filter(path__icontains=path)

        since = params.get("since")
        if since:
            parsed = parse_datetime(since)
            if parsed:
                queryset = queryset.filter(timestamp__gte=parsed)

        until = params.get("until")
        if until:
            parsed = parse_datetime(until)
            if parsed:
                queryset = queryset.filter(timestamp__lte=parsed)

        return queryset
