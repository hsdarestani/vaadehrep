from django.contrib.auth import get_user_model
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from addresses.models import Address
from catalog.models import Product
from integrations.services import payments
from orders.models import Order, OrderDelivery, OrderItem, OrderStatusHistory
from orders.services import (
    ACTIVE_ORDER_STATUSES,
    evaluate_vendor_serviceability,
    handle_order_status_change,
    notify_order_created,
    pick_nearest_available_vendor,
    suggest_products_for_user,
)
from vendors.models import Vendor
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def _normalize_phone(raw: str) -> str:
    if not raw:
        return ""
    p = str(raw).strip()
    return "".join(ch for ch in p if ch.isdigit())


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


class OrderSerializer(serializers.ModelSerializer):
    short_code = serializers.CharField(read_only=True)
    delivery_type = serializers.CharField(source="delivery.delivery_type", read_only=True)
    delivery_is_cash_on_delivery = serializers.BooleanField(
        source="delivery.is_cash_on_delivery", read_only=True, default=None
    )
    items = serializers.SerializerMethodField()
    delivery = serializers.SerializerMethodField()
    payment_url = serializers.SerializerMethodField()

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
            "delivery_type",
            "delivery_is_cash_on_delivery",
            "items",
            "delivery",
            "payment_url",
        ]
        read_only_fields = ["id", "placed_at", "user", "short_code", "items", "delivery", "payment_url"]

    def get_items(self, obj):
        return OrderItemSerializer(obj.items.order_by("created_at"), many=True).data

    def get_delivery(self, obj):
        if hasattr(obj, "delivery"):
            return OrderDeliverySerializer(obj.delivery).data
        return None

    def get_payment_url(self, obj):
        meta = obj.meta or {}
        payment_meta = meta.get("payment") if isinstance(meta, dict) else None
        if isinstance(payment_meta, dict):
            return payment_meta.get("payment_url") or payment_meta.get("paymentUrl") or payment_meta.get("url")
        return None


class OrderItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    quantity = serializers.IntegerField(min_value=1)
    modifiers = serializers.JSONField(required=False)


class CustomerLocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    accuracy = serializers.FloatField(required=False)


class DeliveryAddressInputSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, default="")
    full_text = serializers.CharField(required=False, allow_blank=True, default="")
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)
    city = serializers.CharField(required=False, allow_blank=True, default="")
    district = serializers.CharField(required=False, allow_blank=True, default="")
    street = serializers.CharField(required=False, allow_blank=True, default="")
    receiver_name = serializers.CharField(required=False, allow_blank=True, default="")
    receiver_phone = serializers.CharField(required=False, allow_blank=True, default="")


class OrderCreateSerializer(OrderSerializer):
    vendor = serializers.PrimaryKeyRelatedField(queryset=Vendor.objects.all(), required=False)
    delivery_address = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(), required=False, allow_null=True
    )
    items = OrderItemInputSerializer(many=True)
    customer_location = CustomerLocationSerializer(required=False)
    customer_phone = serializers.CharField(required=False, allow_blank=True)
    accept_terms = serializers.BooleanField(write_only=True)
    delivery_address_data = DeliveryAddressInputSerializer(required=False, allow_null=True)

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + [
            "items",
            "customer_location",
            "customer_phone",
            "accept_terms",
            "delivery_address_data",
        ]
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

        vendor = input_vendor or items[0]["product"].vendor
        attrs["vendor"] = vendor

        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated) and not _normalize_phone(attrs.get("customer_phone", "")):
            raise serializers.ValidationError({"customer_phone": "شماره موبایل برای ثبت سفارش مهمان لازم است."})

        if not attrs.get("accept_terms"):
            raise serializers.ValidationError({"accept_terms": "پذیرش قوانین و شرایط الزامی است."})

        coords = attrs.get("customer_location")
        address = attrs.get("delivery_address")
        address_data = attrs.get("delivery_address_data") or {}
        if not coords and address and address.latitude and address.longitude:
            coords = {"latitude": float(address.latitude), "longitude": float(address.longitude)}
        elif not coords and address_data and address_data.get("latitude") is not None:
            coords = {"latitude": address_data.get("latitude"), "longitude": address_data.get("longitude")}

        is_serviceable, delivery_type, delivery_fee, _, _ = evaluate_vendor_serviceability(vendor, coords)
        if not is_serviceable or not delivery_type:
            raise serializers.ValidationError("ارسال به این موقعیت برای این فروشنده فعال نیست.")

        attrs["delivery_type"] = delivery_type
        if coords:
            attrs["customer_location"] = coords
        if delivery_fee is not None:
            attrs["delivery_fee_amount"] = delivery_fee
        return attrs

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        customer_location = validated_data.pop("customer_location", None)
        customer_phone = _normalize_phone(validated_data.pop("customer_phone", ""))
        accept_terms = validated_data.pop("accept_terms", False)
        delivery_address_data = validated_data.pop("delivery_address_data", None)
        delivery_type = validated_data.pop("delivery_type", None)
        validated_data["status"] = "PENDING_PAYMENT"

        request = self.context.get("request")
        request_user = getattr(request, "user", None)

        if request_user and request_user.is_authenticated:
            user = request_user
        else:
            if not customer_phone:
                raise serializers.ValidationError("شماره موبایل برای ایجاد حساب لازم است.")
            user, created = User.objects.get_or_create(phone=customer_phone, defaults={"is_active": True})
            if created:
                user.set_unusable_password()
                user.save(update_fields=["password"])
            refresh = RefreshToken.for_user(user)
            self.issued_tokens = {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {"id": user.id, "phone": user.phone},
            }

        validated_data["user"] = user

        delivery_address = validated_data.get("delivery_address")
        if not delivery_address:
            if not delivery_address_data:
                raise serializers.ValidationError("آدرس تحویل مشخص نیست.")
            delivery_address = Address.objects.create(
                user=user,
                title=delivery_address_data.get("title") or "آدرس",
                full_text=delivery_address_data.get("full_text") or "",
                latitude=delivery_address_data.get("latitude"),
                longitude=delivery_address_data.get("longitude"),
                city=delivery_address_data.get("city") or "",
                district=delivery_address_data.get("district") or "",
                street=delivery_address_data.get("street") or "",
                receiver_name=delivery_address_data.get("receiver_name") or "",
                receiver_phone=_normalize_phone(delivery_address_data.get("receiver_phone", "")),
                is_default=not Address.objects.filter(user=user).exists(),
            )
            validated_data["delivery_address"] = delivery_address

        validated_data["payment_method"] = "ONLINE"
        validated_data["payment_status"] = "UNPAID"

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
        meta = {**meta, "accept_terms": accept_terms, "delivery_type": delivery_type}
        if customer_location:
            meta = {**meta, "customer_location": customer_location}
        order.meta = meta or None
        order.save(update_fields=["subtotal_amount", "total_amount", "meta"])

        OrderDelivery.objects.create(
            order=order,
            delivery_type=delivery_type or "IN_ZONE",
            is_cash_on_delivery=delivery_type == "OUT_OF_ZONE_SNAPP",
            external_provider="SNAPP" if delivery_type == "OUT_OF_ZONE_SNAPP" else "",
        )

        return order


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


class VendorSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            "id",
            "name",
            "slug",
            "city",
            "area",
            "lat",
            "lng",
            "is_accepting_orders",
            "supports_in_zone_delivery",
            "supports_out_of_zone_snapp_cod",
            "max_active_orders",
        ]
        read_only_fields = fields


class ProductSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "vendor",
            "category",
            "name_fa",
            "short_description",
            "base_price",
            "sort_order",
            "is_available",
            "is_available_today",
        ]
        read_only_fields = fields


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related("delivery").prefetch_related("items").order_by("-placed_at")
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return super().get_permissions()

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

    @action(detail=True, methods=["post"], permission_classes=[AllowAny])
    def pay(self, request, *args, **kwargs):
        order = self.get_object()
        provided_phone = _normalize_phone(
            request.data.get("customer_phone")
            or request.data.get("phone")
            or request.query_params.get("customer_phone")
            or request.query_params.get("phone")
        )
        normalized_order_phone = _normalize_phone(getattr(order.user, "phone", ""))
        is_staff_or_owner = request.user and request.user.is_authenticated and (
            request.user.is_staff or request.user.id == order.user_id
        )
        phone_matches = provided_phone and normalized_order_phone and (provided_phone == normalized_order_phone)
        if not (is_staff_or_owner or phone_matches):
            return Response({"detail": "دسترسی لازم را ندارید."}, status=status.HTTP_403_FORBIDDEN)

        if order.payment_status == "PAID":
            return Response({"detail": "این سفارش قبلاً پرداخت شده است."}, status=status.HTTP_400_BAD_REQUEST)

        if order.status not in {"PENDING_PAYMENT", "FAILED"}:
            return Response(
                {"detail": "این سفارش در وضعیت قابل پرداخت نیست."}, status=status.HTTP_400_BAD_REQUEST
            )

        payment_meta = order.meta.get("payment") if isinstance(order.meta, dict) else None
        existing_payment_url = None
        if isinstance(payment_meta, dict):
            existing_payment_url = (
                payment_meta.get("payment_url") or payment_meta.get("paymentUrl") or payment_meta.get("url")
            )
        if existing_payment_url:
            return Response({"payment_url": existing_payment_url}, status=status.HTTP_200_OK)

        payment = payments.create_payment(order)
        payment_url = payment.get("payment_url") or payment.get("paymentUrl") or payment.get("url") if payment else None
        if payment_url:
            meta = order.meta or {}
            meta["payment"] = payment
            order.meta = meta
            order.save(update_fields=["meta"])
            return Response({"payment_url": payment_url}, status=status.HTTP_200_OK)

        return Response(
            {"payment_url": None, "detail": "لینک پرداخت پیدا نشد. لطفاً دوباره تلاش کنید."},
            status=status.HTTP_200_OK,
        )

    def perform_create(self, serializer):
        order = serializer.save()
        self.issued_tokens = getattr(serializer, "issued_tokens", None)
        changed_by_type = "CUSTOMER" if not (self.request.user and self.request.user.is_staff) else "SYSTEM"
        OrderStatusHistory.objects.create(
            order=order,
            from_status="",
            to_status=order.status,
            changed_by_type=changed_by_type,
            changed_by_user=self.request.user if self.request.user.is_authenticated else order.user,
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
        if getattr(self, "issued_tokens", None):
            data["auth"] = self.issued_tokens
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


class ServiceabilityView(APIView):
    """
    بررسی در دسترس بودن سرویس، هزینه ارسال و نزدیک‌ترین آشپزخانه.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.data or {}
        coords = payload.get("location") or {}
        address_id = payload.get("address_id")
        vendor_id = payload.get("vendor")
        items = payload.get("items") or []

        if address_id:
            address = Address.objects.filter(id=address_id).first()
            if address and address.latitude and address.longitude:
                coords = {"latitude": float(address.latitude), "longitude": float(address.longitude)}

        vendor = None
        if vendor_id:
            vendor = Vendor.objects.filter(id=vendor_id, is_active=True, is_visible=True).first()
        if vendor is None:
            vendor = pick_nearest_available_vendor(coords)

        response = {
            "is_serviceable": False,
            "delivery_type": None,
            "delivery_fee_amount": 0,
            "vendor": None,
            "menu_products": [],
            "distance_meters": None,
            "suggested_product_ids": suggest_products_for_user(request.user),
        }

        active_order = None
        if request.user and request.user.is_authenticated:
            current_order = (
                Order.objects.filter(user=request.user, status__in=ACTIVE_ORDER_STATUSES)
                .order_by("-placed_at")
                .first()
            )
            if current_order:
                active_order = {
                    "id": str(current_order.id),
                    "short_code": current_order.short_code,
                    "status": current_order.status,
                }
        response["active_order"] = active_order

        if not vendor:
            response["reason"] = "no_vendor_available"
            return Response(response)

        is_serviceable, delivery_type, delivery_fee, location, distance_m = evaluate_vendor_serviceability(vendor, coords)
        if not is_serviceable or not delivery_type:
            response["reason"] = "location_out_of_range"
            return Response(response)

        vendor_products = Product.objects.filter(
            vendor=vendor, is_active=True, is_available=True, is_available_today=True
        ).order_by("sort_order", "id")

        # اگر آیتم‌های ورودی مربوط به وندور دیگری باشد، اجازه نمی‌دهیم
        input_product_vendor_ids = {
            prod.get("vendor") for prod in items if prod and isinstance(prod, dict) and prod.get("vendor") is not None
        }
        if input_product_vendor_ids and (vendor.id not in input_product_vendor_ids):
            response["reason"] = "vendor_mismatch"
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        response.update(
            {
                "is_serviceable": True,
                "delivery_type": delivery_type,
                "delivery_fee_amount": delivery_fee or 0,
                "vendor": VendorSummarySerializer(vendor).data,
                "menu_products": ProductSummarySerializer(vendor_products, many=True).data,
                "distance_meters": distance_m,
                "delivery_is_postpaid": delivery_type == "OUT_OF_ZONE_SNAPP",
                "delivery_label": "پیک داخلی با هزینه ثابت" if delivery_type == "IN_ZONE" else "ارسال با اسنپ (پس‌کرایه)",
            }
        )

        if location:
            response["nearest_location"] = {
                "title": location.title,
                "lat": float(location.lat),
                "lng": float(location.lng),
                "service_radius_m": location.service_radius_m,
            }

        return Response(response, status=status.HTTP_200_OK)
