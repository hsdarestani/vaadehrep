from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("phone is required")
        phone = self.normalize_email(phone) if "@" in str(phone) else str(phone).strip()
        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if not password:
            raise ValueError("superuser password required")
        return self.create_user(phone, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    هویت اصلی مشتری/ادمین.
    - لاگین اصلی با phone
    - برای SPA از JWT استفاده می‌کنیم، نه Session
    """
    phone = models.CharField(max_length=20, unique=True, db_index=True)
    full_name = models.CharField(max_length=120, blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # ویژگی‌های اختیاری برای آینده:
    default_city = models.CharField(max_length=80, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now)
    last_login_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.phone}"


class TelegramUser(models.Model):
    """
    اتصال حساب تلگرام به User.
    برای MVP: یک تلگرام = یک User
    """
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="telegram")
    telegram_user_id = models.BigIntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=80, blank=True, default="")
    first_name = models.CharField(max_length=80, blank=True, default="")
    last_name = models.CharField(max_length=80, blank=True, default="")
    language_code = models.CharField(max_length=20, blank=True, default="")
    is_bot = models.BooleanField(default=False)

    # برای کنترل امنیت/ریسک:
    is_blocked = models.BooleanField(default=False)
    state = models.JSONField(null=True, blank=True, default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"tg:{self.telegram_user_id} -> {self.user_id}"


class LoginOTP(models.Model):
    """
    OTP پیامکی برای ورود/ثبت‌نام.
    - code را هش می‌کنیم (نه plaintext)
    - rate limit و lockout با فیلدها کنترل می‌شود
    """
    PURPOSE_LOGIN = "LOGIN"
    PURPOSE_LINK_TG = "LINK_TG"
    PURPOSES = [(PURPOSE_LOGIN, "LOGIN"), (PURPOSE_LINK_TG, "LINK_TG")]

    phone = models.CharField(max_length=20, db_index=True)
    purpose = models.CharField(max_length=16, choices=PURPOSES, default=PURPOSE_LOGIN)

    code_hash = models.CharField(max_length=128)  # hash(code + salt)
    salt = models.CharField(max_length=32)

    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(db_index=True)

    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    is_used = models.BooleanField(default=False)

    # Observability / Anti-fraud:
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=240, blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["phone", "purpose", "expires_at"]),
        ]

    def __str__(self):
        return f"{self.phone} {self.purpose} used={self.is_used}"


class UserDevice(models.Model):
    """
    برای ردیابی دستگاه‌ها/سشن‌های refresh (برای SPA).
    refresh_token را هش‌شده نگه می‌داریم.
    """
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="devices")
    device_id = models.CharField(max_length=64, db_index=True)  # random uuid from client
    title = models.CharField(max_length=120, blank=True, default="")  # e.g. Chrome Windows
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=240, blank=True, default="")

    refresh_hash = models.CharField(max_length=128, blank=True, default="")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("user", "device_id")]

    def __str__(self):
        return f"{self.user_id}:{self.device_id} active={self.is_active}"
