from rest_framework import routers

from vendors.views import (
    VendorHoursViewSet,
    VendorLocationViewSet,
    VendorStaffViewSet,
    VendorViewSet,
)

router = routers.DefaultRouter()
router.register(r"vendors", VendorViewSet)
router.register(r"vendor-locations", VendorLocationViewSet)
router.register(r"vendor-hours", VendorHoursViewSet)
router.register(r"vendor-staff", VendorStaffViewSet)

urlpatterns = router.urls
