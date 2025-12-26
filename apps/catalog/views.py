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
    ProductVariant,
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
    variants = serializers.PrimaryKeyRelatedField(read_only=True, many=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "vendor",
            "category",
            "name_fa",
            "name_en",
            "slug",
            "short_description",
            "description",
            "base_price",
            "sort_order",
            "is_active",
            "is_available",
            "is_available_today",
            "min_qty",
            "max_qty",
            "calories",
            "protein_g",
            "carbs_g",
            "fat_g",
            "variants",
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


class ProductVariantSerializer(serializers.ModelSerializer):
    vendor = serializers.PrimaryKeyRelatedField(source="product.vendor", read_only=True)
    category = serializers.PrimaryKeyRelatedField(source="product.category", read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "product",
            "vendor",
            "category",
            "code",
            "name",
            "price_amount",
            "sort_order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "vendor", "category"]


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


class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all().order_by("sort_order", "id")
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(
            is_active=True,
            product__is_active=True,
            product__is_available=True,
            product__is_available_today=True,
        )

        product_id = self.request.query_params.get("product")
        if product_id:
            qs = qs.filter(product_id=product_id)

        vendor_id = self.request.query_params.get("vendor")
        if vendor_id:
            qs = qs.filter(product__vendor_id=vendor_id)

        return qs


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("sort_order", "id")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by("sort_order", "id")
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(is_active=True, is_available=True, is_available_today=True)

        vendor_id = self.request.query_params.get("vendor")
        if vendor_id:
            qs = qs.filter(vendor_id=vendor_id)

        category_id = self.request.query_params.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)

        available_today = self.request.query_params.get("is_available_today")
        if available_today is not None:
            qs = qs.filter(is_available_today=available_today.lower() == "true")

        is_active_param = self.request.query_params.get("is_active")
        if is_active_param is not None:
            qs = qs.filter(is_active=is_active_param.lower() == "true")

        is_available_param = self.request.query_params.get("is_available")
        if is_available_param is not None:
            qs = qs.filter(is_available=is_available_param.lower() == "true")

        return qs


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
