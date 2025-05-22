from django.contrib import admin
from django.urls import path, include
from django_mongoengine.mongo_admin import site as mongo_admin_site
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.views import obtain_auth_token

from products.views import ProductViewSet
from orders.views import CartViewSet, OrderViewSet
from authentication.views import (
    AddressViewSet,
    UserRegistrationView,
    UserProfileView
)
from . import views  # Stripe webhook view

# Router
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'addresses', AddressViewSet, basename='address')

# Root API View
class ApiRootView(APIView):
    def get(self, request, format=None):
        return Response({
            'products': 'api/products/',
            'cart': 'api/cart/',
            'orders': 'api/orders/',
            'addresses': 'api/addresses/',
        })

# URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('mongo-admin/', mongo_admin_site.urls),
    path('', ApiRootView.as_view(), name='api-root'),
    path('api/', include(router.urls)),
    path('auth/', include('authentication.urls')),
    path('api/register/', UserRegistrationView.as_view(), name='user-registration'),
    path('api/login/', obtain_auth_token, name='api_token_auth'),
    path('api/profile/', UserProfileView.as_view(), name='user-profile'),
    path('webhook/', views.stripe_webhook_view, name='stripe_webhook'),
]
