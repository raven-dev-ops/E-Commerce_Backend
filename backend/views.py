from django.core.cache import cache
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
