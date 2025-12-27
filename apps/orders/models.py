import uuid
from django.db import models
from django.utils import timezone


class Order(models.Model):
    """
    سفارش. برای MVP: یک سفارش = یک Vendor.
    منطق قیمت در این مدل قابل لاگ‌برداری است و برای داشبورد خوب است.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="orders")
    vendor = models.ForeignKey("vendors.Vendor", on_delete=models.PROTECT, related_name="orders")

    # کانال ثبت سفارش
    source = models.CharField(
        max_length=20,
        choices=[("WEB", "WEB"), ("TELEGRAM", "TELEGRAM"), ("ADMIN", "ADMIN")],
        default="WEB",
        db_index=True,
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("DRAFT", "DRAFT"),
            ("PLACED", "PLACED"),
            ("CONFIRMED", "CONFIRMED"),
            ("PREPARING", "PREPARING"),
            ("READY", "READY"),
            ("OUT_FOR_DELIVERY", "OUT_FOR_DELIVERY"),
            ("DELIVERED", "DELIVERED"),
            ("CANCELLED", "CANCELLED"),
            ("FAILED", "FAILED"),
        ],
        default="PLACED",
        db_index=True,
    )

    # آدرس مقصد (از addresses)
    delivery_address = models.ForeignKey(
        "addresses.Address",
        on_delete=models.PROTECT,
        related_name="orders",
    )

    # یادداشت‌ها
    customer_note = models.CharField(max_length=400, blank=True, default="")
    admin_note = models.TextField(blank=True, default="")

    # قیمت‌ها (واحد پول پروژه‌ات: ترجیحاً ریال/تومان یکپارچه)
    subtotal_amount = models.BigIntegerField(default=0)
    discount_amount = models.BigIntegerField(default=0)
    delivery_fee_amount = models.BigIntegerField(default=0)
    service_fee_amount = models.BigIntegerField(default=0)
    total_amount = models.BigIntegerField(default=0)

    currency = models.CharField(max_length=8, default="IRR")  # اگر تومان می‌زنی، یکپارچه کن.

    # پرداخت
    payment_status = models.CharField(
        max_length=20,
        choices=[("UNPAID", "UNPAID"), ("PAID", "PAID"), ("REFUNDED", "REFUNDED"), ("FAILED", "FAILED")],
        default="UNPAID",
        db_index=True,
    )
    payment_method = models.CharField(
        max_length=20,
        choices=[("ONLINE", "ONLINE"), ("COD", "COD")],  # COD برای پس‌کرایه/پرداخت در محل/اسنپ
        default="ONLINE",
        db_index=True,
    )

    # زمان‌ها
    placed_at = models.DateTimeField(default=timezone.now, db_index=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # برای observability / تحلیل
    meta = models.JSONField(null=True, blank=True)  # مثل utm, device, telegram_user_id, etc.

    class Meta:
        indexes = [
            models.Index(fields=["vendor", "status", "placed_at"]),
            models.Index(fields=["user", "placed_at"]),
            models.Index(fields=["source", "placed_at"]),
            models.Index(fields=["payment_status", "placed_at"]),
        ]

    def __str__(self):
        return f"{self.id} {self.status}"

    @property
    def short_code(self) -> str:
        """
        کد کوتاه برای مشتری.
        از بخشی از UUID تولید می‌شود و فقط شامل عدد است تا استفاده در پیامک/تلفن راحت باشد.
        """
        numeric = int(self.id.hex[:12], 16)
        return str(numeric % 10_000_000_000).zfill(10)


class OrderItem(models.Model):
    """
    اقلام سفارش. محصول از catalog می‌آید.
    """

    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="items")

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
    )

    # برای اینکه اگر اسم/قیمت محصول بعداً تغییر کرد، سفارش خراب نشود:
    product_title_snapshot = models.CharField(max_length=250)
    unit_price_snapshot = models.BigIntegerField()  # قیمت واحد در زمان سفارش

    quantity = models.PositiveIntegerField(default=1)

    # آپشن‌ها/سفارشی‌سازی‌ها: سس، سایز، بدون فلان، ...
    modifiers = models.JSONField(null=True, blank=True)

    line_subtotal = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["order", "created_at"]),
            models.Index(fields=["product"]),
        ]

    def __str__(self):
        return f"{self.order_id} x{self.quantity}"


class OrderDelivery(models.Model):
    """
    جزئیات تحویل.
    باید خارج از محدوده با اسنپ (پس‌کرایه) را پوشش دهد.
    """

    order = models.OneToOneField("orders.Order", on_delete=models.CASCADE, related_name="delivery")

    delivery_type = models.CharField(
        max_length=22,
        choices=[("IN_ZONE", "IN_ZONE"), ("OUT_OF_ZONE_SNAPP", "OUT_OF_ZONE_SNAPP")],
        default="IN_ZONE",
        db_index=True,
    )

    # اگر اسنپ باشد، معمولاً پس‌کرایه است (پرداخت با مشتری)
    is_cash_on_delivery = models.BooleanField(default=False)

    # اطلاعات سفیر/پیک (در MVP ممکن است خالی باشد)
    courier_name = models.CharField(max_length=120, blank=True, default="")
    courier_phone = models.CharField(max_length=32, blank=True, default="")

    tracking_code = models.CharField(max_length=80, blank=True, default="")
    tracking_url = models.URLField(blank=True, default="")

    # هزینه تخمینی/نهایی ارسال برای گزارش
    external_delivery_quote_amount = models.BigIntegerField(default=0)
    external_delivery_final_amount = models.BigIntegerField(default=0)

    # لاگ پاسخ سرویس بیرونی (بعداً)
    external_provider = models.CharField(max_length=30, blank=True, default="")  # e.g. SNAPP
    external_payload = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["delivery_type", "created_at"]),
            models.Index(fields=["external_provider"]),
        ]

    def __str__(self):
        return f"{self.order_id} {self.delivery_type}"


class OrderStatusHistory(models.Model):
    """
    تاریخچه تغییر وضعیت برای پیگیری سفارش.
    """

    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="status_history")

    from_status = models.CharField(max_length=20, blank=True, default="")
    to_status = models.CharField(max_length=20, db_index=True)

    changed_by_type = models.CharField(
        max_length=20,
        choices=[("SYSTEM", "SYSTEM"), ("CUSTOMER", "CUSTOMER"), ("VENDOR", "VENDOR"), ("ADMIN", "ADMIN")],
        default="SYSTEM",
        db_index=True,
    )
    changed_by_user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_status_changes",
    )

    reason = models.CharField(max_length=250, blank=True, default="")
    meta = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["order", "created_at"]),
            models.Index(fields=["to_status", "created_at"]),
        ]

    def __str__(self):
        return f"{self.order_id}: {self.from_status}->{self.to_status}"
