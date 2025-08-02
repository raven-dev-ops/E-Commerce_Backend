# products/utils.py

from django.conf import settings
import logging
from .tasks import send_low_stock_email

logger = logging.getLogger(__name__)

def send_low_stock_notification(product_name, product_id, current_stock):
    """
    Sends an email notification to administrators about low stock levels.
    """
    subject = f'Low Stock Alert: {product_name}'
    # Enhance the email message to include more details
    message = (
        f'The following product is running low on stock and requires your attention:\n\n'
        f'Product Name: {product_name}\n'
        f'Current Stock: {current_stock}\n\n'
        f'Please restock this product as soon as possible.'
    )
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [settings.ADMIN_EMAIL] # Make sure ADMIN_EMAIL is set in your settings.py

    try:
        send_low_stock_email.delay(product_name, product_id, current_stock)
        logger.info("Low stock notification task queued for product: %s", product_name)
    except Exception as e:
        logger.error(
            "Error queueing low stock notification for product %s: %s",
            product_name,
            e,
        )
