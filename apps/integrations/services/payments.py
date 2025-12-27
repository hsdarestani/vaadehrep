import logging
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from django.http import HttpRequest
from django.urls import reverse

logger = logging.getLogger(__name__)


def _base_url() -> str:
    if settings.PAYMENT_GATEWAY_BASE_URL:
        return settings.PAYMENT_GATEWAY_BASE_URL.rstrip("/")
    return "https://gateway.zibal.ir/v1"


def _merchant_id() -> str:
    return settings.PAYMENT_MERCHANT_ID


def create_payment(order) -> Optional[Dict[str, Any]]:
    if not _base_url() or not _merchant_id():
        logger.warning("Payment gateway configuration missing; cannot create payment")
        return None

    callback_url = getattr(settings, "PAYMENT_CALLBACK_URL", "")
    if not callback_url and getattr(settings, "SITE_BASE_URL", ""):
        callback_url = f"{settings.SITE_BASE_URL.rstrip('/')}{reverse('payment-callback')}"
    if not callback_url:
        logger.warning("Payment callback URL missing; payment request may fail")

    payload: Dict[str, Any] = {
        "merchant": _merchant_id(),
        "amount": order.total_amount,
        "callbackUrl": callback_url,
        "orderId": order.short_code,
        "mobile": order.user.phone,
    }

    try:
        response = requests.post(f"{_base_url()}/request", json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("result") not in {100, 201}:
            logger.warning("Payment request failed: %s", data)
            return None

        track_id = data.get("trackId")
        payment_url = f"https://gateway.zibal.ir/start/{track_id}" if track_id else None
        return {**data, "payment_url": payment_url, "order_id": payload["orderId"]}
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
    track_id = payload.get("trackId") or payload.get("track_id")
    if not track_id:
        return None

    try:
        response = requests.post(
            f"{_base_url()}/verify",
            json={"merchant": _merchant_id(), "trackId": track_id},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        payment_success = data.get("result") in {100, 101}
        order_id = data.get("orderId")
        return {
            "order_id": order_id,
            "status": "PAID" if payment_success else "FAILED",
            "ref_number": data.get("refNumber"),
            "track_id": track_id,
        }
    except Exception as exc:  # pragma: no cover - logging side-effect
        logger.exception("Payment verification failed: %s", exc)
        return None
