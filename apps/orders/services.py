import math
from typing import Optional, Tuple

from addresses.models import Address
from catalog.models import Product
from core.models import AppSetting
from integrations.services import sms, telegram
from orders.models import Order
from vendors.models import Vendor, VendorLocation

# وضعیت‌هایی که سفارش را فعال نگه می‌دارند و جلوی ویرایش آدرس را می‌گیرند.
ACTIVE_ORDER_STATUSES = {
    "DRAFT",
    "PLACED",
    "CONFIRMED",
    "PREPARING",
    "READY",
    "OUT_FOR_DELIVERY",
}


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


def _haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    محاسبه فاصله تقریبی بین دو نقطه جغرافیایی بر حسب متر.
    """
    r = 6371_000  # شعاع زمین به متر
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return r * c


def get_default_delivery_fee() -> int:
    """
    حق‌الزحمه ارسال داخل محدوده. از AppSetting خوانده می‌شود و در صورت نبود، مقدار پیش‌فرض برمی‌گردد.
    """
    setting = AppSetting.objects.filter(key="default_delivery_fee_in_zone").first()
    if setting:
        value = setting.get_value()
        if isinstance(value, int):
            return value
    return 80000  # تومان/ریال بر اساس واحد پروژه


def vendor_active_orders_count(vendor: Vendor) -> int:
    """
    تعداد سفارش‌های فعال یک وندور (برای کنترل ظرفیت).
    """
    return vendor.orders.filter(status__in=ACTIVE_ORDER_STATUSES).count()


def evaluate_vendor_serviceability(
    vendor: Vendor, coords: Optional[dict]
) -> Tuple[bool, Optional[str], Optional[int], Optional[VendorLocation], Optional[float]]:
    """
    بررسی می‌کند آیا وندور برای مختصات داده‌شده قابل سرویس است یا خیر.
    خروجی: (is_serviceable, delivery_type, delivery_fee_amount, nearest_location, distance_meters)
    """
    if not vendor.is_active or not vendor.is_visible or not vendor.is_accepting_orders:
        return False, None, None, None, None

    if vendor.max_active_orders and vendor_active_orders_count(vendor) >= vendor.max_active_orders:
        return False, None, None, None, None

    nearest_location = None
    distance_meters = None
    if coords and coords.get("latitude") is not None and coords.get("longitude") is not None:
        lat = float(coords["latitude"])
        lng = float(coords["longitude"])
        for loc in vendor.locations.filter(is_active=True, lat__isnull=False, lng__isnull=False):
            dist = _haversine_distance_meters(lat, lng, float(loc.lat), float(loc.lng))
            if distance_meters is None or dist < distance_meters:
                distance_meters = dist
                nearest_location = loc

    # اگر مختصات نداشته باشیم، فرض می‌کنیم داخل محدوده هستیم و ارسال داخلی فعال است.
    if vendor.supports_in_zone_delivery:
        if nearest_location and nearest_location.service_radius_m:
            if distance_meters is not None and distance_meters <= nearest_location.service_radius_m:
                return True, "IN_ZONE", get_default_delivery_fee(), nearest_location, distance_meters
        elif nearest_location is None:
            return True, "IN_ZONE", get_default_delivery_fee(), None, None

    if vendor.supports_out_of_zone_snapp_cod:
        return True, "OUT_OF_ZONE_SNAPP", 0, nearest_location, distance_meters

    return False, None, None, nearest_location, distance_meters


def pick_nearest_available_vendor(coords: Optional[dict]) -> Optional[Vendor]:
    """
    نزدیک‌ترین وندور فعال و قابل سرویس‌دهی را بر اساس مختصات انتخاب می‌کند.
    """
    candidates = Vendor.objects.filter(is_active=True, is_visible=True, is_accepting_orders=True).prefetch_related(
        "locations"
    )
    chosen = None
    best_distance = None
    for vendor in candidates:
        is_ok, delivery_type, _, location, distance_m = evaluate_vendor_serviceability(vendor, coords)
        if not is_ok or not delivery_type:
            continue
        if best_distance is None or (distance_m is not None and distance_m < best_distance):
            chosen = vendor
            best_distance = distance_m
    return chosen


def suggest_products_for_user(user, limit: int = 4):
    """
    بر اساس سفارش‌های قبلی کاربر، چند محصول محبوب پیشنهاد می‌دهد.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return []
    product_ids = (
        Product.objects.filter(order_items__order__user=user)
        .order_by("-order_items__order__placed_at")
        .values_list("id", flat=True)
        .distinct()[:limit]
    )
    return list(product_ids)
