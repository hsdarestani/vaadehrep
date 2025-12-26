from rest_framework import routers

from catalog.views import (
    CategoryViewSet,
    OptionGroupViewSet,
    OptionItemViewSet,
    ProductAvailabilityViewSet,
    ProductImageViewSet,
    ProductOptionGroupViewSet,
    ProductVariantViewSet,
    ProductViewSet,
)

router = routers.DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"products", ProductViewSet)
router.register(r"product-images", ProductImageViewSet)
router.register(r"option-groups", OptionGroupViewSet)
router.register(r"option-items", OptionItemViewSet)
router.register(r"product-option-groups", ProductOptionGroupViewSet)
router.register(r"product-availability", ProductAvailabilityViewSet)
router.register(r"product-variants", ProductVariantViewSet)

urlpatterns = router.urls
