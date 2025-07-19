# backend/urls.py

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse, JsonResponse

def home(request):
    return HttpResponse("Welcome to the e-commerce backend API!")

def custom_404(request, exception=None):
    return JsonResponse({'error': 'Endpoint not found'}, status=404)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),

    # App-specific APIs
    path('users/', include('users.urls')),  # includes social login under /users/auth/google/login/
    path('products/', include('products.urls')),
    path('orders/', include('orders.urls')),
    path('cart/', include('cart.urls')),
    path('payments/', include('payments.urls')),
    path('discounts/', include('discounts.urls')),
    path('reviews/', include('reviews.urls')),
    path('authentication/', include('authentication.urls')),

    # Optional fallback — accessible only if not using users/ for auth
    path('auth/', include('dj_rest_auth.urls')),                  # login/logout/password reset
    path('auth/registration/', include('dj_rest_auth.registration.urls')),  # email registration
    path('auth/social/', include('allauth.socialaccount.urls')),  # optional browser flow: /auth/social/google/login/
]

# Catch-all 404 handler for API
handler404 = 'backend.urls.custom_404'
