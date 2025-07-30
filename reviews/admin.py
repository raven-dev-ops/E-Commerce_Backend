# reviews/admin.py

from django_mongoengine import mongo_admin as admin

from .models import Review


class ReviewAdmin(admin.DocumentAdmin):
    pass


admin.site.register(Review, ReviewAdmin)
