from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from addresses.models import Address, AddressZoneMatch, DeliveryZone


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
            return qs.filter(user=user)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DeliveryZoneViewSet(viewsets.ModelViewSet):
    queryset = DeliveryZone.objects.all().order_by("name")
    serializer_class = DeliveryZoneSerializer


class AddressZoneMatchViewSet(viewsets.ModelViewSet):
    queryset = AddressZoneMatch.objects.select_related("address", "zone").order_by("-matched_at")
    serializer_class = AddressZoneMatchSerializer
