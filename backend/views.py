from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response


class PurgeCacheView(APIView):
    """Clear all application caches."""

    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        cache.clear()
        return Response({"detail": "Cache purged."})


class RateLimitStatusView(APIView):
    """Expose current API rate limit usage and remaining requests."""

    def get(self, request, *args, **kwargs):
        data = {}
        for throttle in self.get_throttles():
            key = throttle.get_cache_key(request, self)
            if not key:
                continue
            history = throttle.cache.get(key, [])
            data[throttle.scope] = {
                "limit": throttle.num_requests,
                "remaining": max(0, throttle.num_requests - len(history)),
            }
        return Response(data)


def _get_client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def metrics_view(request):
    allowed_ips = getattr(settings, "METRICS_ALLOWED_IPS", [])
    token = getattr(settings, "METRICS_AUTH_TOKEN", "")
    if not allowed_ips and not token:
        return HttpResponse(status=404)

    if token:
        provided = request.headers.get("X-Metrics-Token", "")
        if provided != token:
            return HttpResponse(status=403)

    if allowed_ips:
        client_ip = _get_client_ip(request)
        if client_ip not in allowed_ips:
            return HttpResponse(status=403)

    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
