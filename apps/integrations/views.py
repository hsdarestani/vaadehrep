from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAdminUser

from integrations.models import (
    ExternalRequestLog,
    IntegrationEndpoint,
    IntegrationProvider,
    ProviderHealthCheck,
    VendorIntegrationConfig,
)


class IntegrationProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationProvider
        fields = [
            "id",
            "kind",
            "code",
            "name",
            "base_url",
            "is_active",
            "credentials_ref",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class IntegrationEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationEndpoint
        fields = [
            "id",
            "provider",
            "code",
            "path",
            "method",
            "timeout_seconds",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class VendorIntegrationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorIntegrationConfig
        fields = [
            "id",
            "vendor",
            "provider",
            "config",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ExternalRequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalRequestLog
        fields = [
            "id",
            "provider",
            "endpoint",
            "order",
            "vendor",
            "user",
            "trace_id",
            "request_url",
            "request_method",
            "request_headers",
            "request_body",
            "response_status",
            "response_headers",
            "response_body",
            "duration_ms",
            "outcome",
            "error_message",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ProviderHealthCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderHealthCheck
        fields = [
            "id",
            "provider",
            "status",
            "latency_ms",
            "details",
            "checked_at",
        ]
        read_only_fields = ["id", "checked_at"]


class IntegrationProviderViewSet(viewsets.ModelViewSet):
    queryset = IntegrationProvider.objects.all().order_by("code")
    serializer_class = IntegrationProviderSerializer
    permission_classes = [IsAdminUser]


class IntegrationEndpointViewSet(viewsets.ModelViewSet):
    queryset = IntegrationEndpoint.objects.select_related("provider").all().order_by("provider__code", "code")
    serializer_class = IntegrationEndpointSerializer
    permission_classes = [IsAdminUser]


class VendorIntegrationConfigViewSet(viewsets.ModelViewSet):
    queryset = VendorIntegrationConfig.objects.select_related("vendor", "provider").all().order_by("-created_at")
    serializer_class = VendorIntegrationConfigSerializer
    permission_classes = [IsAdminUser]


class ExternalRequestLogViewSet(viewsets.ModelViewSet):
    queryset = ExternalRequestLog.objects.all().order_by("-created_at")
    serializer_class = ExternalRequestLogSerializer
    permission_classes = [IsAdminUser]


class ProviderHealthCheckViewSet(viewsets.ModelViewSet):
    queryset = ProviderHealthCheck.objects.select_related("provider").all().order_by("-checked_at")
    serializer_class = ProviderHealthCheckSerializer
    permission_classes = [IsAdminUser]
