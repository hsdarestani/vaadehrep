from django.db import models
from django.utils import timezone


class Category(models.Model):
    """
    دسته‌بندی نمایش منو برای هر وندور.
    مثال: غذای اصلی، سالاد، نوشیدنی، ...
    """

    vendor = models.ForeignKey("vendors.Vendor", on_delete=models.CASCADE, related_name="categories")

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, blank=True, default="")

    description = models.CharField(max_length=240, blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("vendor", "name"),)
        indexes = [
            models.Index(fields=["vendor", "is_active", "sort_order"]),
            models.Index(fields=["vendor", "name"]),
        ]

    def __str__(self):
        return f"{self.vendor_id}:{self.name}"


class Product(models.Model):
    """
    محصول/آیتم منو.
    """

    vendor = models.ForeignKey("vendors.Vendor", on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey("catalog.Category", on_delete=models.SET_NULL, null=True, blank=True, related_name="products")

    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, blank=True, default="")

    short_description = models.CharField(max_length=240, blank=True, default="")
    description = models.TextField(blank=True, default="")

    # قیمت پایه (ریال/تومان مطابق کل پروژه؛ پیشنهاد: ریال در DB، نمایش تومان در UI)
    price_amount = models.BigIntegerField(default=0)

    # نمایش
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)  # موجود/ناموجود سریع

    # محدودیت‌ها
    min_qty = models.PositiveIntegerField(default=1)
    max_qty = models.PositiveIntegerField(default=50)

    # تغذیه/برند سلامتی (اختیاری برای MVP، مفید برای آینده)
    calories = models.PositiveIntegerField(null=True, blank=True)
    protein_g = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    carbs_g = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    fat_g = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("vendor", "name"),)
        indexes = [
            models.Index(fields=["vendor", "is_active", "sort_order"]),
            models.Index(fields=["vendor", "category", "is_active"]),
            models.Index(fields=["vendor", "name"]),
        ]

    def __str__(self):
        return f"{self.vendor_id}:{self.name}"


class ProductImage(models.Model):
    """
    تصویر محصول.
    - MVP: فقط url
    - Later: ذخیره فایل روی S3/MinIO + thumbnail
    """

    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField(max_length=500)
    alt_text = models.CharField(max_length=180, blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["product", "is_primary"]),
            models.Index(fields=["product", "sort_order"]),
        ]

    def __str__(self):
        return f"{self.product_id}:{self.image_url[:40]}"


class OptionGroup(models.Model):
    """
    گروه گزینه‌ها (Modifiers).
    مثال: «انتخاب سس»، «افزودنی‌ها»، «انتخاب سایز»
    """

    vendor = models.ForeignKey("vendors.Vendor", on_delete=models.CASCADE, related_name="option_groups")

    name = models.CharField(max_length=120)
    description = models.CharField(max_length=240, blank=True, default="")

    # قواعد انتخاب
    is_required = models.BooleanField(default=False)
    min_select = models.PositiveIntegerField(default=0)
    max_select = models.PositiveIntegerField(default=1)

    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("vendor", "name"),)
        indexes = [
            models.Index(fields=["vendor", "is_active", "sort_order"]),
            models.Index(fields=["vendor", "name"]),
        ]

    def __str__(self):
        return f"{self.vendor_id}:{self.name}"


class OptionItem(models.Model):
    """
    آیتم‌های داخل یک گروه گزینه.
    مثال: در گروه «انتخاب سس»: «تهران»، «شیراز»، ...
    """

    group = models.ForeignKey("catalog.OptionGroup", on_delete=models.CASCADE, related_name="items")

    name = models.CharField(max_length=120)
    description = models.CharField(max_length=240, blank=True, default="")

    # تغییر قیمت نسبت به قیمت پایه محصول (می‌تواند منفی هم باشد)
    price_delta_amount = models.BigIntegerField(default=0)

    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = (("group", "name"),)
        indexes = [
            models.Index(fields=["group", "is_active", "sort_order"]),
        ]

    def __str__(self):
        return f"{self.group_id}:{self.name}"


class ProductOptionGroup(models.Model):
    """
    اتصال محصول به گروه گزینه‌ها (Many-to-Many با قابلیت override قواعد).
    مثال: ساندویچ مرغ => گروه انتخاب سس (required, max=1)
    """

    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="product_option_groups")
    group = models.ForeignKey("catalog.OptionGroup", on_delete=models.CASCADE, related_name="product_links")

    # override (اگر null باشد از group استفاده می‌شود)
    is_required = models.BooleanField(null=True, blank=True)
    min_select = models.PositiveIntegerField(null=True, blank=True)
    max_select = models.PositiveIntegerField(null=True, blank=True)

    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = (("product", "group"),)
        indexes = [
            models.Index(fields=["product", "is_active", "sort_order"]),
        ]

    def __str__(self):
        return f"{self.product_id} -> {self.group_id}"


class ProductAvailability(models.Model):
    """
    زمان‌بندی موجود بودن محصول (اختیاری برای MVP).
    - MVP می‌تونی فعلا استفاده نکنی و فقط is_available داشته باشی.
    - Later: برای صبحانه/ناهار/شام یا روزهای خاص.
    """

    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="availability_rules")

    # 0=Monday ... 6=Sunday
    weekday = models.PositiveSmallIntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["product", "weekday", "is_active"]),
        ]

    def __str__(self):
        return f"{self.product_id}:{self.weekday} {self.start_time}-{self.end_time}"

