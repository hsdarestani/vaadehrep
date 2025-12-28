import logging
from typing import Any, Dict, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


TELEGRAM_API_BASE = "https://api.telegram.org/bot"
ORDER_EVENT_LABELS = {
    "ORDER_CREATED": "ثبت سفارش",
    "ORDER_PAYMENT_VERIFIED": "پرداخت تایید شد",
    "ORDER_PENDING_PAYMENT": "در انتظار پرداخت",
    "ORDER_CONFIRMED": "تایید سفارش",
    "ORDER_PREPARING": "در حال آماده‌سازی",
    "ORDER_READY": "آماده تحویل",
    "ORDER_OUT_FOR_DELIVERY": "ارسال شد",
    "ORDER_COMPLETED": "تحویل داده شد",
    "ORDER_CANCELLED": "لغو سفارش",
    "ORDER_FAILED": "ناموفق",
}


def _bot_url(path: str) -> str:
    return f"{TELEGRAM_API_BASE}{settings.TELEGRAM_BOT_TOKEN}/{path}"


def send_message(
    chat_id: str,
    text: str,
    reply_markup: Optional[Dict[str, Any]] = None,
    parse_mode: Optional[str] = None,
    disable_web_page_preview: bool = True,
    protect_content: bool = False,
) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram bot token missing; skipping send_message")
        return False

    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": disable_web_page_preview,
        "protect_content": protect_content,
    }
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


def _order_recipient_details(order):
    address = getattr(order, "delivery_address", None)
    receiver_name = getattr(address, "receiver_name", "") or getattr(order.user, "full_name", "") or "مشتری"
    receiver_phone = getattr(address, "receiver_phone", "") or getattr(order.user, "phone", "") or "-"

    address_text = ""
    if address:
        if address.full_text:
            address_text = address.full_text
        else:
            parts = [address.city, address.district, address.street, address.alley, address.building]
            address_text = " ".join([p for p in parts if p]).strip()

    coords = None
    if address and address.latitude is not None and address.longitude is not None:
        coords = (float(address.latitude), float(address.longitude))
    else:
        meta = order.meta or {}
        customer_location = meta.get("customer_location") if isinstance(meta, dict) else None
        if isinstance(customer_location, dict):
            lat = customer_location.get("latitude")
            lng = customer_location.get("longitude")
            if lat is not None and lng is not None:
                coords = (float(lat), float(lng))

    return receiver_name, receiver_phone, address_text, coords


def build_order_action_keyboard(order, for_vendor: bool = False) -> Dict[str, Any]:
    order_id = order.id
    if for_vendor:
        return {
            "inline_keyboard": [
                [{"text": "در حال آماده‌سازی 👩‍🍳", "callback_data": f"order:{order_id}:PREPARING"}],
                [{"text": "ارسال شد 🛵", "callback_data": f"order:{order_id}:OUT_FOR_DELIVERY"}],
            ]
        }

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


def build_main_menu_keyboard(has_addresses: bool = False, has_active_order: bool = False) -> Dict[str, Any]:
    inline_keyboard = [
        [{"text": "سفارش جدید 🍽️", "callback_data": "menu:order"}],
        [{"text": "آدرس‌ها 📍", "callback_data": "menu:addresses"}],
    ]
    if has_addresses:
        inline_keyboard.insert(1, [{"text": "سفارش مجدد ⚡", "callback_data": "menu:reorder"}])
    if has_active_order:
        inline_keyboard.append([{"text": "پیگیری سفارش 🚚", "callback_data": "menu:track"}])
    return {"inline_keyboard": inline_keyboard}


def build_address_keyboard(addresses) -> Dict[str, Any]:
    rows = []
    for addr in addresses:
        label = addr.title or addr.full_text or "آدرس"
        rows.append([{"text": label[:32], "callback_data": f"address:{addr.id}"}])
    rows.append([{"text": "ارسال موقعیت زنده 📡", "callback_data": "menu:share_location"}])
    return {"inline_keyboard": rows}


def build_menu_keyboard(products) -> Dict[str, Any]:
    rows = []
    for product in products:
        rows.append([{"text": f"{product.name_fa} • {product.base_price:,}", "callback_data": f"product:{product.id}"}])
    rows.append([{"text": "سبد خرید 🛒", "callback_data": "cart:review"}])
    return {"inline_keyboard": rows}


def _format_order_text(order) -> str:
    vendor_name = getattr(order.vendor, "name", "") or "-"
    receiver_name, receiver_phone, address_text, coords = _order_recipient_details(order)
    items = getattr(order, "items", None)
    items_text = ""
    if items and hasattr(items, "all"):
        rendered_items = []
        for item in items.all():
            line = f"- {getattr(item, 'product_title_snapshot', '-')}"
            qty = getattr(item, "quantity", None)
            if qty:
                line += f" ×{qty}"
            rendered_items.append(line)
        items_text = "\n".join(rendered_items)

    location_line = ""
    if coords:
        location_line = f"لوکیشن: https://maps.google.com/?q={coords[0]},{coords[1]}"

    amount = getattr(order, "total_amount", None)
    amount_text = f"{amount:,}" if isinstance(amount, (int, float)) else "-"

    parts = [
        f"سفارش {getattr(order, 'short_code', '') or order.id}",
        f"فروشنده: {vendor_name}",
        f"مبلغ کل: {amount_text} {getattr(order, 'currency', '')}",
        f"وضعیت فعلی: {_status_label(order.status)}",
        f"مشتری: {receiver_name} • {receiver_phone}",
    ]
    if address_text:
        parts.append(f"آدرس: {address_text}")
    if location_line:
        parts.append(location_line)
    if items_text:
        parts.append("اقلام:")
        parts.append(items_text)
    return "\n".join(parts)


def _event_label(event: Optional[str]) -> str:
    if not event:
        return ""
    return ORDER_EVENT_LABELS.get(event, event)


def _format_vendor_admin_order_event_text(order, event: Optional[str]) -> str:
    event_label = _event_label(event)
    prefix = f"رویداد: {event_label}\n" if event_label else ""
    return f"{prefix}{_format_order_text(order)}"


def _format_customer_order_event_text(order, event: Optional[str]) -> str:
    vendor_name = getattr(order.vendor, "name", "") or "-"
    status_text = _status_label(order.status)
    if event == "ORDER_CREATED":
        return f"سفارش شما ثبت شد ✅\nکد سفارش: {order.short_code}\nفروشنده: {vendor_name}\nوضعیت: {status_text}"
    if event == "ORDER_PAYMENT_VERIFIED":
        return f"پرداخت سفارش {order.short_code} تایید شد.\nوضعیت فعلی: {status_text}"
    if event:
        return f"به‌روزرسانی سفارش {order.short_code} ({_event_label(event)}):\nوضعیت: {status_text}"
    return f"به‌روزرسانی سفارش {order.short_code}:\nوضعیت: {status_text}"


def send_order_notification_to_vendor(order, event: Optional[str] = None) -> None:
    chat_id = getattr(order.vendor, "telegram_chat_id", "") or ""
    if not chat_id:
        logger.info("No vendor Telegram chat configured for vendor_id=%s", order.vendor_id)
        return

    text = _format_vendor_admin_order_event_text(order, event)
    send_message(chat_id=chat_id, text=text, reply_markup=build_order_action_keyboard(order, for_vendor=True))


def send_order_notification_to_admin(order, event: Optional[str] = None) -> None:
    admin_chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
    if not admin_chat_id:
        logger.info("TELEGRAM_ADMIN_CHAT_ID not set; skipping admin notification")
        return

    text = _format_vendor_admin_order_event_text(order, event)
    send_message(chat_id=str(admin_chat_id), text=text, reply_markup=build_order_action_keyboard(order))


def send_order_notification_to_customer(order, event: Optional[str] = None) -> None:
    tg_profile = getattr(order.user, "telegram", None)
    chat_id = getattr(tg_profile, "telegram_user_id", None)
    if not chat_id:
        logger.info("No Telegram profile for user_id=%s; skipping customer notification", order.user_id)
        return
    text = _format_customer_order_event_text(order, event)
    send_message(chat_id=str(chat_id), text=text)


def dispatch_order_event(order, event: Optional[str] = None) -> None:
    send_order_notification_to_vendor(order, event=event)
    send_order_notification_to_admin(order, event=event)
    send_order_notification_to_customer(order, event=event)
