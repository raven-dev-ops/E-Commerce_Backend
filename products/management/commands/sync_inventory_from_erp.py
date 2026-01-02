"""Management command to sync product inventory from the ERP system."""

from django.core.management.base import BaseCommand
from products.models import Product
from products.services import sync_product_inventory
from erp.client import ERPClientError


class Command(BaseCommand):
    help = "Sync product inventory from the external ERP system."

    def handle(self, *args, **options):
        for product in Product.objects.all():
            try:
                inventory = sync_product_inventory(product)
                external_id = product.erp_id or str(product.id)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Synced inventory for product {external_id}: {inventory}"
                    )
                )
            except ERPClientError as exc:
                external_id = product.erp_id or str(product.id)
                self.stderr.write(
                    self.style.ERROR(f"Failed to sync product {external_id}: {exc}")
                )
