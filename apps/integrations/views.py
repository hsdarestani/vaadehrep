import logging
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAdminUser

from accounts.models import TelegramUser, User
from integrations.models import (
    ExternalRequestLog,
    IntegrationEndpoint,
    IntegrationProvider,
    ProviderHealthCheck,
    VendorIntegrationConfig,
)
from integrations.services import payments, telegram

logger = logging.getLogger(__name__)


def _normalize_phone(raw: str) -> str:
    if not raw:
        return ""
    p = str(raw).strip()
    return "".join(ch for ch in p if ch.isdigit())


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

    if not chat_id:
        return HttpResponse(status=status.HTTP_200_OK)

    if text.startswith("/start"):
        telegram.send_message(
            chat_id=str(chat_id),
            text="سلام! لطفا شماره موبایل خود را وارد کنید یا دکمه اشتراک‌گذاری شماره را بزنید.",
            reply_markup={"keyboard": [[{"text": "ارسال شماره", "request_contact": True}]], "resize_keyboard": True},
        )
        return HttpResponse(status=status.HTTP_200_OK)

    phone = _normalize_phone(contact.get("phone_number") if contact else text.strip())
    user = User.objects.filter(phone=phone).first()
    if not user:
        telegram.send_message(chat_id=str(chat_id), text="کاربری با این شماره پیدا نشد.")
        return HttpResponse(status=status.HTTP_200_OK)

    TelegramUser.objects.update_or_create(
        telegram_user_id=chat_id,
        defaults={
            "user": user,
            "username": chat.get("username", ""),
            "first_name": chat.get("first_name", ""),
            "last_name": chat.get("last_name", ""),
            "language_code": chat.get("language_code", ""),
            "is_bot": chat.get("is_bot", False),
        },
    )
    reply_markup = {
        "keyboard": [[{"text": "منو"}], [{"text": "سفارش‌های من"}]],
        "resize_keyboard": True,
    }
    telegram.send_message(chat_id=str(chat_id), text="حساب شما لینک شد.", reply_markup=reply_markup)
    return HttpResponse(status=status.HTTP_200_OK)


def _handle_telegram_callback(callback_query: dict):
    data = callback_query.get("data") or ""
    message = callback_query.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if not chat_id or not data.startswith("order:"):
        return HttpResponse(status=status.HTTP_200_OK)

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


@csrf_exempt
@api_view(["POST", "GET"])
def payment_callback(request):
    verification = payments.verify_payment(request)
    if not verification:
        return JsonResponse({"status": "verification_failed"}, status=status.HTTP_400_BAD_REQUEST)

    order_id = verification.get("order_id")
    payment_status = verification.get("status")
    from orders.models import Order  # local import to avoid circular
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        try:
            order = Order.objects.get(meta__payment__order_id=str(order_id))
        except Order.DoesNotExist:
            try:
                order = Order.objects.get(id__startswith=str(order_id))
            except Order.DoesNotExist:
                return JsonResponse({"status": "order_not_found"}, status=status.HTTP_404_NOT_FOUND)

    previous_status = order.status
    if payment_status == "PAID":
        order.payment_status = "PAID"
        order.status = "CONFIRMED"
    else:
        order.payment_status = "FAILED"
        order.status = "FAILED"
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

    redirect_url = getattr(settings, "PAYMENT_RETURN_URL", "")
    if not redirect_url:
        site_base = getattr(settings, "FRONTEND_BASE_URL", "") or getattr(settings, "SITE_BASE_URL", "")
        if site_base:
            redirect_url = f"{site_base.rstrip('/')}/payment-result"

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
    if request.method == "GET" and redirect_url:
        query_params = {
            "order_id": response_payload["order_id"],
            "order_code": response_payload["order_code"],
            "payment_status": response_payload["payment_status"],
            "order_status": response_payload["order_status"],
            "track_id": response_payload["track_id"],
            "ref_number": response_payload["ref_number"],
            "result": response_payload["result"],
            "message": response_payload["message"],
        }
        query_string = urlencode({k: v for k, v in query_params.items() if v not in [None, ""]})
        redirect_target = f"{redirect_url}?{query_string}" if query_string else redirect_url
        return redirect(redirect_target)

    return JsonResponse(response_payload)
