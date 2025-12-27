from rest_framework import routers

from accounts.views import LoginOTPViewSet, PhoneLoginView, TelegramUserViewSet, UserDeviceViewSet, UserViewSet
from django.urls import path

router = routers.DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"telegram-users", TelegramUserViewSet)
router.register(r"login-otps", LoginOTPViewSet)
router.register(r"user-devices", UserDeviceViewSet)

urlpatterns = [path("login/", PhoneLoginView.as_view(), name="phone-login")]
urlpatterns += router.urls
