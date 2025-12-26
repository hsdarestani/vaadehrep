from django.contrib import admin
from .models import Address, DeliveryZone, AddressZoneMatch


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "city", "district", "is_default", "is_active", "updated_at")
    search_fields = ("user__phone", "title", "city", "district", "full_text")
    list_filter = ("is_default", "is_active", "city")
    readonly_fields = ("created_at", "updated_at")


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "city", "is_active", "allow_out_of_zone", "out_of_zone_policy", "updated_at")
    search_fields = ("name", "city")
    list_filter = ("is_active", "allow_out_of_zone", "out_of_zone_policy")
    readonly_fields = ("created_at", "updated_at")


@admin.register(AddressZoneMatch)
class AddressZoneMatchAdmin(admin.ModelAdmin):
    list_display = ("id", "address", "zone", "matched_by", "matched_at")
    list_filter = ("matched_by",)

