from django.contrib import admin
from .models import NotificationTemplate, Notification, NotificationDelivery, AdminRecipient


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ("code", "channel", "language", "is_active", "created_at")
    list_filter = ("channel", "language", "is_active")
    search_fields = ("code", "title", "body")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "event_type",
        "channel",
        "recipient_type",
        "status",
        "priority",
        "scheduled_for",
        "order",
        "vendor",
        "user",
        "created_at",
        "sent_at",
    )
    list_filter = ("channel", "recipient_type", "status", "created_at")
    search_fields = ("event_type", "id")


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "notification",
        "status",
        "attempt_no",
        "provider",
        "endpoint",
        "to_phone_number",
        "to_telegram_chat_id",
        "created_at",
        "sent_at",
    )
    list_filter = ("status", "provider", "created_at")
    search_fields = ("id", "to_phone_number", "to_telegram_chat_id", "error_message")


@admin.register(AdminRecipient)
class AdminRecipientAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "telegram_chat_id", "phone_number", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "phone_number", "telegram_chat_id")

