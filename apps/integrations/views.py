import logging
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser

from accounts.models import TelegramUser, User
from addresses.models import Address
from catalog.models import Product
from integrations.models import (
    ExternalRequestLog,
    IntegrationEndpoint,
    IntegrationProvider,
    ProviderHealthCheck,
    VendorIntegrationConfig,
)
from integrations.services import payments, telegram
from orders.models import Order, OrderStatusHistory
from orders.services import (
    ACTIVE_ORDER_STATUSES,
    evaluate_vendor_serviceability,
    notify_order_created,
    notify_payment_verified,
    pick_nearest_available_vendor,
)
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from vendors.models import Vendor

logger = logging.getLogger(__name__)


def _normalize_phone(raw: str) -> str:
    if not raw:
        return ""
    p = str(raw).strip()
    return "".join(ch for ch in p if ch.isdigit())


def _get_or_create_user_by_phone(phone: str) -> User:
    phone_normalized = _normalize_phone(phone)
    user, created = User.objects.get_or_create(phone=phone_normalized, defaults={"is_active": True})
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    return user


def _send_main_menu(tg_user: TelegramUser):
    has_addresses = Address.objects.filter(user=tg_user.user, is_active=True).exists()
    has_active_order = Order.objects.filter(user=tg_user.user, status__in=ACTIVE_ORDER_STATUSES).exists()
    telegram.send_message(
        chat_id=str(tg_user.telegram_user_id),
        text="حساب شما لینک شد. از منوی زیر استفاده کنید.",
        reply_markup=telegram.build_main_menu_keyboard(has_addresses=has_addresses, has_active_order=has_active_order),
    )
    return HttpResponse(status=status.HTTP_200_OK)


def _payment_return_url():
    redirect_url = getattr(settings, "PAYMENT_RETURN_URL", "")
    if not redirect_url:
        site_base = getattr(settings, "FRONTEND_BASE_URL", "") or getattr(settings, "SITE_BASE_URL", "")
        if site_base:
            redirect_url = f"{site_base.rstrip('/')}/payment-result"
    return redirect_url


def _redirect_or_json(request, payload, *, status_code=status.HTTP_200_OK, redirect_url=""):
    redirect_url = redirect_url or _payment_return_url()
    if request.method == "GET" and redirect_url:
        query_params = {
            "order_id": payload.get("order_id"),
            "order_code": payload.get("order_code"),
            "payment_status": payload.get("payment_status"),
            "order_status": payload.get("order_status"),
            "track_id": payload.get("track_id"),
            "ref_number": payload.get("ref_number"),
            "result": payload.get("result"),
            "message": payload.get("message"),
        }
        query_string = urlencode({k: v for k, v in query_params.items() if v not in [None, ""]})
        redirect_target = f"{redirect_url}?{query_string}" if query_string else redirect_url
        return redirect(redirect_target)

    return JsonResponse(payload, status=status_code)


def _handle_live_location(tg_user: TelegramUser, location: dict):
    chat_id = tg_user.telegram_user_id
    lat = location.get("latitude")
    lng = location.get("longitude")
    if lat is None or lng is None:
        telegram.send_message(chat_id=str(chat_id), text="موقعیت دریافت نشد. دوباره تلاش کنید.")
        return HttpResponse(status=status.HTTP_200_OK)

    coords = {"latitude": float(lat), "longitude": float(lng)}
    vendor = pick_nearest_available_vendor(coords)
    if not vendor:
        telegram.send_message(chat_id=str(chat_id), text="در حال حاضر آشپزخانه فعالی نزدیک شما نیست.")
        return HttpResponse(status=status.HTTP_200_OK)

    ok, delivery_type, delivery_fee, _, _ = evaluate_vendor_serviceability(vendor, coords)
    if not ok or not delivery_type:
        telegram.send_message(chat_id=str(chat_id), text="در این موقعیت امکان ارسال نداریم.")
        return HttpResponse(status=status.HTTP_200_OK)

    address, _ = Address.objects.get_or_create(
        user=tg_user.user,
        full_text="موقعیت زنده تلگرام",
        defaults={"title": "موقعیت زنده", "latitude": lat, "longitude": lng, "receiver_phone": tg_user.user.phone},
    )
    address.latitude = lat
    address.longitude = lng
    address.save(update_fields=["latitude", "longitude", "updated_at"])

    products = Product.objects.filter(
        vendor=vendor, is_active=True, is_available=True, is_available_today=True
    ).order_by("sort_order", "id")

    tg_state = tg_user.state or {}
    tg_state.update(
        {
            "address_id": address.id,
            "vendor_id": vendor.id,
            "delivery_type": delivery_type,
            "delivery_fee": delivery_fee or 0,
            "cart": tg_state.get("cart") or [],
            "coords": coords,
        }
    )
    tg_user.state = tg_state
    tg_user.save(update_fields=["state"])

    telegram.send_message(
        chat_id=str(chat_id),
        text=f"نزدیک‌ترین آشپزخانه انتخاب شد: {vendor.name}\nروش ارسال: {'پس‌کرایه' if delivery_type == 'OUT_OF_ZONE_SNAPP' else 'پیک داخلی'}",
        reply_markup=telegram.build_menu_keyboard(products),
    )
    return HttpResponse(status=status.HTTP_200_OK)


class IntegrationProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationProvider
        fields = [
            "id",
            "kind",
            "code",
            "name",
            "base_url",
            "is_active",
            "credentials_ref",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class IntegrationEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationEndpoint
        fields = [
            "id",
            "provider",
            "code",
            "path",
            "method",
            "timeout_seconds",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class VendorIntegrationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorIntegrationConfig
        fields = [
            "id",
            "vendor",
            "provider",
            "config",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ExternalRequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalRequestLog
        fields = [
            "id",
            "provider",
            "endpoint",
            "order",
            "vendor",
            "user",
            "trace_id",
            "request_url",
            "request_method",
            "request_headers",
            "request_body",
            "response_status",
            "response_headers",
            "response_body",
            "duration_ms",
            "outcome",
            "error_message",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ProviderHealthCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderHealthCheck
        fields = [
            "id",
            "provider",
            "status",
            "latency_ms",
            "details",
            "checked_at",
        ]
        read_only_fields = ["id", "checked_at"]


class IntegrationProviderViewSet(viewsets.ModelViewSet):
    queryset = IntegrationProvider.objects.all().order_by("code")
    serializer_class = IntegrationProviderSerializer
    permission_classes = [IsAdminUser]


class IntegrationEndpointViewSet(viewsets.ModelViewSet):
    queryset = IntegrationEndpoint.objects.select_related("provider").all().order_by("provider__code", "code")
    serializer_class = IntegrationEndpointSerializer
    permission_classes = [IsAdminUser]


class VendorIntegrationConfigViewSet(viewsets.ModelViewSet):
    queryset = VendorIntegrationConfig.objects.select_related("vendor", "provider").all().order_by("-created_at")
    serializer_class = VendorIntegrationConfigSerializer
    permission_classes = [IsAdminUser]


class ExternalRequestLogViewSet(viewsets.ModelViewSet):
    queryset = ExternalRequestLog.objects.all().order_by("-created_at")
    serializer_class = ExternalRequestLogSerializer
    permission_classes = [IsAdminUser]


class ProviderHealthCheckViewSet(viewsets.ModelViewSet):
    queryset = ProviderHealthCheck.objects.select_related("provider").all().order_by("-checked_at")
    serializer_class = ProviderHealthCheckSerializer
    permission_classes = [IsAdminUser]


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def telegram_webhook(request, secret: str):
    if settings.TELEGRAM_WEBHOOK_SECRET and secret != settings.TELEGRAM_WEBHOOK_SECRET:
        return HttpResponse(status=status.HTTP_403_FORBIDDEN)

    update = request.data or {}
    callback_query = update.get("callback_query") or {}
    if callback_query:
        return _handle_telegram_callback(callback_query)

    message = update.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = message.get("text", "")
    contact = message.get("contact") or {}
    location = message.get("location") or {}

    if not chat_id:
        return HttpResponse(status=status.HTTP_200_OK)

    if text.startswith("/start"):
        telegram.send_message(
            chat_id=str(chat_id),
            text="برای ادامه، لطفا شماره موبایل خود را با دکمه زیر ارسال کنید.",
            reply_markup={"keyboard": [[{"text": "اشتراک‌گذاری شماره 📱", "request_contact": True}]], "resize_keyboard": True},
        )
        return HttpResponse(status=status.HTTP_200_OK)

    if contact:
        phone = _normalize_phone(contact.get("phone_number"))
        if not phone:
            telegram.send_message(chat_id=str(chat_id), text="شماره معتبر نیست. لطفا دوباره ارسال کنید.")
            return HttpResponse(status=status.HTTP_200_OK)

        user = _get_or_create_user_by_phone(phone)
        tg_user, _ = TelegramUser.objects.update_or_create(
            telegram_user_id=chat_id,
            defaults={
                "user": user,
                "username": chat.get("username", ""),
                "first_name": chat.get("first_name", ""),
                "last_name": chat.get("last_name", ""),
                "language_code": chat.get("language_code", ""),
                "is_bot": chat.get("is_bot", False),
                "state": {},
            },
        )
        return _send_main_menu(tg_user)

    tg_user = TelegramUser.objects.filter(telegram_user_id=chat_id).select_related("user").first()
    if not tg_user:
        telegram.send_message(
            chat_id=str(chat_id),
            text="برای شروع لازم است شماره موبایل خود را با دکمه اشتراک‌گذاری ارسال کنید.",
            reply_markup={"keyboard": [[{"text": "اشتراک‌گذاری شماره 📱", "request_contact": True}]], "resize_keyboard": True},
        )
        return HttpResponse(status=status.HTTP_200_OK)

    if location:
        return _handle_live_location(tg_user, location)

    normalized_text = (text or "").strip()
    if normalized_text in {"منو", "menu", "Menu"}:
        return _send_main_menu(tg_user)
    if normalized_text in {"سفارش‌های من", "orders"}:
        return _handle_menu_callback(chat_id, "menu:track")

    telegram.send_message(chat_id=str(chat_id), text="از دکمه‌ها برای ادامه استفاده کنید.")
    return HttpResponse(status=status.HTTP_200_OK)


def _handle_telegram_callback(callback_query: dict):
    data = callback_query.get("data") or ""
    message = callback_query.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if not chat_id:
        return HttpResponse(status=status.HTTP_200_OK)

    if data.startswith("order:"):
        return _handle_order_status_callback(chat_id, data)

    if data.startswith("menu:") or data.startswith("address:") or data.startswith("product:") or data.startswith("cart:"):
        return _handle_menu_callback(chat_id, data)

    telegram.send_message(chat_id=str(chat_id), text="دستور ناشناخته است.")
    return HttpResponse(status=status.HTTP_200_OK)


def _handle_order_status_callback(chat_id, data: str):
    parts = data.split(":")
    if len(parts) != 3:
        return HttpResponse(status=status.HTTP_200_OK)

    _, order_id, target_status = parts
    from orders.models import Order, OrderStatusHistory  # local import
    from orders.services import handle_order_status_change

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        telegram.send_message(chat_id=str(chat_id), text="سفارش پیدا نشد.")
        return HttpResponse(status=status.HTTP_200_OK)

    vendor_chat_id = getattr(order.vendor, "telegram_chat_id", "") or ""
    admin_chat_id = str(settings.TELEGRAM_ADMIN_CHAT_ID) if settings.TELEGRAM_ADMIN_CHAT_ID else ""
    if str(chat_id) not in {str(vendor_chat_id), admin_chat_id}:
        telegram.send_message(chat_id=str(chat_id), text="شما مجاز به تغییر این سفارش نیستید.")
        return HttpResponse(status=status.HTTP_200_OK)

    if target_status == order.status:
        telegram.send_message(chat_id=str(chat_id), text="وضعیت سفارش قبلاً روی همین حالت است.")
        return HttpResponse(status=status.HTTP_200_OK)

    valid_statuses = {
        "CONFIRMED",
        "PREPARING",
        "READY",
        "OUT_FOR_DELIVERY",
        "DELIVERED",
        "CANCELLED",
    }
    if target_status not in valid_statuses:
        telegram.send_message(chat_id=str(chat_id), text="دستور ناشناخته است.")
        return HttpResponse(status=status.HTTP_200_OK)

    previous_status = order.status
    order.status = target_status
    order.save(update_fields=["status"])
    OrderStatusHistory.objects.create(
        order=order,
        from_status=previous_status,
        to_status=order.status,
        changed_by_type="VENDOR" if str(chat_id) == str(vendor_chat_id) else "ADMIN",
    )
    handle_order_status_change(order)
    telegram.send_message(
        chat_id=str(chat_id),
        text=f"وضعیت سفارش به {telegram.status_label(order.status)} تغییر کرد.",
        reply_markup=telegram.build_order_action_keyboard(order),
    )
    return HttpResponse(status=status.HTTP_200_OK)


def _handle_menu_callback(chat_id, data: str):
    tg_user = TelegramUser.objects.filter(telegram_user_id=chat_id).select_related("user").first()
    if not tg_user:
        telegram.send_message(chat_id=str(chat_id), text="برای استفاده ابتدا شماره موبایل خود را ارسال کنید.")
        return HttpResponse(status=status.HTTP_200_OK)

    user = tg_user.user

    if data == "menu:order":
        addresses = Address.objects.filter(user=user, is_active=True)
        if not addresses.exists():
            telegram.send_message(
                chat_id=str(chat_id),
                text="ابتدا موقعیت یا آدرس خود را ارسال کنید. از دکمه ارسال موقعیت تلگرام استفاده کنید.",
                reply_markup={"keyboard": [[{"text": "اشتراک‌گذاری موقعیت 📡", "request_location": True}]], "resize_keyboard": True},
            )
            return HttpResponse(status=status.HTTP_200_OK)
        telegram.send_message(
            chat_id=str(chat_id),
            text="آدرس تحویل را انتخاب کنید یا موقعیت زنده بفرستید.",
            reply_markup=telegram.build_address_keyboard(addresses),
        )
        return HttpResponse(status=status.HTTP_200_OK)

    if data == "menu:share_location":
        telegram.send_message(
            chat_id=str(chat_id),
            text="برای ارسال موقعیت زنده، از گزینه ارسال Location در تلگرام استفاده کنید.",
        )
        return HttpResponse(status=status.HTTP_200_OK)

    if data == "menu:addresses":
        addresses = Address.objects.filter(user=user, is_active=True)
        if not addresses.exists():
            telegram.send_message(
                chat_id=str(chat_id),
                text="هیچ آدرسی ثبت نشده است. از وب یا ارسال موقعیت برای ثبت استفاده کنید.",
                reply_markup={"inline_keyboard": [[{"text": "ثبت آدرس جدید", "callback_data": "menu:order"}]]},
            )
            return HttpResponse(status=status.HTTP_200_OK)
        telegram.send_message(
            chat_id=str(chat_id),
            text="آدرس‌های شما:",
            reply_markup=telegram.build_address_keyboard(addresses),
        )
        return HttpResponse(status=status.HTTP_200_OK)

    if data == "menu:reorder":
        last_order = (
            Order.objects.filter(user=user, status__in=["DELIVERED", "CANCELLED", "FAILED"])
            .order_by("-placed_at")
            .prefetch_related("items__product")
            .first()
        )
        if not last_order:
            telegram.send_message(chat_id=str(chat_id), text="سفارشی برای تکرار یافت نشد.")
            return HttpResponse(status=status.HTTP_200_OK)
        tg_user.state = {
            "cart": [
                {
                    "product_id": str(item.product_id),
                    "quantity": item.quantity,
                }
                for item in last_order.items.all()
            ],
            "address_id": getattr(last_order, "delivery_address_id", None),
            "vendor_id": getattr(last_order, "vendor_id", None),
            "delivery_type": getattr(last_order.delivery, "delivery_type", None) if hasattr(last_order, "delivery") else None,
        }
        tg_user.save(update_fields=["state"])
        telegram.send_message(
            chat_id=str(chat_id),
            text="سبد خرید از آخرین سفارش بازسازی شد. برای ادامه آدرس را انتخاب کنید.",
            reply_markup=telegram.build_main_menu_keyboard(has_addresses=True, has_active_order=False),
        )
        return HttpResponse(status=status.HTTP_200_OK)

    if data == "menu:track":
        active_order = (
            Order.objects.filter(user=user, status__in=ACTIVE_ORDER_STATUSES)
            .order_by("-placed_at")
            .first()
        )
        if not active_order:
            telegram.send_message(chat_id=str(chat_id), text="سفارش فعالی وجود ندارد.")
            return HttpResponse(status=status.HTTP_200_OK)
        payment_meta = active_order.meta.get("payment") if isinstance(active_order.meta, dict) else {}
        payment_url = None
        if isinstance(payment_meta, dict):
            payment_url = payment_meta.get("payment_url") or payment_meta.get("paymentUrl") or payment_meta.get("url")
        buttons = []
        if active_order.status == "PENDING_PAYMENT" and active_order.payment_status != "PAID" and payment_url:
            buttons.append([{"text": "پرداخت سفارش 💳", "url": payment_url}])
        telegram.send_message(
            chat_id=str(chat_id),
            text=f"وضعیت سفارش {active_order.short_code}: {telegram.status_label(active_order.status)}",
            reply_markup={"inline_keyboard": buttons} if buttons else None,
        )
        return HttpResponse(status=status.HTTP_200_OK)

    if data.startswith("address:"):
        address_id = data.split(":")[1]
        address = Address.objects.filter(id=address_id, user=user, is_active=True).first()
        if not address:
            telegram.send_message(chat_id=str(chat_id), text="آدرس پیدا نشد.")
            return HttpResponse(status=status.HTTP_200_OK)
        coords = None
        if address.latitude and address.longitude:
            coords = {"latitude": float(address.latitude), "longitude": float(address.longitude)}
        vendor = pick_nearest_available_vendor(coords)
        if not vendor:
            telegram.send_message(chat_id=str(chat_id), text="در حال حاضر فروشنده‌ای فعال نیست.")
            return HttpResponse(status=status.HTTP_200_OK)

        ok, delivery_type, delivery_fee, _, _ = evaluate_vendor_serviceability(vendor, coords)
        if not ok:
            telegram.send_message(chat_id=str(chat_id), text="ارسال به این آدرس فعال نیست.")
            return HttpResponse(status=status.HTTP_200_OK)

        products = Product.objects.filter(
            vendor=vendor, is_active=True, is_available=True, is_available_today=True
        ).order_by("sort_order", "id")

        tg_user.state = {
            "address_id": address.id,
            "vendor_id": vendor.id,
            "delivery_type": delivery_type,
            "delivery_fee": delivery_fee or 0,
            "cart": [],
            "coords": coords,
        }
        tg_user.save(update_fields=["state"])

        telegram.send_message(
            chat_id=str(chat_id),
            text=f"آشپزخانه انتخاب شد: {vendor.name}\nروش ارسال: {'پس‌کرایه' if delivery_type == 'OUT_OF_ZONE_SNAPP' else 'پیک داخلی'}",
            reply_markup=telegram.build_menu_keyboard(products),
        )
        return HttpResponse(status=status.HTTP_200_OK)

    if data.startswith("product:"):
        product_id = data.split(":")[1]
        product = Product.objects.filter(id=product_id, is_active=True, is_available=True, is_available_today=True).first()
        if not product:
            telegram.send_message(chat_id=str(chat_id), text="این آیتم در دسترس نیست.")
            return HttpResponse(status=status.HTTP_200_OK)

        state = tg_user.state or {}
        if not state.get("cart"):
            state["cart"] = []
        if state.get("vendor_id") and str(state["vendor_id"]) != str(product.vendor_id):
            telegram.send_message(chat_id=str(chat_id), text="آدرس یا فروشنده انتخاب شده با این آیتم سازگار نیست.")
            return HttpResponse(status=status.HTTP_200_OK)
        state["cart"].append({"product_id": product.id, "quantity": 1})
        tg_user.state = state
        tg_user.save(update_fields=["state"])

        telegram.send_message(
            chat_id=str(chat_id),
            text=f"{product.name_fa} به سبد خرید اضافه شد.",
            reply_markup=telegram.build_menu_keyboard(Product.objects.filter(
                vendor=product.vendor, is_active=True, is_available=True, is_available_today=True
            ).order_by("sort_order", "id")),
        )
        return HttpResponse(status=status.HTTP_200_OK)

    if data == "cart:review":
        state = tg_user.state or {}
        cart = state.get("cart") or []
        if not cart:
            telegram.send_message(chat_id=str(chat_id), text="سبد خرید خالی است.")
            return HttpResponse(status=status.HTTP_200_OK)
        product_ids = [item.get("product_id") for item in cart]
        products = Product.objects.filter(id__in=product_ids)
        lines = []
        total = state.get("delivery_fee") or 0
        for item in cart:
            prod = next((p for p in products if str(p.id) == str(item.get("product_id"))), None)
            if not prod:
                continue
            qty = int(item.get("quantity") or 1)
            line = prod.base_price * qty
            total += line
            lines.append(f"{prod.name_fa} × {qty} = {line:,}")
        lines.append(f"هزینه ارسال: {state.get('delivery_fee') or 0:,}")
        lines.append(f"جمع کل: {total:,}")
        lines.append(f"روش ارسال: {'پس‌کرایه' if state.get('delivery_type') == 'OUT_OF_ZONE_SNAPP' else 'پیک داخلی'}")
        telegram.send_message(
            chat_id=str(chat_id),
            text="\n".join(lines),
            reply_markup={"inline_keyboard": [[{"text": "ثبت و پرداخت 💳", "callback_data": "cart:checkout"}]]},
        )
        return HttpResponse(status=status.HTTP_200_OK)

    if data == "cart:checkout":
        state = tg_user.state or {}
        cart = state.get("cart") or []
        address_id = state.get("address_id")
        vendor_id = state.get("vendor_id")
        delivery_type = state.get("delivery_type")
        if not cart or not address_id or not vendor_id:
            telegram.send_message(chat_id=str(chat_id), text="اطلاعات سفارش کامل نیست.")
            return HttpResponse(status=status.HTTP_200_OK)
        address = Address.objects.filter(id=address_id, user=user).first()
        vendor = Vendor.objects.filter(id=vendor_id).first()
        if not address or not vendor:
            telegram.send_message(chat_id=str(chat_id), text="آدرس یا فروشنده نامعتبر است.")
            return HttpResponse(status=status.HTTP_200_OK)

        cart_products = Product.objects.filter(id__in=[item.get("product_id") for item in cart])
        items_payload = []
        subtotal = 0
        for item in cart:
            prod = next((p for p in cart_products if str(p.id) == str(item.get("product_id"))), None)
            if not prod:
                continue
            qty = int(item.get("quantity") or 1)
            items_payload.append({"product": prod.id, "quantity": qty})
            subtotal += prod.base_price * qty

        order, payment_url, error = _place_order_from_state(tg_user)
        if error:
            telegram.send_message(chat_id=str(chat_id), text=error)
            return HttpResponse(status=status.HTTP_200_OK)

        summary = f"سفارش شما ثبت شد. کد: {order.short_code}\nمبلغ: {order.total_amount:,}"
        reply_markup = None
        if payment_url:
            summary += f"\nبرای تکمیل سفارش پرداخت کنید."
            reply_markup = {"inline_keyboard": [[{"text": "پرداخت سفارش 💳", "url": payment_url}]]}
        telegram.send_message(chat_id=str(chat_id), text=summary, reply_markup=reply_markup)
        tg_user.state = {"cart": []}
        tg_user.save(update_fields=["state"])
        return HttpResponse(status=status.HTTP_200_OK)

    telegram.send_message(chat_id=str(chat_id), text="دستور ناشناخته است.")
    return HttpResponse(status=status.HTTP_200_OK)


def _build_fake_request(user):
    factory = APIRequestFactory()
    drf_request = factory.post("/orders/orders/")
    drf_request.user = user
    return Request(drf_request)


def _place_order_from_state(tg_user: TelegramUser):
    state = tg_user.state or {}
    user = tg_user.user

    cart = state.get("cart") or []
    address_id = state.get("address_id")
    vendor_id = state.get("vendor_id")
    coords = state.get("coords")
    if not cart:
        return None, None, "سبد خرید خالی است."
    if not address_id or not vendor_id:
        return None, None, "آدرس یا فروشنده انتخاب نشده است."

    address = Address.objects.filter(id=address_id, user=user).first()
    vendor = Vendor.objects.filter(id=vendor_id, is_active=True, is_visible=True).first()
    if not address or not vendor:
        return None, None, "آدرس یا فروشنده معتبر نیست."

    if coords is None and address.latitude and address.longitude:
        coords = {"latitude": float(address.latitude), "longitude": float(address.longitude)}

    is_serviceable, delivery_type, delivery_fee, _, _ = evaluate_vendor_serviceability(vendor, coords)
    if not is_serviceable or not delivery_type:
        return None, None, "در حال حاضر امکان سرویس‌دهی به این آدرس وجود ندارد."

    if state.get("delivery_type") and state.get("delivery_type") != delivery_type:
        return None, None, "روش ارسال تغییر کرده است. لطفاً دوباره آدرس را انتخاب کنید."

    product_ids = [item.get("product_id") for item in cart if item.get("product_id")]
    products = Product.objects.filter(id__in=product_ids, vendor=vendor, is_active=True, is_available=True, is_available_today=True)
    items_payload = []
    for item in cart:
        prod = next((p for p in products if str(p.id) == str(item.get("product_id"))), None)
        if not prod:
            continue
        qty = int(item.get("quantity") or 1)
        items_payload.append({"product": prod.id, "quantity": qty})

    if not items_payload:
        return None, None, "هیچ آیتم فعالی در سبد شما نیست."

    payload = {
        "vendor": vendor.id,
        "delivery_address": address.id,
        "items": items_payload,
        "customer_phone": user.phone,
        "accept_terms": True,
        "customer_location": coords,
        "source": "TELEGRAM",
    }

    serializer = OrderCreateSerializer(data=payload, context={"request": _build_fake_request(user)})
    if not serializer.is_valid():
        return None, None, "خطا در ثبت سفارش."

    order = serializer.save()
    OrderStatusHistory.objects.create(
        order=order,
        from_status="",
        to_status=order.status,
        changed_by_type="CUSTOMER",
        changed_by_user=user,
    )
    notify_order_created(order)

    payment = payments.create_payment(order)
    payment_url = None
    if payment:
        payment_url = payment.get("payment_url") or payment.get("paymentUrl") or payment.get("url")
        if payment_url:
            meta = order.meta or {}
            meta["payment"] = payment
            order.meta = meta
            order.save(update_fields=["meta"])

    return order, payment_url, None


@csrf_exempt
@api_view(["POST", "GET"])
def payment_callback(request):
    redirect_url = _payment_return_url()
    verification = payments.verify_payment(request)
    if not verification:
        payload_source = {}
        if hasattr(request, "data"):
            payload_source = request.data or {}
        payload_source = payload_source or getattr(request, "POST", {}) or getattr(request, "GET", {})
        track_id = payload_source.get("trackId") or payload_source.get("track_id")
        failure_payload = {
            "status": "verification_failed",
            "order_status": "FAILED",
            "payment_status": "FAILED",
            "order_id": "",
            "order_code": "",
            "track_id": track_id,
            "ref_number": "",
            "result": None,
            "message": "",
        }
        return _redirect_or_json(request, failure_payload, status_code=status.HTTP_400_BAD_REQUEST, redirect_url=redirect_url)

    order_id = verification.get("order_id")
    payment_status = verification.get("status")
    from orders.models import Order  # local import to avoid circular
    order = None
    if order_id:
        order = Order.objects.filter(meta__payment__order_id=str(order_id)).first()
        if not order:
            order = Order.objects.filter(id=str(order_id)).first()
        if not order:
            # Fall back to comparing short codes derived from the UUID
            order = next((o for o in Order.objects.all() if getattr(o, "short_code", "") == str(order_id)), None)
    if not order:
        failure_payload = {
            "status": "order_not_found",
            "order_status": "FAILED",
            "payment_status": verification.get("status") or "FAILED",
            "order_id": str(order_id) if order_id else "",
            "order_code": str(order_id) if order_id else "",
            "track_id": verification.get("track_id"),
            "ref_number": verification.get("ref_number"),
            "result": verification.get("result"),
            "message": verification.get("message"),
        }
        return _redirect_or_json(request, failure_payload, status_code=status.HTTP_404_NOT_FOUND, redirect_url=redirect_url)

    previous_status = order.status
    previous_payment_status = order.payment_status
    payment_verified_now = payment_status == "PAID" and previous_payment_status != "PAID"
    if payment_status == "PAID":
        order.payment_status = "PAID"
        if order.status in {"PENDING_PAYMENT", "FAILED"}:
            order.status = "CONFIRMED"
    else:
        # Only downgrade if payment was not previously captured
        if order.payment_status != "PAID":
            order.payment_status = "FAILED"
            if order.status == "PENDING_PAYMENT":
                order.status = "FAILED"
    if order.payment_status != previous_payment_status or order.status != previous_status:
        order.save(update_fields=["payment_status", "status"])

    if previous_status != order.status:
        from orders.models import OrderStatusHistory
        from orders.services import handle_order_status_change

        OrderStatusHistory.objects.create(
            order=order,
            from_status=previous_status,
            to_status=order.status,
            changed_by_type="SYSTEM",
        )
        handle_order_status_change(order)

    if payment_verified_now:
        notify_payment_verified(order)

    response_payload = {
        "status": "ok",
        "order_status": order.status,
        "payment_status": order.payment_status,
        "order_id": str(order.id),
        "order_code": getattr(order, "short_code", ""),
        "track_id": verification.get("track_id"),
        "ref_number": verification.get("ref_number"),
        "result": verification.get("result"),
        "message": verification.get("message"),
    }
    return _redirect_or_json(request, response_payload, redirect_url=redirect_url)
