from django.utils.deprecation import MiddlewareMixin

class PermissionsPolicyMiddleware(MiddlewareMixin):
    """Add basic Permissions-Policy headers."""

    def process_response(self, request, response):
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=()",
        )
        return response
