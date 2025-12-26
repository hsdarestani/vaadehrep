from django.contrib import admin
from .models import Event, EventType


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "is_active", "created_at")
    search_fields = ("code", "description")
    list_filter = ("is_active",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "event_type",
        "actor_type",
        "actor_user",
        "order",
        "vendor",
        "source",
        "level",
        "created_at",
    )
    search_fields = (
        "event_type__code",
        "actor_user__phone",
        "order__id",
        "vendor__name",
    )
    list_filter = ("actor_type", "source", "level", "created_at")
    readonly_fields = ("created_at",)

