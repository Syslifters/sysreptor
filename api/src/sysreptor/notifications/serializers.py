from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from sysreptor.notifications.models import RemoteNotificationSpec, UserNotification
from sysreptor.utils.utils import omit_items


class NotificationSpecContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RemoteNotificationSpec
        fields = ['title', 'text', 'link_url']


class UserNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotification
        fields = ['id', 'created', 'updated', 'read', 'content']
        read_only_fields = omit_items(fields, ['read'])


class UserConditionsSerializer(serializers.Serializer):
    is_superuser = serializers.BooleanField(required=False)
    is_project_admin = serializers.BooleanField(required=False)
    is_user_manager = serializers.BooleanField(required=False)
    is_designer = serializers.BooleanField(required=False)
    is_template_editor = serializers.BooleanField(required=False)


class RemoteNotificationSpecListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        notifications = [RemoteNotificationSpec(**n) for n in validated_data]
        # Set deleted notifications as inactive
        RemoteNotificationSpec.objects \
            .only_active() \
            .exclude(id__in=[n.id for n in notifications]) \
            .update(active_until=(timezone.now() - timedelta(days=1)).date())
        UserNotification.objects \
            .filter(remotenotificationspec__isnull=False) \
            .exclude(remotenotificationspec_id__in=[n.id for n in notifications]) \
            .update(visible_until=timezone.now())

        # Create new notifications
        existing_notification_ids = set(RemoteNotificationSpec.objects.filter(id__in=[n.id for n in notifications]).values_list('id', flat=True))
        new_notifications = list(filter(lambda n: n.id not in existing_notification_ids, notifications))
        return RemoteNotificationSpec.objects.bulk_create(new_notifications)


class RemoteNotificationSpecSerializer(serializers.ModelSerializer):
    user_conditions = UserConditionsSerializer(required=False)

    class Meta:
        model = RemoteNotificationSpec
        fields = ['id', 'active_until', 'visible_for_days', 'user_conditions', 'title', 'text', 'link_url']
        extra_kwargs = {'id': {'read_only': False}}
        list_serializer_class = RemoteNotificationSpecListSerializer

