from rest_framework import routers

from core.views import AppSettingViewSet, FeatureFlagViewSet, MediaAssetViewSet

router = routers.DefaultRouter()
router.register(r"settings", AppSettingViewSet)
router.register(r"feature-flags", FeatureFlagViewSet)
router.register(r"media-assets", MediaAssetViewSet)

urlpatterns = router.urls
