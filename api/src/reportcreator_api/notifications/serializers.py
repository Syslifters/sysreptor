from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers

from reportcreator_api.notifications.models import UserNotification, NotificationSpec


class NotificationSpecContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSpec
        fields = ['title', 'text', 'link_url']


class UserNotificationSerializer(serializers.ModelSerializer):
    content = NotificationSpecContentSerializer(source='notification', read_only=True)

    class Meta:
        model = UserNotification
        fields = ['id', 'created', 'updated', 'read', 'content']


class InstanceConditionsSerializer(serializers.Serializer):
    version = serializers.RegexField(r'^(==|>=|<=|>|<)?[0-9a-zA-Z.]+$', required=False)
    any_tags = serializers.ListField(child=serializers.CharField(), required=False)


class UserConditionsSerializer(serializers.Serializer):
    is_superuser = serializers.BooleanField(required=False)
    is_user_manager = serializers.BooleanField(required=False)
    is_designer = serializers.BooleanField(required=False)
    is_template_editor = serializers.BooleanField(required=False)


class NotificationSpecListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        notifications = [NotificationSpec(**n) for n in validated_data]
        # Set deleted notifications as inactive
        NotificationSpec.objects \
            .only_active() \
            .exclude(id__in=[n.id for n in notifications]) \
            .update(active_until=(timezone.now() - timedelta(days=1)).date())
        # Create new notifications
        existing_notification_ids = set(NotificationSpec.objects.filter(id__in=[n.id for n in notifications]).values_list('id', flat=True))
        new_notifications = list(filter(lambda n: n.id not in existing_notification_ids and NotificationSpec.objects.check_instance_conditions(n), notifications))
        return NotificationSpec.objects.bulk_create(new_notifications)


class NotificationSpecSerializer(serializers.ModelSerializer):
    instance_conditions = InstanceConditionsSerializer(required=False)
    user_conditions = UserConditionsSerializer(required=False)

    class Meta:
        model = NotificationSpec
        fields = ['id', 'active_until', 'visible_for_days', 'instance_conditions', 'user_conditions', 'title', 'text', 'link_url']
        extra_kwargs = {'id': {'read_only': False}}
        list_serializer_class = NotificationSpecListSerializer

