from django.contrib import admin
from .models import (
    Category, Product, ProductImage,
    OptionGroup, OptionItem, ProductOptionGroup,
    ProductAvailability,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "vendor", "name", "sort_order", "is_active", "updated_at")
    list_filter = ("vendor", "is_active")
    search_fields = ("name", "vendor__name")
    ordering = ("vendor", "sort_order", "name")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class ProductOptionGroupInline(admin.TabularInline):
    model = ProductOptionGroup
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "vendor", "name", "category", "price_amount", "is_active", "is_available", "sort_order", "updated_at")
    list_filter = ("vendor", "is_active", "is_available", "category")
    search_fields = ("name", "vendor__name")
    ordering = ("vendor", "sort_order", "name")
    inlines = [ProductImageInline, ProductOptionGroupInline]


@admin.register(OptionGroup)
class OptionGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "vendor", "name", "is_required", "min_select", "max_select", "is_active", "updated_at")
    list_filter = ("vendor", "is_active", "is_required")
    search_fields = ("name", "vendor__name")
    ordering = ("vendor", "sort_order", "name")


@admin.register(OptionItem)
class OptionItemAdmin(admin.ModelAdmin):
    list_display = ("id", "group", "name", "price_delta_amount", "is_active", "sort_order")
    list_filter = ("is_active", "group__vendor")
    search_fields = ("name", "group__name", "group__vendor__name")
    ordering = ("group", "sort_order", "name")


@admin.register(ProductAvailability)
class ProductAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "weekday", "start_time", "end_time", "is_active")
    list_filter = ("weekday", "is_active", "product__vendor")

