from rest_framework import routers

from orders.views import (
    OrderDeliveryViewSet,
    OrderItemViewSet,
    OrderStatusHistoryViewSet,
    OrderViewSet,
)

router = routers.DefaultRouter()
router.register(r"orders", OrderViewSet)
router.register(r"order-items", OrderItemViewSet)
router.register(r"order-deliveries", OrderDeliveryViewSet)
router.register(r"order-status-history", OrderStatusHistoryViewSet)

urlpatterns = router.urls
