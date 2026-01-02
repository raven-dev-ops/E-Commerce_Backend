"""Service layer for product-related operations."""

from __future__ import annotations

from typing import List

from orders.models import OrderItem
from products.models import Product
from erp.client import get_inventory


def get_recommended_products(user, limit: int = 5) -> List[Product]:
    """Return products recommended for ``user`` based on purchase history.

    Recommendations are derived from the categories of previously purchased
    products. Products the user has already purchased are excluded, and results
    are ordered by average rating in descending order.
    """

    purchased_names = list(
        OrderItem.objects.filter(order__user=user).values_list(
            "product_name", flat=True
        )
    )
    if not purchased_names:
        return []

    published_qs = Product.objects.published()
    purchased_products = published_qs.filter(product_name__in=purchased_names)
    categories = {p.category_id for p in purchased_products}
    if not categories:
        return []

    recommended_qs = (
        published_qs.filter(category_id__in=list(categories))
        .exclude(product_name__in=purchased_names)
        .order_by("-average_rating")
    )
    return list(recommended_qs[:limit])


def sync_product_inventory(product: Product) -> int:
    """Update ``product`` inventory from the ERP system.

    Returns the new inventory level.
    """
    external_id = product.erp_id or str(product.id)
    inventory = get_inventory(external_id)
    product.inventory = inventory
    product.save()
    return inventory
