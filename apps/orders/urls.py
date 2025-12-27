from rest_framework import routers

from django.urls import path
from orders.views import (
    OrderDeliveryViewSet,
    OrderItemViewSet,
    OrderStatusHistoryViewSet,
    OrderViewSet,
    ServiceabilityView,
)

router = routers.DefaultRouter()
router.register(r"orders", OrderViewSet)
router.register(r"order-items", OrderItemViewSet)
router.register(r"order-deliveries", OrderDeliveryViewSet)
router.register(r"order-status-history", OrderStatusHistoryViewSet)

urlpatterns = router.urls
urlpatterns += [
    path("serviceability/", ServiceabilityView.as_view(), name="serviceability"),
]
