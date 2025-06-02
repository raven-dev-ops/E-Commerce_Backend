# users/urls.py

from django.urls import path, include
from .views import RegisterUserView, UserProfileView, google_login_redirect

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    # Social and rest-auth endpoints
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/', include('dj_rest_auth.registration.urls')),
    path('auth/', include('allauth.socialaccount.urls')),  # Enables /users/auth/social/login/google/
    path('auth/google/login/', google_login_redirect, name='google-login-redirect'),  # Optional shortcut
]
