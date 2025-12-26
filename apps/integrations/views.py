import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
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
    message = update.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = message.get("text", "")

    if not chat_id:
        return HttpResponse(status=status.HTTP_200_OK)

    if text.startswith("/start"):
        telegram.send_message(chat_id=str(chat_id), text="سلام! لطفا شماره موبایل خود را وارد کنید.")
        return HttpResponse(status=status.HTTP_200_OK)

    phone = text.strip()
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


@csrf_exempt
@api_view(["POST"])
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

    return JsonResponse({"status": "ok", "order_status": order.status})
