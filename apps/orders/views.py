from rest_framework import serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from catalog.models import Product
from integrations.services import payments
from orders.models import Order, OrderDelivery, OrderItem, OrderStatusHistory
from orders.services import handle_order_status_change, notify_order_created
from vendors.models import Vendor


class OrderSerializer(serializers.ModelSerializer):
    short_code = serializers.CharField(read_only=True)

    def validate_payment_method(self, value):
        if value != "ONLINE":
            raise serializers.ValidationError("در حال حاضر تنها پرداخت آنلاین فعال است.")
        return value

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
            "short_code",
        ]
        read_only_fields = ["id", "placed_at", "user", "short_code"]


class OrderItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    quantity = serializers.IntegerField(min_value=1)
    modifiers = serializers.JSONField(required=False)


class CustomerLocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    accuracy = serializers.FloatField(required=False)


class OrderCreateSerializer(OrderSerializer):
    vendor = serializers.PrimaryKeyRelatedField(queryset=Vendor.objects.all(), required=False)
    items = OrderItemInputSerializer(many=True)
    customer_location = CustomerLocationSerializer(required=False)

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + ["items", "customer_location"]
        read_only_fields = OrderSerializer.Meta.read_only_fields

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("حداقل یک آیتم برای ثبت سفارش لازم است.")
        return items

    def validate_delivery_address(self, address):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated and not user.is_staff and address.user_id != user.id:
            raise serializers.ValidationError("آدرس انتخاب‌شده متعلق به شما نیست.")
        return address

    def validate(self, attrs):
        items = attrs.get("items", [])
        if not items:
            return attrs

        item_vendors = {item["product"].vendor for item in items}
        input_vendor = attrs.get("vendor")

        if input_vendor:
            item_vendors.add(input_vendor)

        if len(item_vendors) > 1:
            raise serializers.ValidationError("تمام اقلام سفارش باید از یک فروشنده باشند.")

        attrs["vendor"] = input_vendor or items[0]["product"].vendor
        return attrs

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        customer_location = validated_data.pop("customer_location", None)

        validated_data["payment_method"] = "ONLINE"

        order = Order.objects.create(**validated_data)

        subtotal = 0
        for item in items:
            product = item["product"]
            quantity = item.get("quantity") or 1
            unit_price = product.base_price
            line_subtotal = unit_price * quantity
            subtotal += line_subtotal

            OrderItem.objects.create(
                order=order,
                product=product,
                product_title_snapshot=product.name_fa,
                unit_price_snapshot=unit_price,
                quantity=quantity,
                modifiers=item.get("modifiers"),
                line_subtotal=line_subtotal,
            )

        order.subtotal_amount = subtotal
        discount_amount = order.discount_amount or 0
        delivery_fee = order.delivery_fee_amount or 0
        service_fee = order.service_fee_amount or 0
        order.total_amount = subtotal - discount_amount + delivery_fee + service_fee

        meta = order.meta or {}
        if customer_location:
            meta = {**meta, "customer_location": customer_location}
        order.meta = meta or None
        order.save(update_fields=["subtotal_amount", "total_amount", "meta"])

        return order


class OrderItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    quantity = serializers.IntegerField(min_value=1)
    modifiers = serializers.JSONField(required=False)


class CustomerLocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    accuracy = serializers.FloatField(required=False)


class OrderCreateSerializer(OrderSerializer):
    vendor = serializers.PrimaryKeyRelatedField(queryset=Vendor.objects.all(), required=False)
    items = OrderItemInputSerializer(many=True)
    customer_location = CustomerLocationSerializer(required=False)

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + ["items", "customer_location"]
        read_only_fields = OrderSerializer.Meta.read_only_fields

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("حداقل یک آیتم برای ثبت سفارش لازم است.")
        return items

    def validate_delivery_address(self, address):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated and not user.is_staff and address.user_id != user.id:
            raise serializers.ValidationError("آدرس انتخاب‌شده متعلق به شما نیست.")
        return address

    def validate(self, attrs):
        items = attrs.get("items", [])
        if not items:
            return attrs

        item_vendors = {item["product"].vendor for item in items}
        input_vendor = attrs.get("vendor")

        if input_vendor:
            item_vendors.add(input_vendor)

        if len(item_vendors) > 1:
            raise serializers.ValidationError("تمام اقلام سفارش باید از یک فروشنده باشند.")

        attrs["vendor"] = input_vendor or items[0]["product"].vendor
        return attrs

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        customer_location = validated_data.pop("customer_location", None)

        validated_data["payment_method"] = "ONLINE"

        order = Order.objects.create(**validated_data)

        subtotal = 0
        for item in items:
            product = item["product"]
            quantity = item.get("quantity") or 1
            unit_price = product.base_price
            line_subtotal = unit_price * quantity
            subtotal += line_subtotal

            OrderItem.objects.create(
                order=order,
                product=product,
                product_title_snapshot=product.name_fa,
                unit_price_snapshot=unit_price,
                quantity=quantity,
                modifiers=item.get("modifiers"),
                line_subtotal=line_subtotal,
            )

        order.subtotal_amount = subtotal
        discount_amount = order.discount_amount or 0
        delivery_fee = order.delivery_fee_amount or 0
        service_fee = order.service_fee_amount or 0
        order.total_amount = subtotal - discount_amount + delivery_fee + service_fee

        meta = order.meta or {}
        if customer_location:
            meta = {**meta, "customer_location": customer_location}
        order.meta = meta or None
        order.save(update_fields=["subtotal_amount", "total_amount", "meta"])

        return order


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

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return super().get_serializer_class()

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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        order: Order = serializer.instance

        payment = payments.create_payment(order)
        payment_url = None
        if payment:
            payment_url = payment.get("payment_url") or payment.get("paymentUrl") or payment.get("url")
            if payment_url:
                meta = order.meta or {}
                meta["payment"] = payment
                order.meta = meta
                order.save(update_fields=["meta"])

        headers = self.get_success_headers(serializer.data)
        data = dict(serializer.data)
        data["payment_url"] = payment_url
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


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
