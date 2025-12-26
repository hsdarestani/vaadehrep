from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAdminUser

from notifications.models import (
    AdminRecipient,
    Notification,
    NotificationDelivery,
    NotificationTemplate,
)


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = [
            "id",
            "code",
            "title",
            "channel",
            "language",
            "body",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "event_type",
            "template",
            "order",
            "vendor",
            "user",
            "context",
            "recipient_type",
            "channel",
            "status",
            "priority",
            "scheduled_for",
            "created_at",
            "sent_at",
        ]
        read_only_fields = ["id", "created_at"]


class NotificationDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationDelivery
        fields = [
            "id",
            "notification",
            "to_telegram_chat_id",
            "to_phone_number",
            "to_email",
            "rendered_title",
            "rendered_body",
            "status",
            "attempt_no",
            "max_attempts",
            "provider",
            "endpoint",
            "external_request_log",
            "error_message",
            "created_at",
            "sent_at",
        ]
        read_only_fields = ["id", "created_at"]


class AdminRecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminRecipient
        fields = [
            "id",
            "name",
            "is_active",
            "telegram_chat_id",
            "phone_number",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    queryset = NotificationTemplate.objects.all().order_by("code")
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAdminUser]


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by("-created_at")
    serializer_class = NotificationSerializer
    permission_classes = [IsAdminUser]


class NotificationDeliveryViewSet(viewsets.ModelViewSet):
    queryset = NotificationDelivery.objects.all().order_by("-created_at")
    serializer_class = NotificationDeliverySerializer
    permission_classes = [IsAdminUser]


class AdminRecipientViewSet(viewsets.ModelViewSet):
    queryset = AdminRecipient.objects.all().order_by("name")
    serializer_class = AdminRecipientSerializer
    permission_classes = [IsAdminUser]
