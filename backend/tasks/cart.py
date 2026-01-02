from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from cart.models import Cart


@shared_task
def purge_inactive_carts() -> None:
    """Delete carts and items inactive for a configurable number of days."""
    cutoff = timezone.now() - timedelta(
        days=getattr(settings, "CART_INACTIVITY_DAYS", 30)
    )
    inactive_carts = Cart.objects.filter(updated_at__lt=cutoff)
    inactive_carts.delete()

