from django.urls import path
from rest_framework import routers

from accounts.views import (
    LoginOTPViewSet,
    SessionView,
    TelegramUserViewSet,
    UserDeviceViewSet,
    UserViewSet,
    VerifyLoginView,
)

router = routers.DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"telegram-users", TelegramUserViewSet)
router.register(r"login-otps", LoginOTPViewSet)
router.register(r"user-devices", UserDeviceViewSet)

urlpatterns = router.urls
urlpatterns += [
    path("verify-login/", VerifyLoginView.as_view(), name="verify-login"),
    path("session/", SessionView.as_view(), name="session"),
]
