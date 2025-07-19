import logging
from rest_framework import generics, permissions, status
from rest_framework.serializers import ModelSerializer, CharField
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

logger = logging.getLogger(__name__)
User = get_user_model()


class UserSerializer(ModelSerializer):
    password = CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class CustomGoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client

    def get_callback_url(self):
        return "https://twiinz-beard-frontend.netlify.app"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['callback_url'] = self.get_callback_url()
        return context

    def post(self, request, *args, **kwargs):
        logger.info("🔐 Received POST request for Google login")
        logger.info("Request data: %s", request.data)
        return super().post(request, *args, **kwargs)
