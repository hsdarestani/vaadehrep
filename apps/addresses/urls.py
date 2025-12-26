from rest_framework import routers

from addresses.views import AddressViewSet, AddressZoneMatchViewSet, DeliveryZoneViewSet

router = routers.DefaultRouter()
router.register(r"addresses", AddressViewSet)
router.register(r"delivery-zones", DeliveryZoneViewSet)
router.register(r"address-zone-matches", AddressZoneMatchViewSet)

urlpatterns = router.urls
