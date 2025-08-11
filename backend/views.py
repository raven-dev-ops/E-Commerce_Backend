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
