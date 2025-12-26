from rest_framework import serializers, viewsets
from rest_framework.permissions import SAFE_METHODS, BasePermission

from vendors.models import Vendor, VendorHours, VendorLocation, VendorStaff


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            "id",
            "name",
            "slug",
            "is_active",
            "is_accepting_orders",
            "phone_number",
            "telegram_chat_id",
            "logo_url",
            "description",
            "prep_time_minutes_default",
            "min_order_amount",
            "max_active_orders",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class VendorLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorLocation
        fields = [
            "id",
            "vendor",
            "title",
            "is_active",
            "address_text",
            "lat",
            "lng",
            "service_radius_m",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class VendorHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorHours
        fields = [
            "id",
            "vendor",
            "weekday",
            "opens_at",
            "closes_at",
            "is_active",
        ]
        read_only_fields = ["id"]


class VendorStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorStaff
        fields = [
            "id",
            "vendor",
            "user",
            "role",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all().order_by("name")
    serializer_class = VendorSerializer
    permission_classes = [IsAdminOrReadOnly]


class VendorLocationViewSet(viewsets.ModelViewSet):
    queryset = VendorLocation.objects.all().order_by("-created_at")
    serializer_class = VendorLocationSerializer
    permission_classes = [IsAdminOrReadOnly]


class VendorHoursViewSet(viewsets.ModelViewSet):
    queryset = VendorHours.objects.all().order_by("weekday", "opens_at")
    serializer_class = VendorHoursSerializer
    permission_classes = [IsAdminOrReadOnly]


class VendorStaffViewSet(viewsets.ModelViewSet):
    queryset = VendorStaff.objects.all().order_by("-created_at")
    serializer_class = VendorStaffSerializer
    permission_classes = [IsAdminOrReadOnly]
