from django.db import models
from django.utils import timezone


class IntegrationProvider(models.Model):
    """
    ارائه‌دهنده/سرویس بیرونی.
    نمونه: Telegram Bot API, Kavenegar, Ghasedak, Zibal, NextPay, Snapp (delivery), Webhook, ...
    """

    kind = models.CharField(
        max_length=32,
        choices=[
            ("TELEGRAM", "TELEGRAM"),
            ("SMS", "SMS"),
            ("PAYMENT", "PAYMENT"),
            ("DELIVERY", "DELIVERY"),
            ("WEBHOOK", "WEBHOOK"),
            ("ANALYTICS", "ANALYTICS"),
            ("OTHER", "OTHER"),
        ],
        db_index=True,
    )
    code = models.CharField(max_length=80, unique=True)  # e.g. telegram_main, sms_kavenegar, pay_zibal
    name = models.CharField(max_length=120)

    base_url = models.URLField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    # اگر از secret manager استفاده نمی‌کنی، حداقل «اسم کلیدهای env» را اینجا نگه دار
    # مثال payload:
    # {"env": {"api_key": "VAADH_SMS_API_KEY", "token": "VAADH_TG_BOT_TOKEN"}}
    credentials_ref = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["kind", "is_active"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return f"{self.kind}:{self.code}"


class IntegrationEndpoint(models.Model):
    """
    بعضی سرویس‌ها چند endpoint دارند (ارسال پیامک، وضعیت پیامک، ساخت لینک پرداخت، verify پرداخت...)
    """

    provider = models.ForeignKey(
        "integrations.IntegrationProvider",
        on_delete=models.CASCADE,
        related_name="endpoints",
    )
    code = models.CharField(max_length=80)  # e.g. send_sms, verify_payment, create_payment, send_message
    path = models.CharField(max_length=240, blank=True, default="")  # relative path or full
    method = models.CharField(
        max_length=10,
        default="POST",
        choices=[("GET", "GET"), ("POST", "POST"), ("PUT", "PUT"), ("PATCH", "PATCH"), ("DELETE", "DELETE")],
    )
    timeout_seconds = models.PositiveSmallIntegerField(default=15)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("provider", "code")]
        indexes = [
            models.Index(fields=["provider", "is_active"]),
        ]

    def __str__(self):
        return f"{self.provider.code}:{self.code}"


class VendorIntegrationConfig(models.Model):
    """
    اگر بعضی وندورها تنظیم خاص داشته باشند (مثلاً شماره پیامک متفاوت، webhook اختصاصی، سیاست ارسال متفاوت).
    در MVP ممکن است فقط چند فیلد پر شود.
    """

    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.CASCADE,
        related_name="integration_configs",
    )
    provider = models.ForeignKey(
        "integrations.IntegrationProvider",
        on_delete=models.CASCADE,
        related_name="vendor_configs",
    )

    # تنظیمات اختصاصی وندور برای این سرویس
    config = models.JSONField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("vendor", "provider")]
        indexes = [
            models.Index(fields=["vendor", "is_active"]),
            models.Index(fields=["provider", "is_active"]),
        ]

    def __str__(self):
        return f"{self.vendor_id}:{self.provider.code}"


class ExternalRequestLog(models.Model):
    """
    لاگ درخواست/پاسخ بیرونی برای observability و دیباگ.
    پیشنهاد: payloadها را کوتاه نگه دار؛ چیزهای حساس را ماسک کن (token/api_key).
    """

    provider = models.ForeignKey(
        "integrations.IntegrationProvider",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="request_logs",
    )
    endpoint = models.ForeignKey(
        "integrations.IntegrationEndpoint",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="request_logs",
    )

    # ارتباط با دامنه بیزنس (اختیاری)
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="external_logs",
    )
    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="external_logs",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="external_logs",
    )

    # برای همبستگی لاگ‌ها در یک جریان (trace)
    trace_id = models.CharField(max_length=64, blank=True, default="", db_index=True)

    request_url = models.CharField(max_length=500, blank=True, default="")
    request_method = models.CharField(max_length=10, blank=True, default="")
    request_headers = models.JSONField(null=True, blank=True)
    request_body = models.JSONField(null=True, blank=True)

    response_status = models.IntegerField(null=True, blank=True, db_index=True)
    response_headers = models.JSONField(null=True, blank=True)
    response_body = models.JSONField(null=True, blank=True)

    duration_ms = models.PositiveIntegerField(null=True, blank=True)

    outcome = models.CharField(
        max_length=16,
        default="UNKNOWN",
        choices=[("SUCCESS", "SUCCESS"), ("FAIL", "FAIL"), ("TIMEOUT", "TIMEOUT"), ("UNKNOWN", "UNKNOWN")],
        db_index=True,
    )

    error_message = models.CharField(max_length=500, blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["provider", "created_at"]),
            models.Index(fields=["outcome", "created_at"]),
            models.Index(fields=["response_status", "created_at"]),
            models.Index(fields=["trace_id", "created_at"]),
        ]

    def __str__(self):
        return f"{self.provider_id}/{self.endpoint_id} {self.response_status} {self.outcome}"


class ProviderHealthCheck(models.Model):
    """
    وضعیت سلامت سرویس‌ها (برای داشبورد و alert).
    می‌تواند توسط cron/celery beat هر N دقیقه پر شود.
    """

    provider = models.ForeignKey(
        "integrations.IntegrationProvider",
        on_delete=models.CASCADE,
        related_name="health_checks",
    )
    status = models.CharField(
        max_length=16,
        choices=[("UP", "UP"), ("DEGRADED", "DEGRADED"), ("DOWN", "DOWN")],
        db_index=True,
    )
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    details = models.JSONField(null=True, blank=True)

    checked_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["provider", "checked_at"]),
            models.Index(fields=["status", "checked_at"]),
        ]

    def __str__(self):
        return f"{self.provider.code} {self.status} @ {self.checked_at}"

