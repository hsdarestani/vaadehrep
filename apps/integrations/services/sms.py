import logging
from typing import Any, Dict

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {settings.SMS_API_KEY}"} if settings.SMS_API_KEY else {}


def _base_url() -> str:
    return settings.SMS_GATEWAY_BASE_URL.rstrip("/") if settings.SMS_GATEWAY_BASE_URL else ""


def send_sms(mobile: str, text: str) -> bool:
    if not settings.SMS_API_KEY or not _base_url():
        logger.warning("SMS configuration incomplete; skipping send_sms")
        return False

    payload: Dict[str, Any] = {
        "to": mobile,
        "from": settings.SMS_SENDER_NUMBER,
        "text": text,
    }

    try:
        response = requests.post(f"{_base_url()}/messages", json=payload, headers=_headers(), timeout=10)
        response.raise_for_status()
        return True
    except Exception as exc:  # pragma: no cover - logging side-effect
        logger.exception("Failed to send SMS: %s", exc)
        return False


def send_otp(mobile: str, code: str) -> bool:
    text = f"کد ورود شما: {code}"
    return send_sms(mobile=mobile, text=text)
