from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import (
    AddressViewSet,
    UserRegistrationView,
    LoginView,
    GoogleLogin,
    VerifyEmailView,
)

router = DefaultRouter()
router.register(r"addresses", AddressViewSet, basename="address")

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token-verify"),
    path("auth/google/login/", GoogleLogin.as_view(), name="google_login"),
    path("verify-email/<uuid:token>/", VerifyEmailView.as_view(), name="verify-email"),
    path("", include(router.urls)),
]
