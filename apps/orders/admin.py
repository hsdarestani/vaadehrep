from django.contrib import admin
from .models import Order, OrderItem, OrderDelivery, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "vendor",
        "user",
        "status",
        "payment_status",
        "payment_method",
        "source",
        "total_amount",
        "placed_at",
    )
    list_filter = ("status", "payment_status", "payment_method", "source", "vendor", "placed_at")
    search_fields = ("id", "user__email", "user__username")
    inlines = [OrderItemInline]


@admin.register(OrderDelivery)
class OrderDeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "delivery_type",
        "is_cash_on_delivery",
        "external_provider",
        "external_delivery_final_amount",
        "tracking_code",
        "created_at",
    )
    list_filter = ("delivery_type", "external_provider")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product_title_snapshot", "quantity", "unit_price_snapshot", "line_subtotal", "created_at")
    search_fields = ("order__id", "product_title_snapshot")


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("order", "from_status", "to_status", "changed_by_type", "changed_by_user", "reason", "created_at")
    list_filter = ("to_status", "changed_by_type", "created_at")
    search_fields = ("order__id", "reason")

