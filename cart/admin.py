# cart/admin.py

from django_mongoengine.mongo_admin.sites import site as mongo_admin_site
from .models import Cart, CartItem

mongo_admin_site.register(Cart)
mongo_admin_site.register(CartItem)
