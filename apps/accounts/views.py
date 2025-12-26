from django.contrib.auth import get_user_model
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAdminUser

from accounts.models import LoginOTP, TelegramUser, UserDevice


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


class LoginOTPViewSet(viewsets.ModelViewSet):
    queryset = LoginOTP.objects.all().order_by("-created_at")
    serializer_class = LoginOTPSerializer
    permission_classes = [IsAdminUser]


class UserDeviceViewSet(viewsets.ModelViewSet):
    queryset = UserDevice.objects.all().order_by("-created_at")
    serializer_class = UserDeviceSerializer
    permission_classes = [IsAdminUser]
