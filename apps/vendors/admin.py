from django.contrib import admin
from .models import Vendor, VendorLocation, VendorHours, VendorStaff


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "is_active", "is_accepting_orders", "phone_number", "created_at")
    list_filter = ("is_active", "is_accepting_orders")
    search_fields = ("name", "slug", "phone_number")


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

