import logging
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from django.http import HttpRequest

logger = logging.getLogger(__name__)


def _base_url() -> str:
    return settings.PAYMENT_GATEWAY_BASE_URL.rstrip("/") if settings.PAYMENT_GATEWAY_BASE_URL else ""


def _merchant_id() -> str:
    return settings.PAYMENT_MERCHANT_ID


def create_payment(order) -> Optional[Dict[str, Any]]:
    if not _base_url() or not _merchant_id():
        logger.warning("Payment gateway configuration missing; cannot create payment")
        return None

    payload: Dict[str, Any] = {
        "merchant_id": _merchant_id(),
        "amount": order.total_amount,
        "currency": order.currency,
        "order_id": str(order.id),
        "callback_url": f"{_base_url()}/callback/",
        "meta": {"customer": order.user.phone},
    }

    try:
        response = requests.post(f"{_base_url()}/payments", json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as exc:  # pragma: no cover - logging side-effect
        logger.exception("Failed to create payment: %s", exc)
        return None


def verify_payment(request: HttpRequest) -> Optional[Dict[str, Any]]:
    if not _base_url() or not _merchant_id():
        logger.warning("Payment gateway configuration missing; cannot verify payment")
        return None

    payload = request.data if hasattr(request, "data") else {}
    payload = payload or getattr(request, "POST", {})
    payload = dict(payload)

    try:
        response = requests.post(f"{_base_url()}/payments/verify", json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as exc:  # pragma: no cover - logging side-effect
        logger.exception("Payment verification failed: %s", exc)
        return None
