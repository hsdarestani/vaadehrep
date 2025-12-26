from rest_framework import routers

from accounts.views import (
    LoginOTPViewSet,
    TelegramUserViewSet,
    UserDeviceViewSet,
    UserViewSet,
)

router = routers.DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"telegram-users", TelegramUserViewSet)
router.register(r"login-otps", LoginOTPViewSet)
router.register(r"user-devices", UserDeviceViewSet)

urlpatterns = router.urls
