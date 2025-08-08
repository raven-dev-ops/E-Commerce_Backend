from __future__ import annotations

from django.http import HttpRequest, HttpResponse

from .models import AuditLog


class AuditLogMiddleware:
    """Persist audit logs for staff actions that modify data."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if (
            request.user.is_authenticated
            and request.user.is_staff
            and request.method in {"POST", "PUT", "PATCH", "DELETE"}
        ):
            AuditLog.objects.create(
                user=request.user,
                path=request.path,
                method=request.method,
            )
        return response
