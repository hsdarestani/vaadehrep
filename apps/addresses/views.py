from django.contrib.auth import get_user_model
from django.db.models import ProtectedError
from rest_framework import serializers, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from addresses.models import Address, AddressZoneMatch, DeliveryZone
from orders.models import Order
from orders.services import ACTIVE_ORDER_STATUSES
from rest_framework_simplejwt.tokens import RefreshToken
from core.utils import normalize_phone

User = get_user_model()


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "title",
            "receiver_name",
            "receiver_phone",
            "province",
            "city",
            "district",
            "street",
            "alley",
            "building",
            "plaque",
            "unit",
            "floor",
            "postal_code",
            "full_text",
            "notes",
            "latitude",
            "longitude",
            "is_default",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "user"]


class DeliveryZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryZone
        fields = [
            "id",
            "name",
            "city",
            "description",
            "is_active",
            "districts_csv",
            "allow_out_of_zone",
            "out_of_zone_policy",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AddressZoneMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressZoneMatch
        fields = [
            "id",
            "address",
            "zone",
            "matched_by",
            "matched_at",
        ]
        read_only_fields = ["id", "matched_at"]


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all().order_by("-created_at")
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user and user.is_authenticated and not user.is_staff:
            return qs.filter(user=user, is_active=True)
        return qs

    def _raise_if_locked(self, user):
        if Order.objects.filter(user=user, status__in=ACTIVE_ORDER_STATUSES).exists():
            raise serializers.ValidationError("در حال حاضر امکان ویرایش آدرس به دلیل سفارش فعال وجود ندارد.")

    def perform_update(self, serializer):
        user = self.request.user
        if user and user.is_authenticated and not user.is_staff:
            self._raise_if_locked(user)
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if user and user.is_authenticated and not user.is_staff:
            self._raise_if_locked(user)
        return super().perform_destroy(instance)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            instance.is_active = False
            instance.save(update_fields=["is_active", "updated_at"])
            return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        issued_tokens = None
        request_user = request.user if request.user and request.user.is_authenticated else None

        if not request_user:
            provided_phone = normalize_phone(
                request.data.get("receiver_phone")
                or request.data.get("phone")
                or request.data.get("customer_phone")
                or request.query_params.get("phone")
                or request.query_params.get("customer_phone")
            )
            if not provided_phone:
                return Response(
                    {"detail": "شماره موبایل برای ثبت آدرس مهمان لازم است."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user, created = User.objects.get_or_create(phone=provided_phone, defaults={"is_active": True})
            if created:
                user.set_unusable_password()
                user.save(update_fields=["password"])
            refresh = RefreshToken.for_user(user)
            issued_tokens = {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {"id": user.id, "phone": user.phone},
            }
            request_user = user

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_first_address = not Address.objects.filter(user=request_user).exists()
        address = serializer.save(
            user=request_user,
            is_default=serializer.validated_data.get("is_default") or is_first_address,
        )
        headers = self.get_success_headers(serializer.data)
        data = self.get_serializer(address).data
        if issued_tokens:
            data["auth"] = issued_tokens
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class DeliveryZoneViewSet(viewsets.ModelViewSet):
    queryset = DeliveryZone.objects.all().order_by("name")
    serializer_class = DeliveryZoneSerializer


class AddressZoneMatchViewSet(viewsets.ModelViewSet):
    queryset = AddressZoneMatch.objects.select_related("address", "zone").order_by("-matched_at")
    serializer_class = AddressZoneMatchSerializer
