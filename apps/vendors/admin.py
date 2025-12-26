from django.contrib import admin
from .models import Vendor, VendorDeliveryZone, VendorLocation, VendorHours, VendorStaff


class VendorDeliveryZoneInline(admin.TabularInline):
    model = VendorDeliveryZone
    extra = 1
    autocomplete_fields = ("zone",)
    raw_id_fields = ("zone",)
    fields = ("zone", "is_active")


class VendorHoursInline(admin.TabularInline):
    model = VendorHours
    extra = 1
    fields = ("weekday", "opens_at", "closes_at", "is_active")


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "slug",
        "is_active",
        "is_visible",
        "is_accepting_orders",
        "primary_phone_number",
        "city",
        "area",
        "supports_in_zone_delivery",
        "supports_out_of_zone_snapp_cod",
        "created_at",
    )
    list_filter = (
        "is_active",
        "is_visible",
        "is_accepting_orders",
        "supports_in_zone_delivery",
        "supports_out_of_zone_snapp_cod",
        "city",
        "area",
    )
    search_fields = ("name", "slug", "primary_phone_number", "city", "area", "address_text")
    inlines = [VendorHoursInline, VendorDeliveryZoneInline]


@admin.register(VendorLocation)
class VendorLocationAdmin(admin.ModelAdmin):
    list_display = ("id", "vendor", "title", "is_active", "service_radius_m", "lat", "lng", "created_at")
    list_filter = ("is_active",)
    search_fields = ("vendor__name", "title", "address_text")


@admin.register(VendorHours)
class VendorHoursAdmin(admin.ModelAdmin):
    list_display = ("id", "vendor", "weekday", "opens_at", "closes_at", "is_active")
    list_filter = ("weekday", "is_active")


@admin.register(VendorStaff)
class VendorStaffAdmin(admin.ModelAdmin):
    list_display = ("id", "vendor", "user", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("vendor__name", "user__username", "user__email")
