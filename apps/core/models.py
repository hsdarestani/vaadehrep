import uuid
from django.db import models
from django.utils import timezone


# -------------------------
# Base abstract models
# -------------------------

class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save(update_fields=["is_deleted", "deleted_at"])


class ActiveModel(models.Model):
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True


# -------------------------
# Core concrete models
# -------------------------

class AppSetting(TimeStampedModel):
    """
    تنظیمات Key-Value برای کنترل رفتار سیستم بدون دیپلوی مجدد.
    مثال‌ها:
    - ordering_open: true/false
    - max_active_orders_per_user: 3
    - support_phone: "09..."
    - default_delivery_fee_in_zone: 80000
    - snapp_out_of_zone_enabled: true
    """

    VALUE_TYPE_STR = "str"
    VALUE_TYPE_INT = "int"
    VALUE_TYPE_BOOL = "bool"
    VALUE_TYPE_JSON = "json"

    VALUE_TYPE_CHOICES = (
        (VALUE_TYPE_STR, "String"),
        (VALUE_TYPE_INT, "Integer"),
        (VALUE_TYPE_BOOL, "Boolean"),
        (VALUE_TYPE_JSON, "JSON"),
    )

    key = models.CharField(max_length=120, unique=True)
    value_type = models.CharField(max_length=10, choices=VALUE_TYPE_CHOICES, default=VALUE_TYPE_STR)

    value_str = models.TextField(blank=True, default="")
    value_int = models.BigIntegerField(null=True, blank=True)
    value_bool = models.BooleanField(null=True, blank=True)
    value_json = models.JSONField(null=True, blank=True)

    description = models.CharField(max_length=240, blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["key"]),
            models.Index(fields=["value_type"]),
        ]

    def __str__(self):
        return f"{self.key}"

    def get_value(self):
        if self.value_type == self.VALUE_TYPE_STR:
            return self.value_str
        if self.value_type == self.VALUE_TYPE_INT:
            return self.value_int
        if self.value_type == self.VALUE_TYPE_BOOL:
            return self.value_bool
        if self.value_type == self.VALUE_TYPE_JSON:
            return self.value_json
        return None


class FeatureFlag(TimeStampedModel, ActiveModel):
    """
    فعال/غیرفعال کردن قابلیت‌ها برای MVP و rollout تدریجی.
    مثال‌ها:
    - telegram_ordering_enabled
    - sms_notifications_enabled
    - snapp_out_of_zone_enabled
    - admin_manual_edit_orders_enabled
    """

    code = models.CharField(max_length=120, unique=True)
    description = models.CharField(max_length=240, blank=True, default="")

    # اگر خواستی بعداً شرط‌گذاری کنی (برای درصدی از کاربران یا یک vendor خاص)
    rules = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["code", "is_active"]),
        ]

    def __str__(self):
        return f"{self.code}"


class MediaAsset(UUIDModel, TimeStampedModel, ActiveModel):
    """
    نگهداری مرجع فایل/تصویر.
    - MVP: فقط URL (مثلاً روی CDN/S3/Cloudflare R2 یا حتی static)
    - Later: آپلود مستقیم + مدیریت نسخه/thumbnail

    استفاده‌ها:
    - تصویر محصول، بنر لندینگ، تصویر وندور، فایل‌های خروجی ادمین
    """

    ASSET_IMAGE = "image"
    ASSET_FILE = "file"
    ASSET_CHOICES = (
        (ASSET_IMAGE, "Image"),
        (ASSET_FILE, "File"),
    )

    asset_type = models.CharField(max_length=20, choices=ASSET_CHOICES, default=ASSET_IMAGE)
    title = models.CharField(max_length=160, blank=True, default="")
    url = models.URLField(max_length=600)

    # متادیتا برای داشبورد/آنالیتیکس
    meta = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["asset_type", "is_active", "created_at"]),
        ]

    def __str__(self):
        return f"{self.asset_type}:{self.title or str(self.id)}"

