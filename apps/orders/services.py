from typing import Optional

from integrations.services import sms, telegram
from orders.models import Order


ORDER_STATUS_EVENTS = {
    "PLACED": "ORDER_CREATED",
    "CONFIRMED": "ORDER_CONFIRMED",
    "PREPARING": "ORDER_PREPARING",
    "READY": "ORDER_READY",
    "OUT_FOR_DELIVERY": "ORDER_OUT_FOR_DELIVERY",
    "DELIVERED": "ORDER_COMPLETED",
    "CANCELLED": "ORDER_CANCELLED",
    "FAILED": "ORDER_FAILED",
}


def notify_order_created(order: Order) -> None:
    telegram.send_order_notification_to_vendor(order)
    telegram.send_order_notification_to_admin(order)
    sms.send_sms(mobile=order.user.phone, text=f"سفارش شما ثبت شد. کد سفارش: {order.short_code}")


def handle_order_status_change(order: Order, changed_by_user=None) -> None:
    event = ORDER_STATUS_EVENTS.get(order.status)
    if order.status in {"CONFIRMED", "PREPARING", "READY", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED", "FAILED"}:
        telegram.send_order_notification_to_vendor(order)
        telegram.send_order_notification_to_admin(order)

    if order.status in {"CONFIRMED", "OUT_FOR_DELIVERY", "DELIVERED"}:
        status_texts = {
            "CONFIRMED": "تایید شد",
            "OUT_FOR_DELIVERY": "در حال ارسال",
            "DELIVERED": "تحویل داده شد",
        }
        sms.send_sms(
            mobile=order.user.phone,
            text=f"وضعیت سفارش شما: {status_texts.get(order.status, order.status)}",
        )
