import logging
from typing import Any, Dict, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


TELEGRAM_API_BASE = "https://api.telegram.org/bot"


def _bot_url(path: str) -> str:
    return f"{TELEGRAM_API_BASE}{settings.TELEGRAM_BOT_TOKEN}/{path}"


def send_message(
    chat_id: str,
    text: str,
    reply_markup: Optional[Dict[str, Any]] = None,
    parse_mode: Optional[str] = None,
) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram bot token missing; skipping send_message")
        return False

    payload: Dict[str, Any] = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        response = requests.post(_bot_url("sendMessage"), json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as exc:  # pragma: no cover - logging side-effect
        logger.exception("Failed to send Telegram message: %s", exc)
        return False


def set_webhook(webhook_url: str) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram bot token missing; cannot set webhook")
        return False
    if not webhook_url:
        logger.warning("Webhook URL missing; cannot set webhook")
        return False
    try:
        response = requests.post(_bot_url("setWebhook"), json={"url": webhook_url}, timeout=10)
        response.raise_for_status()
        data = response.json()
        ok = data.get("ok", False)
        if not ok:
            logger.warning("Failed to set webhook: %s", data)
        return ok
    except Exception as exc:  # pragma: no cover - logging side-effect
        logger.exception("Failed to set Telegram webhook: %s", exc)
        return False


def _status_label(status: str) -> str:
    return {
        "PENDING_PAYMENT": "در انتظار پرداخت",
        "PLACED": "ثبت شد",
        "CONFIRMED": "تایید شد",
        "PREPARING": "در حال آماده‌سازی",
        "READY": "آماده تحویل",
        "OUT_FOR_DELIVERY": "ارسال شد",
        "DELIVERED": "تحویل داده شد",
        "CANCELLED": "لغو شد",
        "FAILED": "ناموفق",
    }.get(status, status)


def status_label(status: str) -> str:
    return _status_label(status)


def build_order_action_keyboard(order) -> Dict[str, Any]:
    order_id = order.id
    return {
        "inline_keyboard": [
            [
                {"text": "تایید سفارش ✅", "callback_data": f"order:{order_id}:CONFIRMED"},
                {"text": "در حال آماده‌سازی 👩‍🍳", "callback_data": f"order:{order_id}:PREPARING"},
            ],
            [
                {"text": "آماده تحویل 📦", "callback_data": f"order:{order_id}:READY"},
                {"text": "ارسال شد 🛵", "callback_data": f"order:{order_id}:OUT_FOR_DELIVERY"},
            ],
            [{"text": "تحویل شد ✅", "callback_data": f"order:{order_id}:DELIVERED"}],
            [{"text": "لغو سفارش ❌", "callback_data": f"order:{order_id}:CANCELLED"}],
        ]
    }


def _format_order_text(order) -> str:
    customer_phone = getattr(order.user, "phone", "") or "-"
    vendor_name = getattr(order.vendor, "name", "") or "-"
    parts = [
        f"سفارش #{order.id}",
        f"فروشنده: {vendor_name}",
        f"مبلغ کل: {order.total_amount} {order.currency}",
        f"وضعیت فعلی: {_status_label(order.status)}",
        f"مشتری: {customer_phone}",
    ]
    return "\n".join(parts)


def send_order_notification_to_vendor(order) -> None:
    chat_id = getattr(order.vendor, "telegram_chat_id", "") or ""
    if not chat_id:
        logger.info("No vendor Telegram chat configured for vendor_id=%s", order.vendor_id)
        return

    text = _format_order_text(order)
    send_message(chat_id=chat_id, text=text, reply_markup=build_order_action_keyboard(order))


def send_order_notification_to_admin(order) -> None:
    admin_chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
    if not admin_chat_id:
        logger.info("TELEGRAM_ADMIN_CHAT_ID not set; skipping admin notification")
        return

    text = f"سفارش جدید/به‌روزرسانی #{order.id}\nوضعیت: {_status_label(order.status)}"
    send_message(chat_id=str(admin_chat_id), text=text, reply_markup=build_order_action_keyboard(order))
