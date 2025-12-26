from django.contrib import admin
from .models import AppSetting, FeatureFlag, MediaAsset


@admin.register(AppSetting)
class AppSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value_type", "description", "updated_at")
    search_fields = ("key", "description")
    list_filter = ("value_type",)


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ("code", "is_active", "updated_at")
    search_fields = ("code", "description")
    list_filter = ("is_active",)


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("id", "asset_type", "title", "is_active", "created_at")
    search_fields = ("title", "url")
    list_filter = ("asset_type", "is_active")

