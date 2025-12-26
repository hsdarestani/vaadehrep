from django.db import models
from django.utils import timezone


class EventType(models.Model):
    """
    دیکشنری نوع رویدادها (اختیاری ولی بسیار تمیز برای تحلیل).
    مثال‌ها:
    - user.login
    - user.logout
    - order.created
    - order.accepted
    - order.rejected
    - order.delivered
    - notification.sent
    - notification.failed
    """

    code = models.CharField(max_length=120, unique=True)
    description = models.CharField(max_length=240, blank=True, default="")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["code", "is_active"]),
        ]

    def __str__(self):
        return self.code


class Event(models.Model):
    """
    جدول مرکزی رویدادها.
    هر اتفاق مهم در سیستم = یک رکورد اینجا.
    """

    event_type = models.ForeignKey(
        "events.EventType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )

    # actor: چه کسی این رویداد را ایجاد کرده؟
    actor_user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )

    actor_type = models.CharField(
        max_length=32,
        default="SYSTEM",
        choices=[
            ("USER", "USER"),
            ("ADMIN", "ADMIN"),
            ("VENDOR", "VENDOR"),
            ("SYSTEM", "SYSTEM"),
            ("TELEGRAM", "TELEGRAM"),
        ],
    )

    # ارتباط با دامنه بیزنس (اختیاری)
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )

    # کانال یا منبع رویداد
    source = models.CharField(
        max_length=32,
        default="BACKEND",
        choices=[
            ("WEB", "WEB"),
            ("MOBILE", "MOBILE"),
            ("TELEGRAM", "TELEGRAM"),
            ("ADMIN", "ADMIN"),
            ("CRON", "CRON"),
            ("BACKEND", "BACKEND"),
        ],
    )

    # شدت/اهمیت (برای مانیتورینگ)
    level = models.CharField(
        max_length=16,
        default="INFO",
        choices=[
            ("DEBUG", "DEBUG"),
            ("INFO", "INFO"),
            ("WARNING", "WARNING"),
            ("ERROR", "ERROR"),
            ("CRITICAL", "CRITICAL"),
        ],
    )

    # داده آزاد برای تحلیل (بسیار مهم)
    payload = models.JSONField(null=True, blank=True)

    # متادیتای فنی
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=240, blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["actor_type", "created_at"]),
            models.Index(fields=["source", "created_at"]),
            models.Index(fields=["level", "created_at"]),
            models.Index(fields=["order"]),
            models.Index(fields=["vendor"]),
        ]

    def __str__(self):
        return f"{self.event_type_id} @ {self.created_at}"

