import hashlib
import secrets
from django.contrib.auth import get_user_model
from rest_framework import serializers, status, viewsets
from rest_framework.permissions import IsAdminUser,AllowAny
from rest_framework.response import Response
import random
from django.utils import timezone
from datetime import timedelta
from accounts.models import LoginOTP, TelegramUser, UserDevice
from integrations.services import sms
from django.conf import settings

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "full_name",
            "is_active",
            "is_staff",
            "default_city",
            "notes",
            "created_at",
            "last_login_at",
            "password",
        ]
        read_only_fields = ["id", "created_at", "last_login_at", "is_staff"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class TelegramUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramUser
        fields = [
            "id",
            "user",
            "telegram_user_id",
            "username",
            "first_name",
            "last_name",
            "language_code",
            "is_bot",
            "is_blocked",
            "created_at",
            "last_seen_at",
        ]
        read_only_fields = ["id", "created_at"]


class LoginOTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginOTP
        fields = [
            "id",
            "phone",
            "purpose",
            "code_hash",
            "salt",
            "created_at",
            "expires_at",
            "attempts",
            "max_attempts",
            "is_used",
            "ip",
            "user_agent",
        ]
        read_only_fields = ["id", "created_at"]


class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = [
            "id",
            "user",
            "device_id",
            "title",
            "ip",
            "user_agent",
            "refresh_hash",
            "is_active",
            "created_at",
            "last_seen_at",
        ]
        read_only_fields = ["id", "created_at"]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-created_at")
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class TelegramUserViewSet(viewsets.ModelViewSet):
    queryset = TelegramUser.objects.all().order_by("-created_at")
    serializer_class = TelegramUserSerializer
    permission_classes = [IsAdminUser]


def _normalize_phone(raw: str) -> str:
    if not raw:
        return ""
    p = str(raw).strip()
    # ساده‌ترین نرمال‌سازی: فقط اعداد
    p = "".join(ch for ch in p if ch.isdigit())
    return p


def _make_otp_code(length: int = 6) -> str:
    # فقط عددی
    return "".join(secrets.choice("0123456789") for _ in range(length))


def _hash_code(code: str, salt: str) -> str:
    # sha256(code + ":" + salt)
    return hashlib.sha256(f"{code}:{salt}".encode("utf-8")).hexdigest()


class LoginOTPViewSet(viewsets.ModelViewSet):
    queryset = LoginOTP.objects.all().order_by("-created_at")
    serializer_class = LoginOTPSerializer

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsAdminUser()]

    def create(self, request, *args, **kwargs):
        # ورودی‌هایی که از فرانت قبول می‌کنیم
        phone = _normalize_phone(request.data.get("phone"))
        purpose = (request.data.get("purpose") or "LOGIN").strip().upper()

        if not phone:
            return Response({"ok": False, "error": "phone is required"}, status=status.HTTP_400_BAD_REQUEST)

        # TTL از تنظیمات یا پیش‌فرض
        ttl_seconds = int(getattr(settings, "LOGIN_OTP_TTL_SECONDS", 120))
        expires_at = timezone.now() + timedelta(seconds=ttl_seconds)

        # تولید کد و هش
        raw_code = _make_otp_code(length=6)
        salt = secrets.token_hex(8)
        code_hash = _hash_code(raw_code, salt)

        # IP و UA
        ip = request.META.get("HTTP_CF_CONNECTING_IP") or request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]

        # ایجاد رکورد (فرانت نباید code_hash/salt/expires_at بدهد؛ اینجا ساخته می‌شود)
        otp = LoginOTP.objects.create(
            phone=phone,
            purpose=purpose,
            code_hash=code_hash,
            salt=salt,
            expires_at=expires_at,
            ip=ip,
            user_agent=user_agent,
        )

        # ارسال پیامک (real یا mock)
        try:
            sms.send_otp(mobile=otp.phone, code=raw_code)
        except Exception as e:
            # اگر می‌خواهی حتی با خطای SMS هم OTP ساخته شود، همین‌طور بماند.
            # اگر می‌خواهی rollback شود، اینجا otp.delete() کن.
            return Response(
                {"ok": False, "error": f"sms_failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        data = self.get_serializer(otp).data
        data["ok"] = True
        data["message"] = "OTP created and dispatch attempted"

        # فقط برای تست (در production خاموش)
        if getattr(settings, "SMS_MODE", "real") == "mock":
            data["debug_code"] = raw_code

        return Response(data, status=status.HTTP_201_CREATED)


class UserDeviceViewSet(viewsets.ModelViewSet):
    queryset = UserDevice.objects.all().order_by("-created_at")
    serializer_class = UserDeviceSerializer
    permission_classes = [IsAdminUser]
