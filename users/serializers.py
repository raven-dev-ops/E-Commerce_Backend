# users/serializers.py

from rest_framework_mongoengine.serializers import DocumentSerializer
from .models import User  # your MongoEngine User document

class UserSerializer(DocumentSerializer):
    class Meta:
        document = User
        fields = '__all__'
