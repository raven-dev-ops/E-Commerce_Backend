"""Service layer for order-related operations."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
import logging
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import stripe
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.conf import settings
from django.db import connection, transaction
from django.db.models import F
from django.utils import timezone

from cart.models import Cart, CartItem
from discounts.models import Discount, DiscountRedemption
from orders.models import Order, OrderItem
from orders.tasks import send_order_status_sms
from products.models import Product


logger = logging.getLogger(__name__)


def _select_for_update(queryset):
    if connection.features.has_select_for_update:
        return queryset.select_for_update()
    return queryset


def _to_stripe_amount(total: Decimal) -> int:
    return int((total * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _quantize_amount(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _compute_cart_totals(
    items: list[CartItem],
    currency: str | None,
    shipping_cost: Decimal,
    tax_amount: Decimal,
) -> tuple[Decimal, Decimal, str]:
    subtotal = Decimal("0.00")
    resolved_currency = currency.lower() if currency else None

    for item in items:
        product = item.product
        if not product or not product.is_published():
            raise ValueError("One or more products are unavailable.")
        product_currency = product.currency.lower()
        if resolved_currency and product_currency != resolved_currency:
            raise ValueError("Cart contains multiple currencies.")
        resolved_currency = resolved_currency or product_currency
        subtotal += product.price * item.quantity

    total = subtotal + shipping_cost + tax_amount
    if total <= 0:
        raise ValueError("Order total must be greater than zero.")

    return subtotal, total, resolved_currency or "usd"


def _eligible_discount_subtotal(items: list[CartItem], discount: Discount) -> Decimal:
    product_ids = set(discount.products.values_list("id", flat=True))
    category_ids = set(discount.categories.values_list("id", flat=True))
    apply_to_all = not product_ids and not category_ids

    subtotal = Decimal("0.00")
    for item in items:
        product = item.product
        if not product:
            continue
        if apply_to_all:
            eligible = True
        else:
            eligible = product.id in product_ids
            if not eligible and category_ids:
                eligible = product.category_id in category_ids
        if eligible:
            subtotal += item.unit_price * item.quantity
    return subtotal


def _calculate_discount_amount(
    discount: Discount, eligible_subtotal: Decimal
) -> Decimal:
    if eligible_subtotal <= 0:
        return Decimal("0.00")
    if discount.discount_type == Discount.Type.PERCENTAGE:
        percent = discount.value / Decimal("100")
        return _quantize_amount(eligible_subtotal * percent)
    if discount.discount_type == Discount.Type.FIXED:
        return _quantize_amount(min(discount.value, eligible_subtotal))
    return Decimal("0.00")


def _resolve_discount(
    discount_code: str,
    user,
    items: list[CartItem],
    subtotal: Decimal,
    lock: bool = False,
) -> tuple[Discount, Decimal]:
    code = discount_code.strip().upper()
    qs = Discount.objects
    if lock:
        qs = qs.select_for_update()
    discount = qs.filter(code=code).first()
    if not discount or not discount.is_available(timezone.now()):
        raise ValueError("Invalid or inactive discount code.")
    if subtotal < discount.min_order_amount:
        raise ValueError("Order total does not meet minimum amount for discount.")
    if discount.max_uses_per_user is not None:
        redemptions = DiscountRedemption.objects.filter(
            discount=discount, user=user
        ).count()
        if redemptions >= discount.max_uses_per_user:
            raise ValueError("Discount usage limit reached.")
    eligible_subtotal = _eligible_discount_subtotal(items, discount)
    if eligible_subtotal <= 0:
        raise ValueError("Discount not applicable to cart items.")
    discount_amount = _calculate_discount_amount(discount, eligible_subtotal)
    if discount_amount <= 0:
        raise ValueError("Discount amount must be greater than zero.")
    return discount, discount_amount


def _create_payment_intent(
    amount: int, currency: str, user_id: int, idempotency_key: str | None
):
    stripe_secret = getattr(settings, "STRIPE_SECRET_KEY", None)
    if not stripe_secret or stripe_secret == "dummy":
        raise ValueError("Stripe configuration is missing.")

    stripe.api_key = stripe_secret
    metadata = {"user_id": str(user_id)}
    if idempotency_key:
        metadata["idempotency_key"] = idempotency_key

    params: dict[str, Any] = {
        "amount": amount,
        "currency": currency,
        "automatic_payment_methods": {"enabled": True},
        "metadata": metadata,
    }
    if idempotency_key:
        params["idempotency_key"] = idempotency_key

    try:
        return stripe.PaymentIntent.create(**params)
    except stripe.error.StripeError as exc:
        logger.error("Stripe PaymentIntent creation failed: %s", exc)
        raise ValueError("Payment processing is unavailable.") from exc


def _update_payment_intent_metadata(payment_intent_id: str, metadata: dict[str, str]):
    try:
        stripe.PaymentIntent.modify(payment_intent_id, metadata=metadata)
    except stripe.error.StripeError as exc:
        logger.warning("Failed to update Stripe metadata: %s", exc)


def create_order_from_cart(user, data) -> Order:
    idempotency_key = data.get("idempotency_key") or None
    if idempotency_key:
        existing = Order.objects.filter(
            user=user, idempotency_key=idempotency_key
        ).first()
        if existing:
            if not existing.payment_intent_id:
                amount = _to_stripe_amount(existing.total_price)
                payment_intent = _create_payment_intent(
                    amount, existing.currency, user.id, idempotency_key
                )
                existing.payment_intent_id = payment_intent.id
                existing.save(update_fields=["payment_intent_id"])
                _update_payment_intent_metadata(
                    payment_intent.id,
                    {
                        "user_id": str(user.id),
                        "order_id": str(existing.id),
                    },
                )
            existing._created = False
            return existing

    try:
        cart = Cart.objects.prefetch_related("items__product").get(user=user)
    except Cart.DoesNotExist as exc:
        raise ValueError("Cart is empty.") from exc

    items = list(cart.items.select_related("product"))
    if not items:
        raise ValueError("Cart is empty.")

    shipping_cost = data.get("shipping_cost") or Decimal("0.00")
    tax_amount = data.get("tax_amount") or Decimal("0.00")
    currency = data.get("currency") or None
    discount_code = data.get("discount_code") or None

    subtotal, total, resolved_currency = _compute_cart_totals(
        items, currency, shipping_cost, tax_amount
    )
    discount_amount = Decimal("0.00")
    if discount_code:
        _, discount_amount = _resolve_discount(
            discount_code, user, items, subtotal, lock=False
        )
        total -= discount_amount
        if total <= 0:
            raise ValueError("Order total must be greater than zero.")
    amount = _to_stripe_amount(total)

    payment_intent = _create_payment_intent(
        amount, resolved_currency, user.id, idempotency_key
    )

    try:
        with transaction.atomic():
            cart = _select_for_update(Cart.objects).get(pk=cart.pk)
            item_qs = CartItem.objects.select_related("product").filter(cart=cart)
            item_qs = _select_for_update(item_qs)
            items = list(item_qs)
            if not items:
                raise ValueError("Cart is empty.")

            product_ids = [item.product_id for item in items]
            product_qs = _select_for_update(Product.objects.filter(id__in=product_ids))
            products = {product.id: product for product in product_qs}

            for item in items:
                product = products.get(item.product_id)
                if not product or not product.is_published():
                    raise ValueError("One or more products are unavailable.")
                if item.quantity > product.inventory:
                    raise ValueError("Insufficient inventory for one or more items.")

            subtotal, total, resolved_currency = _compute_cart_totals(
                items, currency, shipping_cost, tax_amount
            )
            discount = None
            discount_amount = Decimal("0.00")
            if discount_code:
                discount, discount_amount = _resolve_discount(
                    discount_code, user, items, subtotal, lock=True
                )
                total -= discount_amount
                if total <= 0:
                    raise ValueError("Order total must be greater than zero.")
            if _to_stripe_amount(total) != amount:
                raise ValueError("Cart totals changed. Please retry checkout.")

            order = Order.objects.create(
                user=user,
                total_price=total,
                shipping_cost=shipping_cost,
                tax_amount=tax_amount,
                payment_intent_id=payment_intent.id,
                currency=resolved_currency,
                shipping_address=data.get("shipping_address"),
                billing_address=data.get("billing_address"),
                discount_code=discount.code if discount else None,
                discount_type=discount.discount_type if discount else None,
                discount_value=discount.value if discount else None,
                discount_amount=discount_amount if discount else None,
                is_gift=bool(data.get("is_gift")),
                gift_message=data.get("gift_message") or "",
                idempotency_key=idempotency_key,
            )

            order_items = []
            for item in items:
                product = products[item.product_id]
                order_items.append(
                    OrderItem(
                        order=order,
                        product=product,
                        product_name=product.product_name,
                        quantity=item.quantity,
                        unit_price=product.price,
                    )
                )

            OrderItem.objects.bulk_create(order_items)
            for item in items:
                Product.objects.filter(id=item.product_id).update(
                    inventory=F("inventory") - item.quantity
                )

            if discount:
                DiscountRedemption.objects.create(
                    discount=discount, user=user, order=order
                )
                Discount.objects.filter(id=discount.id).update(
                    times_used=F("times_used") + 1
                )

            cart.items.all().delete()
            cart.touch()
    except Exception:
        try:
            stripe.PaymentIntent.cancel(payment_intent.id)
        except stripe.error.StripeError:
            logger.warning("Failed to cancel Stripe PaymentIntent %s", payment_intent.id)
        raise

    _update_payment_intent_metadata(
        payment_intent.id,
        {
            "user_id": str(user.id),
            "order_id": str(order.id),
        },
    )

    order._created = True
    return order


def release_reserved_inventory(order: Order) -> None:
    items = order.items.select_related("product")
    for item in items:
        if item.product_id:
            Product.objects.filter(id=item.product_id).update(
                inventory=F("inventory") + item.quantity
            )


def _send_status_notifications(
    order_id: int, status: str, phone_number: str | None
) -> None:
    if phone_number:
        send_order_status_sms.delay(order_id, status, phone_number)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"order_{order_id}",
        {"type": "status.update", "status": status},
    )


def transition_order_status(
    order: Order, new_status: str, *, shipped_date=None
) -> Order:
    previous_status = order.status
    status_changed = new_status != previous_status
    update_fields = []

    if status_changed:
        order.status = new_status
        update_fields.append("status")
    if shipped_date is not None:
        order.shipped_date = shipped_date
        update_fields.append("shipped_date")

    if not update_fields:
        return order

    order.save(update_fields=update_fields)

    if not status_changed:
        return order

    phone_number = getattr(order.user, "phone_number", None)

    def _after_commit():
        if previous_status not in {
            Order.Status.CANCELED,
            Order.Status.FAILED,
        } and new_status in {
            Order.Status.CANCELED,
            Order.Status.FAILED,
        }:
            release_reserved_inventory(order)
        _send_status_notifications(order.id, new_status, phone_number)

    transaction.on_commit(_after_commit)
    return order


def generate_invoice_pdf(order: Order) -> bytes:
    """Generate a simple PDF invoice for the given order."""

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Invoice for Order #{order.id}")
    y -= 25
    p.drawString(50, y, f"Customer: {order.user.username}")
    y -= 40
    p.drawString(50, y, "Items:")
    y -= 20
    for item in order.items.all():
        p.drawString(
            60,
            y,
            f"{item.product_name} (x{item.quantity}) - ${item.unit_price}",
        )
        y -= 20
    y -= 20
    p.drawString(50, y, f"Total: ${order.total_price}")
    p.showPage()
    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
