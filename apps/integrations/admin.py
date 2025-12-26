from django.contrib import admin
from .models import (
    IntegrationProvider,
    IntegrationEndpoint,
    VendorIntegrationConfig,
    ExternalRequestLog,
    ProviderHealthCheck,
)


@admin.register(IntegrationProvider)
class IntegrationProviderAdmin(admin.ModelAdmin):
    list_display = ("kind", "code", "name", "is_active", "base_url", "created_at")
    list_filter = ("kind", "is_active")
    search_fields = ("code", "name")


@admin.register(IntegrationEndpoint)
class IntegrationEndpointAdmin(admin.ModelAdmin):
    list_display = ("provider", "code", "method", "path", "timeout_seconds", "is_active", "created_at")
    list_filter = ("provider", "method", "is_active")
    search_fields = ("provider__code", "code", "path")


@admin.register(VendorIntegrationConfig)
class VendorIntegrationConfigAdmin(admin.ModelAdmin):
    list_display = ("vendor", "provider", "is_active", "created_at")
    list_filter = ("provider", "is_active")
    search_fields = ("vendor__name", "provider__code")


@admin.register(ExternalRequestLog)
class ExternalRequestLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "provider",
        "endpoint",
        "response_status",
        "outcome",
        "duration_ms",
        "trace_id",
        "order",
        "vendor",
        "created_at",
    )
    list_filter = ("provider", "outcome", "response_status", "created_at")
    search_fields = ("trace_id", "error_message", "request_url")
    readonly_fields = ("created_at",)


@admin.register(ProviderHealthCheck)
class ProviderHealthCheckAdmin(admin.ModelAdmin):
    list_display = ("provider", "status", "latency_ms", "checked_at")
    list_filter = ("status", "checked_at", "provider")
    readonly_fields = ("checked_at",)

