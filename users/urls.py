# users/urls.py

from django.urls import path, include
from .views import RegisterUserView, UserProfileView, CustomGoogleLogin

urlpatterns = [
    # Local user endpoints
    path('register/', RegisterUserView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),

    # dj-rest-auth default endpoints (login, logout, password reset)
    path('auth/', include('dj_rest_auth.urls')),

    # Registration endpoints (email verification, signup, etc.)
    path('auth/', include('dj_rest_auth.registration.urls')),

    # ✅ Google social login endpoint
    path('auth/google/', CustomGoogleLogin.as_view(), name='google_login'),
]
