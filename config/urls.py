from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # API Root
    path("api/core/", include(("apps.core.urls", "core"), namespace="core")),
    path("api/accounts/", include(("apps.accounts.urls", "accounts"), namespace="accounts")),
    path("api/addresses/", include(("apps.addresses.urls", "addresses"), namespace="addresses")),
    path("api/catalog/", include(("apps.catalog.urls", "catalog"), namespace="catalog")),
    path("api/vendors/", include(("apps.vendors.urls", "vendors"), namespace="vendors")),
    path("api/orders/", include(("apps.orders.urls", "orders"), namespace="orders")),
    path("api/notifications/", include(("apps.notifications.urls", "notifications"), namespace="notifications")),
    path("api/integrations/", include(("apps.integrations.urls", "integrations"), namespace="integrations")),
    path("api/events/", include(("apps.events.urls", "events"), namespace="events")),
]

