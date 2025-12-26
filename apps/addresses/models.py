from django.db import models
from django.utils import timezone


class Address(models.Model):
    """
    آدرس‌های کاربر برای سفارش‌دهی و ارسال.
    - برای MVP: هر آدرس متعلق به یک User
    - default address با is_default
    - lat/lng برای تشخیص محدوده ارسال و محاسبه مسیر/هزینه
    """

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="addresses")

    title = models.CharField(max_length=60, blank=True, default="")  # مثلا: خانه، محل کار
    receiver_name = models.CharField(max_length=120, blank=True, default="")
    receiver_phone = models.CharField(max_length=20, blank=True, default="")

    province = models.CharField(max_length=80, blank=True, default="")
    city = models.CharField(max_length=80, blank=True, default="")
    district = models.CharField(max_length=120, blank=True, default="")  # منطقه/محله
    street = models.CharField(max_length=240, blank=True, default="")
    alley = models.CharField(max_length=240, blank=True, default="")
    building = models.CharField(max_length=120, blank=True, default="")  # ساختمان/برج
    plaque = models.CharField(max_length=30, blank=True, default="")
    unit = models.CharField(max_length=30, blank=True, default="")
    floor = models.CharField(max_length=30, blank=True, default="")

    postal_code = models.CharField(max_length=20, blank=True, default="")

    full_text = models.TextField(blank=True, default="")  # متن کامل آدرس برای UI و ارسال به پیک
    notes = models.CharField(max_length=240, blank=True, default="")  # مثلا: زنگ نزنید/نگهبانی

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_default"]),
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["city", "district"]),
        ]

    def __str__(self):
        t = self.title or "address"
        return f"{self.user_id}:{t}"


class DeliveryZone(models.Model):
    """
    محدوده‌های پوشش ارسال (برای MVP می‌تواند فقط برای ادمین باشد).
    - ایده MVP: چند «زون» تعریف می‌کنی (مثلاً مناطق 1/2/3/4/5/22 یا چند محله)
    - سفارش داخل زون => ارسال استاندارد
    - سفارش خارج زون => اجازه ارسال با اسنپ (پس‌کرایه) یا رد
    """

    name = models.CharField(max_length=120, unique=True)
    city = models.CharField(max_length=80, blank=True, default="")
    description = models.CharField(max_length=240, blank=True, default="")

    is_active = models.BooleanField(default=True)

    # برای MVP ساده: تعریف زون بر اساس لیست district یا regex (بدون GIS)
    # اگر later GIS خواستی: polygon/geojson اضافه می‌کنیم.
    districts_csv = models.TextField(blank=True, default="")  # مثال: "منطقه 1,منطقه 2,زعفرانیه,..."

    allow_out_of_zone = models.BooleanField(default=True)  # اجازه ارسال خارج محدوده؟
    out_of_zone_policy = models.CharField(
        max_length=32,
        default="SNAPP_COD",
        choices=[
            ("SNAPP_COD", "SNAPP_COD"),   # اسنپ با پس‌کرایه
            ("SNAPP_PREPAID", "SNAPP_PREPAID"),  # اسنپ با پیش‌پرداخت
            ("DISALLOW", "DISALLOW"),     # عدم امکان ارسال
        ],
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class AddressZoneMatch(models.Model):
    """
    نگاشت آدرس به زون (اختیاری، برای سرعت و تحلیل).
    - می‌تواند هنگام ذخیره آدرس یا قبل از ثبت سفارش محاسبه شود.
    """

    address = models.OneToOneField("addresses.Address", on_delete=models.CASCADE, related_name="zone_match")
    zone = models.ForeignKey("addresses.DeliveryZone", on_delete=models.SET_NULL, null=True, blank=True)
    matched_by = models.CharField(
        max_length=32,
        default="UNKNOWN",
        choices=[
            ("DISTRICT", "DISTRICT"),
            ("GEO", "GEO"),
            ("MANUAL", "MANUAL"),
            ("UNKNOWN", "UNKNOWN"),
        ],
    )
    matched_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.address_id} -> {self.zone_id}"

