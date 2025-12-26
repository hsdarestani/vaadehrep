from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from orders.models import Order, OrderDelivery, OrderItem, OrderStatusHistory
from orders.services import handle_order_status_change, notify_order_created


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "id",
            "vendor",
            "source",
            "status",
            "delivery_address",
            "customer_note",
            "admin_note",
            "subtotal_amount",
            "discount_amount",
            "delivery_fee_amount",
            "service_fee_amount",
            "total_amount",
            "currency",
            "payment_status",
            "payment_method",
            "placed_at",
            "confirmed_at",
            "delivered_at",
            "cancelled_at",
            "meta",
        ]
        read_only_fields = ["id", "placed_at", "user"]


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "order",
            "product",
            "product_title_snapshot",
            "unit_price_snapshot",
            "quantity",
            "modifiers",
            "line_subtotal",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class OrderDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDelivery
        fields = [
            "id",
            "order",
            "delivery_type",
            "is_cash_on_delivery",
            "courier_name",
            "courier_phone",
            "tracking_code",
            "tracking_url",
            "external_delivery_quote_amount",
            "external_delivery_final_amount",
            "external_provider",
            "external_payload",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = [
            "id",
            "order",
            "from_status",
            "to_status",
            "changed_by_type",
            "changed_by_user",
            "reason",
            "meta",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by("-placed_at")
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user and user.is_authenticated and not user.is_staff:
            return qs.filter(user=user)
        return qs

    def perform_create(self, serializer):
        order = serializer.save(user=self.request.user)
        OrderStatusHistory.objects.create(
            order=order,
            from_status="",
            to_status=order.status,
            changed_by_type="CUSTOMER" if self.request.user and not self.request.user.is_staff else "SYSTEM",
            changed_by_user=self.request.user if self.request.user.is_authenticated else None,
        )
        notify_order_created(order)

    def perform_update(self, serializer):
        prev_status = serializer.instance.status
        order = serializer.save()
        if prev_status != order.status:
            OrderStatusHistory.objects.create(
                order=order,
                from_status=prev_status,
                to_status=order.status,
                changed_by_type="CUSTOMER" if self.request.user and not self.request.user.is_staff else "SYSTEM",
                changed_by_user=self.request.user if self.request.user.is_authenticated else None,
            )
            handle_order_status_change(order)


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all().order_by("-created_at")
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user and user.is_authenticated and not user.is_staff:
            return qs.filter(order__user=user)
        return qs


class OrderDeliveryViewSet(viewsets.ModelViewSet):
    queryset = OrderDelivery.objects.all().order_by("-created_at")
    serializer_class = OrderDeliverySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user and user.is_authenticated and not user.is_staff:
            return qs.filter(order__user=user)
        return qs


class OrderStatusHistoryViewSet(viewsets.ModelViewSet):
    queryset = OrderStatusHistory.objects.select_related("order").order_by("-created_at")
    serializer_class = OrderStatusHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user and user.is_authenticated and not user.is_staff:
            return qs.filter(order__user=user)
        return qs
