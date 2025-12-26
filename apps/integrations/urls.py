from django.urls import path
from rest_framework import routers

from integrations.views import (
    ExternalRequestLogViewSet,
    IntegrationEndpointViewSet,
    IntegrationProviderViewSet,
    ProviderHealthCheckViewSet,
    VendorIntegrationConfigViewSet,
    payment_callback,
    telegram_webhook,
)

router = routers.DefaultRouter()
router.register(r"providers", IntegrationProviderViewSet)
router.register(r"endpoints", IntegrationEndpointViewSet)
router.register(r"vendor-configs", VendorIntegrationConfigViewSet)
router.register(r"request-logs", ExternalRequestLogViewSet)
router.register(r"health-checks", ProviderHealthCheckViewSet)

urlpatterns = router.urls + [
    path("telegram/webhook/<str:secret>/", telegram_webhook, name="telegram-webhook"),
    path("payments/callback/", payment_callback, name="payment-callback"),
]
