from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, TelegramUser, LoginOTP, UserDevice


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = ("id", "phone", "full_name", "is_staff", "is_active", "created_at")
    search_fields = ("phone", "full_name")
    ordering = ("-id",)
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Profile", {"fields": ("full_name", "default_city", "notes")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Timestamps", {"fields": ("created_at", "last_login_at")}),
    )
    add_fieldsets = (
        (None, {"fields": ("phone", "password1", "password2", "is_staff", "is_active")}),
    )
    readonly_fields = ("created_at", "last_login_at")


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "telegram_user_id", "username", "is_blocked", "last_seen_at")
    search_fields = ("telegram_user_id", "username", "user__phone")
    list_filter = ("is_blocked",)


@admin.register(LoginOTP)
class LoginOTPAdmin(admin.ModelAdmin):
    list_display = ("id", "phone", "purpose", "created_at", "expires_at", "attempts", "is_used")
    search_fields = ("phone",)
    list_filter = ("purpose", "is_used")
    readonly_fields = ("created_at",)


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "device_id", "title", "ip", "is_active", "last_seen_at")
    search_fields = ("device_id", "user__phone")
    list_filter = ("is_active",)

