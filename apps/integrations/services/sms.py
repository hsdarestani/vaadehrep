import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {settings.SMS_API_KEY}"} if settings.SMS_API_KEY else {}


def _base_url() -> str:
    return settings.SMS_GATEWAY_BASE_URL.rstrip("/") if settings.SMS_GATEWAY_BASE_URL else ""


def _rest_base_url() -> str:
    """
    برمی‌گرداند آدرس پایه REST برای ملی‌پیامک.
    اگر SMS_REST_BASE_URL تعریف شده باشد، همان را استفاده می‌کند،
    وگرنه دیفالت را می‌گذارد روی rest.payamak-panel.com
    """
    base = getattr(settings, "SMS_REST_BASE_URL", None)
    if not base:
        base = getattr(settings, "SMS_GATEWAY_BASE_URL", "https://rest.payamak-panel.com")
    return base.rstrip("/")


def _send_base_service_number_sms(
    mobile: str, body_id: int, text: str, mock_label: str = "PATTERN", extra_mock_fields: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    ارسال پیامک پترنی با وب‌سرویس BaseServiceNumber (ملی‌پیامک).
    """
    mode = getattr(settings, "SMS_MODE", "real")

    if mode == "mock":
        logger.warning(f"[SMS MOCK] {mock_label} to {mobile}: body_id={body_id} text={text}")
        mock_response = {
            "ok": True,
            "mode": "mock",
            "mobile": mobile,
            "text": str(text),
            "body_id": body_id,
        }
        if extra_mock_fields:
            mock_response.update(extra_mock_fields)
        return mock_response

    url = _rest_base_url() + "/api/SendSMS/BaseServiceNumber"
    payload = {
        "username": getattr(settings, "SMS_USERNAME", ""),
        "password": getattr(settings, "SMS_PASSWORD", ""),
        "text": str(text),
        "to": mobile,
        "bodyId": body_id,
    }

    try:
        resp = requests.post(url, data=payload, timeout=10)
    except Exception as e:
        logger.exception("Payamak-panel request failed")
        return {"ok": False, "error": str(e)}

    if resp.status_code != 200:
        logger.error("Payamak-panel HTTP error %s: %s", resp.status_code, resp.text)
        return {
            "ok": False,
            "http_status": resp.status_code,
            "raw": resp.text,
        }

    try:
        data = resp.json()
    except ValueError:
        logger.error("Payamak-panel non-JSON response: %s", resp.text)
        return {"ok": False, "raw": resp.text}

    logger.info("Payamak-panel response: %s", data)
    return data


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


def send_otp(mobile: str, code: str) -> Dict[str, Any]:
    """
    ارسال OTP با وب‌سرویس خدماتی (پترن) ملی‌پیامک.

    - اگر settings.SMS_MODE == "mock" باشد:
        فقط در لاگ می‌نویسد و درخواست واقعی نمی‌فرستد.
    - اگر "real" باشد:
        به وب‌سرویس BaseServiceNumber (REST) کال واقعی می‌زند.

    پارامترها:
        mobile: شماره موبایل به صورت 09...
        code  : کد یکبارمصرف (OTP) که در پترن {code} استفاده می‌شود.
    """

    body_id = getattr(settings, "SMS_OTP_BODY_ID", 0)
    response = _send_base_service_number_sms(
        mobile=mobile,
        body_id=body_id,
        text=str(code),
        mock_label="OTP",
        extra_mock_fields={"code": str(code)},
    )
    return response


def send_pattern_sms(mobile: str, body_id: int, params: Optional[list]) -> Dict[str, Any]:
    """
    ارسال پیامک بر اساس پترن (template) با body_id مشخص و پارامترهای جداشده با ; .
    """
    params = params or []
    text = ";".join(str(p) for p in params)
    return _send_base_service_number_sms(
        mobile=mobile,
        body_id=body_id,
        text=text,
        mock_label="PATTERN",
    )
