import logging
from typing import Any, Dict, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


TELEGRAM_API_BASE = "https://api.telegram.org/bot"


def _bot_url(path: str) -> str:
    return f"{TELEGRAM_API_BASE}{settings.TELEGRAM_BOT_TOKEN}/{path}"


def send_message(chat_id: str, text: str, reply_markup: Optional[Dict[str, Any]] = None) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram bot token missing; skipping send_message")
        return False

    payload: Dict[str, Any] = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        response = requests.post(_bot_url("sendMessage"), json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as exc:  # pragma: no cover - logging side-effect
        logger.exception("Failed to send Telegram message: %s", exc)
        return False


def send_order_notification_to_vendor(order) -> None:
    chat_id = getattr(order.vendor, "telegram_chat_id", "") or ""
    if not chat_id:
        logger.info("No vendor Telegram chat configured for vendor_id=%s", order.vendor_id)
        return

    text = f"سفارش جدید #{order.id}\nمبلغ: {order.total_amount} {order.currency}"
    send_message(chat_id=chat_id, text=text)


def send_order_notification_to_admin(order) -> None:
    admin_chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
    if not admin_chat_id:
        logger.info("TELEGRAM_ADMIN_CHAT_ID not set; skipping admin notification")
        return

    text = f"سفارش جدید/به‌روزرسانی #{order.id} وضعیت {order.status}"
    send_message(chat_id=admin_chat_id, text=text)
