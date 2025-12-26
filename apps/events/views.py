from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAdminUser

from events.models import Event, EventType


class EventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType
        fields = [
            "id",
            "code",
            "description",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id",
            "event_type",
            "actor_user",
            "actor_type",
            "order",
            "vendor",
            "source",
            "level",
            "payload",
            "ip",
            "user_agent",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class EventTypeViewSet(viewsets.ModelViewSet):
    queryset = EventType.objects.all().order_by("code")
    serializer_class = EventTypeSerializer
    permission_classes = [IsAdminUser]


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.select_related("event_type").all().order_by("-created_at")
    serializer_class = EventSerializer
    permission_classes = [IsAdminUser]
