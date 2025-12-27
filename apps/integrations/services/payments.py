import logging
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from django.http import HttpRequest
from django.urls import reverse

logger = logging.getLogger(__name__)


def _base_url() -> str:
    base_url = settings.PAYMENT_GATEWAY_BASE_URL.rstrip("/") if settings.PAYMENT_GATEWAY_BASE_URL else ""
    if not base_url:
        base_url = "https://gateway.zibal.ir/v1"
    if not base_url.endswith("/v1"):
        base_url = f"{base_url}/v1"
    return base_url


def _merchant_id() -> str:
    return settings.PAYMENT_MERCHANT_ID


def _request_headers() -> Dict[str, str]:
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    api_key = getattr(settings, "PAYMENT_API_KEY", "") or ""
    if api_key:
        headers["Authorization"] = api_key
    return headers


def _normalize_phone(raw: str) -> str:
    if not raw:
        return ""
    p = str(raw).strip()
    return "".join(ch for ch in p if ch.isdigit())


def create_payment(order) -> Optional[Dict[str, Any]]:
    if not _base_url() or not _merchant_id():
        logger.warning("Payment gateway configuration missing; cannot create payment")
        return {"payment_url": None, "message": "gateway_configuration_missing"}

    site_base_url = getattr(settings, "SITE_BASE_URL", "") or getattr(settings, "FRONTEND_BASE_URL", "")
    callback_url = getattr(settings, "PAYMENT_CALLBACK_URL", "")
    if not callback_url and site_base_url:
        callback_url = f"{site_base_url.rstrip('/')}{reverse('payment-callback')}"
    if not callback_url:
        logger.warning("Payment callback URL missing; payment request may fail")

    payload: Dict[str, Any] = {
        "merchant": _merchant_id(),
        "amount": order.total_amount,
        "callbackUrl": callback_url,
        "orderId": str(order.short_code),
        "mobile": _normalize_phone(getattr(order.user, "phone", "")),
        "description": f"Order {order.short_code}",
    }

    try:
        response = requests.post(f"{_base_url()}/request", json=payload, headers=_request_headers(), timeout=15)
        response.raise_for_status()
        data = response.json()
        result = data.get("result")
        message = data.get("message")
        track_id = data.get("trackId")
        payment_url = f"https://gateway.zibal.ir/start/{track_id}" if track_id else None

        if result in {100, 201} and payment_url:
            return {**data, "payment_url": payment_url, "order_id": payload["orderId"], "message": message}

        logger.warning("Payment request failed: result=%s message=%s payload=%s", result, message, payload)
        return {"payment_url": None, "message": message, "result": result, "payload": payload}
    except Exception as exc:  # pragma: no cover - logging side-effect
        logger.exception("Failed to create payment: %s", exc)
        return {"payment_url": None, "message": "exception", "error": str(exc)}


def verify_payment(request: HttpRequest) -> Optional[Dict[str, Any]]:
    if not _base_url() or not _merchant_id():
        logger.warning("Payment gateway configuration missing; cannot verify payment")
        return None

    payload = request.data if hasattr(request, "data") else {}
    payload = payload or getattr(request, "POST", {})
    payload = payload or getattr(request, "GET", {})
    payload = dict(payload)
    track_id = payload.get("trackId") or payload.get("track_id")
    if not track_id:
        return None

    try:
        response = requests.post(
            f"{_base_url()}/verify",
            json={"merchant": _merchant_id(), "trackId": track_id},
            headers=_request_headers(),
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
            "message": data.get("message"),
            "result": data.get("result"),
        }
    except Exception as exc:  # pragma: no cover - logging side-effect
        logger.exception("Payment verification failed: %s", exc)
        return None
