"""Client for interacting with the external ERP system."""

from typing import Any
import requests  # type: ignore[import-untyped]
from django.conf import settings


class ERPClientError(Exception):
    """Raised when the ERP client encounters an error."""


def get_inventory(product_id: str) -> int:
    """Fetch inventory level for ``product_id`` from the ERP system.

    Args:
        product_id: Identifier of the product.

    Returns:
        The available inventory level for the product.
    """
    base_url = getattr(settings, "ERP_API_URL", "").rstrip("/")
    if not base_url:
        raise ERPClientError("ERP_API_URL is not configured")

    url = f"{base_url}/inventory/{product_id}"
    headers = {}
    api_key = getattr(settings, "ERP_API_KEY", "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data: Any = response.json()
        return int(data.get("inventory", 0))
    except requests.RequestException as exc:  # pragma: no cover - network issues
        raise ERPClientError(str(exc)) from exc
