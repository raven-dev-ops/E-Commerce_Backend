from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryListCreateAPIView,
    CategoryRetrieveUpdateDestroyAPIView,
    DiscountValidateAPIView,
    DiscountViewSet,
)

router = DefaultRouter()
router.register(r"discounts", DiscountViewSet, basename="discount")

urlpatterns = [
    path("discounts/validate/", DiscountValidateAPIView.as_view(), name="discount-validate"),
    path("", include(router.urls)),
    path(
        "categories/", CategoryListCreateAPIView.as_view(), name="category-list-create"
    ),
    path(
        "categories/<str:pk>/",
        CategoryRetrieveUpdateDestroyAPIView.as_view(),
        name="category-detail",
    ),
]
