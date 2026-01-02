from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.authentication import JWTAuthentication

from backend.permissions import IsOwnerOrAdmin
from reviews.models import Review
from reviews.serializers import ReviewSerializer, ReviewWriteSerializer
from reviews.services import update_product_rating
from reviews.throttles import ReviewCreateThrottle


class ReviewViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]
    queryset = Review.objects.select_related("user", "product")

    def get_queryset(self):
        queryset = Review.objects.select_related("user", "product")
        if not self.request.user.is_staff:
            queryset = queryset.filter(status=Review.Status.APPROVED)
        product_id = self.request.query_params.get("product_id")
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return ReviewWriteSerializer
        return ReviewSerializer

    def get_throttles(self):
        throttles = super().get_throttles()
        if self.action == "create":
            throttles.append(ReviewCreateThrottle())
        return throttles

    def perform_create(self, serializer):
        review = serializer.save(user=self.request.user)
        update_product_rating(review.product_id)

    def perform_update(self, serializer):
        review = serializer.save()
        update_product_rating(review.product_id)

    def perform_destroy(self, instance):
        product_id = instance.product_id
        instance.delete()
        update_product_rating(product_id)
