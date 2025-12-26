from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAdminUser

from core.models import AppSetting, FeatureFlag, MediaAsset


class AppSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppSetting
        fields = [
            "id",
            "key",
            "value_type",
            "value_str",
            "value_int",
            "value_bool",
            "value_json",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class FeatureFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureFlag
        fields = [
            "id",
            "code",
            "description",
            "rules",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MediaAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAsset
        fields = [
            "id",
            "asset_type",
            "title",
            "url",
            "meta",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AppSettingViewSet(viewsets.ModelViewSet):
    queryset = AppSetting.objects.all().order_by("key")
    serializer_class = AppSettingSerializer
    permission_classes = [IsAdminUser]


class FeatureFlagViewSet(viewsets.ModelViewSet):
    queryset = FeatureFlag.objects.all().order_by("code")
    serializer_class = FeatureFlagSerializer
    permission_classes = [IsAdminUser]


class MediaAssetViewSet(viewsets.ModelViewSet):
    queryset = MediaAsset.objects.all().order_by("-created_at")
    serializer_class = MediaAssetSerializer
    permission_classes = [IsAdminUser]
