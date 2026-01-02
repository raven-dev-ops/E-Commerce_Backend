from __future__ import annotations

from typing import Any, Dict, Optional

import requests  # type: ignore[import-untyped]


class ECommerceClient:
    """Lightweight client for interacting with the e-commerce API."""

    def __init__(self, base_url: str, token: Optional[str] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def get_products(self, params: Optional[Dict[str, Any]] = None) -> Any:
        """Return a list of products from the API."""
        url = f"{self.base_url}/api/v1/products/"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def validate_discount(
        self, code: str, order_total: Optional[str] = None
    ) -> Any:
        """Validate a discount code for the current user."""
        url = f"{self.base_url}/api/v1/discounts/discounts/validate/"
        payload: Dict[str, Any] = {"code": code}
        if order_total is not None:
            payload["order_total"] = order_total
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def get_reviews(self, product_id: Optional[int] = None) -> Any:
        """Return a list of reviews, optionally filtered by product."""
        url = f"{self.base_url}/api/v1/reviews/reviews/"
        params = {"product_id": product_id} if product_id else None
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def create_review(
        self, product_id: int, rating: int, title: str = "", body: str = ""
    ) -> Any:
        """Create a review for a product."""
        url = f"{self.base_url}/api/v1/reviews/reviews/"
        payload = {
            "product_id": product_id,
            "rating": rating,
            "title": title,
            "body": body,
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
