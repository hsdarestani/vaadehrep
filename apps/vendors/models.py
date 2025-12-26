from django.db import models
from django.utils import timezone


class Vendor(models.Model):
    """
    رستوران/کافه/آشپزخانه‌ای که سفارش را fulfil می‌کند.
    در MVP: هر سفارش به یک Vendor وصل است.
    """

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)

    is_active = models.BooleanField(default=True)
    is_accepting_orders = models.BooleanField(default=True)

    # اطلاعات تماس/مسئول شیفت
    phone_number = models.CharField(max_length=32, blank=True, default="")
    telegram_chat_id = models.CharField(max_length=64, blank=True, default="")  # برای اعلان‌های vendor

    # برندینگ/نمایش
    logo_url = models.URLField(blank=True, default="")
    description = models.TextField(blank=True, default="")

    # تنظیمات عملیاتی
    prep_time_minutes_default = models.PositiveSmallIntegerField(default=20)
    min_order_amount = models.PositiveIntegerField(default=0)  # ریال/تومان بر اساس واحد پروژه
    max_active_orders = models.PositiveSmallIntegerField(default=0)  # 0 یعنی محدودیت ندارد

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["is_active", "is_accepting_orders"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.name


class VendorLocation(models.Model):
    """
    موقعیت و محدوده خدمات‌دهی Vendor
    برای MVP: یک location فعال کافیست.
    """

    vendor = models.ForeignKey("vendors.Vendor", on_delete=models.CASCADE, related_name="locations")

    title = models.CharField(max_length=120, default="main")  # مثلا "شعبه اصلی"
    is_active = models.BooleanField(default=True)

    address_text = models.CharField(max_length=500, blank=True, default="")

    # مختصات (برای محاسبه فاصله/زون، بعداً)
    lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    # شعاع خدمات‌دهی (متر) برای داخل محدوده
    service_radius_m = models.PositiveIntegerField(default=0)  # 0 یعنی غیرفعال/نامشخص

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["vendor", "is_active"]),
        ]

    def __str__(self):
        return f"{self.vendor_id}:{self.title}"


class VendorHours(models.Model):
    """
    ساعت کاری. برای MVP ساده: روز هفته + بازه.
    """

    vendor = models.ForeignKey("vendors.Vendor", on_delete=models.CASCADE, related_name="hours")
    weekday = models.PositiveSmallIntegerField(
        choices=[(0, "Mon"), (1, "Tue"), (2, "Wed"), (3, "Thu"), (4, "Fri"), (5, "Sat"), (6, "Sun")],
        db_index=True,
    )

    opens_at = models.TimeField()
    closes_at = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["vendor", "weekday", "is_active"]),
        ]

    def __str__(self):
        return f"{self.vendor_id} {self.weekday} {self.opens_at}-{self.closes_at}"


class VendorStaff(models.Model):
    """
    کاربران داخلی که به یک Vendor متصل‌اند (برای داشبورد vendor در آینده).
    """

    vendor = models.ForeignKey("vendors.Vendor", on_delete=models.CASCADE, related_name="staff")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="vendor_roles")

    role = models.CharField(
        max_length=20,
        choices=[("OWNER", "OWNER"), ("MANAGER", "MANAGER"), ("OPERATOR", "OPERATOR")],
        default="OPERATOR",
        db_index=True,
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("vendor", "user")]
        indexes = [
            models.Index(fields=["vendor", "role", "is_active"]),
        ]

    def __str__(self):
        return f"{self.vendor_id}:{self.user_id}:{self.role}"

