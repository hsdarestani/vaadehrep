from django.db.models import ProtectedError
from rest_framework import serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from addresses.models import Address, AddressZoneMatch, DeliveryZone
from orders.models import Order
from orders.services import ACTIVE_ORDER_STATUSES


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

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user and user.is_authenticated and not user.is_staff:
            return qs.filter(user=user, is_active=True)
        return qs

    def _raise_if_locked(self, user):
        if Order.objects.filter(user=user, status__in=ACTIVE_ORDER_STATUSES).exists():
            raise serializers.ValidationError("در حال حاضر امکان ویرایش آدرس به دلیل سفارش فعال وجود ندارد.")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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


class DeliveryZoneViewSet(viewsets.ModelViewSet):
    queryset = DeliveryZone.objects.all().order_by("name")
    serializer_class = DeliveryZoneSerializer


class AddressZoneMatchViewSet(viewsets.ModelViewSet):
    queryset = AddressZoneMatch.objects.select_related("address", "zone").order_by("-matched_at")
    serializer_class = AddressZoneMatchSerializer
