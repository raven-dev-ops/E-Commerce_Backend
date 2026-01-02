from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Avg, Count

from products.models import Product
from reviews.models import Review


def update_product_rating(product_id: int) -> None:
    aggregates = Review.objects.filter(
        product_id=product_id, status=Review.Status.APPROVED
    ).aggregate(avg=Avg("rating"), count=Count("id"))
    average = aggregates["avg"] or Decimal("0")
    rating_count = aggregates["count"] or 0
    average = Decimal(str(average)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    Product.objects.filter(id=product_id).update(
        average_rating=average, rating_count=rating_count
    )
