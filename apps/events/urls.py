from rest_framework import routers

from events.views import EventTypeViewSet, EventViewSet

router = routers.DefaultRouter()
router.register(r"event-types", EventTypeViewSet)
router.register(r"events", EventViewSet)

urlpatterns = router.urls
