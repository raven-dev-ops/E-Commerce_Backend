# reviews/models.py

from mongoengine import Document, StringField, IntField, DateTimeField, ReferenceField
from datetime import datetime
from products.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()

class Review(Document):
    user_id = IntField(required=True)
    product = ReferenceField(Product, required=True)
    rating = IntField(min_value=1, max_value=5, required=True)
    comment = StringField(required=False)  # allow empty comment
    status = StringField(choices=['pending', 'approved', 'rejected'], default='pending')
    created_at = DateTimeField(default=datetime.utcnow)
    
    @property
    def user(self):
        try:
            return User.objects.get(pk=self.user_id)
        except User.DoesNotExist:
            return None

    meta = {
        'indexes': [
            'user_id',
            'product',
            'status',
        ]
    }
