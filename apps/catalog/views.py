from rest_framework import serializers, viewsets
from rest_framework.permissions import SAFE_METHODS, BasePermission

from catalog.models import (
    Category,
    OptionGroup,
    OptionItem,
    Product,
    ProductAvailability,
    ProductImage,
    ProductOptionGroup,
)


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "vendor",
            "name",
            "slug",
            "description",
            "sort_order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "vendor",
            "category",
            "name",
            "slug",
            "short_description",
            "description",
            "price_amount",
            "sort_order",
            "is_active",
            "is_available",
            "min_qty",
            "max_qty",
            "calories",
            "protein_g",
            "carbs_g",
            "fat_g",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = [
            "id",
            "product",
            "image_url",
            "alt_text",
            "sort_order",
            "is_primary",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class OptionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptionGroup
        fields = [
            "id",
            "vendor",
            "name",
            "description",
            "is_required",
            "min_select",
            "max_select",
            "sort_order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class OptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptionItem
        fields = [
            "id",
            "group",
            "name",
            "description",
            "price_delta_amount",
            "sort_order",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ProductOptionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductOptionGroup
        fields = [
            "id",
            "product",
            "group",
            "is_required",
            "min_select",
            "max_select",
            "sort_order",
            "is_active",
        ]
        read_only_fields = ["id"]


class ProductAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAvailability
        fields = [
            "id",
            "product",
            "weekday",
            "start_time",
            "end_time",
            "is_active",
        ]
        read_only_fields = ["id"]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("sort_order", "id")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by("sort_order", "id")
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all().order_by("-created_at")
    serializer_class = ProductImageSerializer
    permission_classes = [IsAdminOrReadOnly]


class OptionGroupViewSet(viewsets.ModelViewSet):
    queryset = OptionGroup.objects.all().order_by("sort_order", "id")
    serializer_class = OptionGroupSerializer
    permission_classes = [IsAdminOrReadOnly]


class OptionItemViewSet(viewsets.ModelViewSet):
    queryset = OptionItem.objects.all().order_by("sort_order", "id")
    serializer_class = OptionItemSerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductOptionGroupViewSet(viewsets.ModelViewSet):
    queryset = ProductOptionGroup.objects.all().order_by("sort_order", "id")
    serializer_class = ProductOptionGroupSerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = ProductAvailability.objects.all().order_by("weekday", "start_time")
    serializer_class = ProductAvailabilitySerializer
    permission_classes = [IsAdminOrReadOnly]
