from django.contrib import admin
from .models import (
    Category,
    OptionGroup,
    OptionItem,
    Product,
    ProductAvailability,
    ProductImage,
    ProductOptionGroup,
    ProductVariant,
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


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ("name", "code", "price_amount", "is_active", "sort_order")


class ProductOptionGroupInline(admin.TabularInline):
    model = ProductOptionGroup
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "vendor",
        "name_fa",
        "category",
        "base_price",
        "is_active",
        "is_available",
        "is_available_today",
        "sort_order",
        "updated_at",
    )
    list_filter = ("vendor", "is_active", "is_available", "is_available_today", "category")
    search_fields = ("name_fa", "name_en", "vendor__name")
    ordering = ("vendor", "sort_order", "name_fa")
    inlines = [ProductVariantInline, ProductImageInline, ProductOptionGroupInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "code", "name", "price_amount", "is_active", "sort_order", "updated_at")
    list_filter = ("is_active", "product__vendor")
    search_fields = ("code", "name", "product__name_fa", "product__vendor__name")
    ordering = ("product", "sort_order", "code")


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
