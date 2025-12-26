from django.db import models
from django.utils import timezone


class NotificationTemplate(models.Model):
    """
    قالب پیام‌های سیستم برای کانال‌های مختلف.
    body می‌تواند متن ساده یا template string باشد (مثلاً با {{order_id}}).
    """

    code = models.CharField(max_length=80, unique=True)  # e.g. ORDER_CREATED_CUSTOMER, ORDER_NEW_VENDOR, ...
    title = models.CharField(max_length=160, blank=True, default="")

    channel = models.CharField(
        max_length=16,
        choices=[
            ("TELEGRAM", "TELEGRAM"),
            ("SMS", "SMS"),
            ("EMAIL", "EMAIL"),
            ("PUSH", "PUSH"),
        ],
        db_index=True,
    )

    language = models.CharField(
        max_length=8,
        default="fa",
        choices=[("fa", "fa"), ("en", "en")],
        db_index=True,
    )

    body = models.TextField()  # template string
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["channel", "is_active"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return f"{self.code} ({self.channel}/{self.language})"


class Notification(models.Model):
    """
    یک اعلان منطقی که ممکن است چندین Attempt داشته باشد.
    مثال: اعلان ORDER_CREATED به مشتری با تلگرام + پیامک (دو delivery)
    """

    event_type = models.CharField(max_length=80, db_index=True)  # e.g. ORDER_CREATED, ORDER_PAID, ORDER_CANCELLED
    template = models.ForeignKey(
        "notifications.NotificationTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )

    # ارتباط با دامنه بیزنس (اختیاری ولی برای داشبورد/فیلتر مهم)
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )

    # داده‌های لازم برای رندر کردن قالب
    context = models.JSONField(null=True, blank=True)

    # مقصد از نظر بیزنسی (نه فنی)
    recipient_type = models.CharField(
        max_length=16,
        choices=[
            ("CUSTOMER", "CUSTOMER"),
            ("VENDOR", "VENDOR"),
            ("ADMIN", "ADMIN"),
            ("SYSTEM", "SYSTEM"),
        ],
        db_index=True,
    )

    # کانال هدف این Notification (در MVP بهتره هر Notification یک channel داشته باشه)
    channel = models.CharField(
        max_length=16,
        choices=[
            ("TELEGRAM", "TELEGRAM"),
            ("SMS", "SMS"),
            ("EMAIL", "EMAIL"),
            ("PUSH", "PUSH"),
        ],
        db_index=True,
    )

    status = models.CharField(
        max_length=16,
        default="PENDING",
        choices=[
            ("PENDING", "PENDING"),
            ("SENDING", "SENDING"),
            ("SENT", "SENT"),
            ("FAILED", "FAILED"),
            ("CANCELLED", "CANCELLED"),
        ],
        db_index=True,
    )

    priority = models.PositiveSmallIntegerField(default=5, db_index=True)  # 1=high ... 9=low
    scheduled_for = models.DateTimeField(null=True, blank=True, db_index=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["channel", "status"]),
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["recipient_type", "created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type}/{self.channel} {self.status}"


class NotificationDelivery(models.Model):
    """
    هر بار تلاش برای ارسال یک Notification.
    برای retry، هر attempt یک رکورد جدید می‌گیرد.
    """

    notification = models.ForeignKey(
        "notifications.Notification",
        on_delete=models.CASCADE,
        related_name="deliveries",
    )

    # مقصد فنی
    to_telegram_chat_id = models.CharField(max_length=64, blank=True, default="")
    to_phone_number = models.CharField(max_length=32, blank=True, default="")
    to_email = models.EmailField(blank=True, default="")

    # payload نهایی آماده ارسال (بعد از رندر template)
    rendered_title = models.CharField(max_length=160, blank=True, default="")
    rendered_body = models.TextField(blank=True, default="")

    # وضعیت ارسال
    status = models.CharField(
        max_length=16,
        default="PENDING",
        choices=[
            ("PENDING", "PENDING"),
            ("SENDING", "SENDING"),
            ("SENT", "SENT"),
            ("FAILED", "FAILED"),
        ],
        db_index=True,
    )

    attempt_no = models.PositiveSmallIntegerField(default=1)
    max_attempts = models.PositiveSmallIntegerField(default=3)

    provider = models.ForeignKey(
        "integrations.IntegrationProvider",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_deliveries",
    )
    endpoint = models.ForeignKey(
        "integrations.IntegrationEndpoint",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_deliveries",
    )

    external_request_log = models.ForeignKey(
        "integrations.ExternalRequestLog",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_deliveries",
    )

    error_message = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["provider", "status"]),
            models.Index(fields=["notification", "attempt_no"]),
        ]

    def __str__(self):
        return f"delivery#{self.id} {self.status} attempt={self.attempt_no}"


class AdminRecipient(models.Model):
    """
    گیرنده‌های ادمین (برای اعلان‌های سیستم).
    در MVP ساده: چند نفر admin که پیام تلگرام/پیامک می‌گیرند.
    """

    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    telegram_chat_id = models.CharField(max_length=64, blank=True, default="")
    phone_number = models.CharField(max_length=32, blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name

