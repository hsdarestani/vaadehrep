from rest_framework import routers

from notifications.views import (
    AdminRecipientViewSet,
    NotificationDeliveryViewSet,
    NotificationTemplateViewSet,
    NotificationViewSet,
)

router = routers.DefaultRouter()
router.register(r"templates", NotificationTemplateViewSet)
router.register(r"notifications", NotificationViewSet)
router.register(r"deliveries", NotificationDeliveryViewSet)
router.register(r"admin-recipients", AdminRecipientViewSet)

urlpatterns = router.urls
