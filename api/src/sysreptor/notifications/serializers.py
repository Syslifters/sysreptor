from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from sysreptor.notifications.models import Notification, RemoteNotificationSpec


class NotificationSpecContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RemoteNotificationSpec
        fields = ['title', 'text', 'link_url']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'created', 'updated', 'status', 'content']


class UserConditionsSerializer(serializers.Serializer):
    is_superuser = serializers.BooleanField(required=False)
    is_project_admin = serializers.BooleanField(required=False)
    is_user_manager = serializers.BooleanField(required=False)
    is_designer = serializers.BooleanField(required=False)
    is_template_editor = serializers.BooleanField(required=False)


class NotificationSpecListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        notifications = [RemoteNotificationSpec(**n) for n in validated_data]
        # Set deleted notifications as inactive
        RemoteNotificationSpec.objects \
            .only_active() \
            .exclude(id__in=[n.id for n in notifications]) \
            .update(active_until=(timezone.now() - timedelta(days=1)).date())
        Notification.objects \
            .filter(remotenotificationspec__isnull=False) \
            .exclude(id__in=[n.id for n in notifications]) \
            .update(visible_until=timezone.now())

        # Create new notifications
        existing_notification_ids = set(RemoteNotificationSpec.objects.filter(id__in=[n.id for n in notifications]).values_list('id', flat=True))
        new_notifications = list(filter(lambda n: n.id not in existing_notification_ids, notifications))
        return RemoteNotificationSpec.objects.bulk_create(new_notifications)


class NotificationSpecSerializer(serializers.ModelSerializer):
    user_conditions = UserConditionsSerializer(required=False)

    class Meta:
        model = RemoteNotificationSpec
        fields = ['id', 'active_until', 'visible_for_days', 'user_conditions', 'title', 'text', 'link_url']
        extra_kwargs = {'id': {'read_only': False}}
        list_serializer_class = NotificationSpecListSerializer

