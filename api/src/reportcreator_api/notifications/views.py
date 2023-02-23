from rest_framework import viewsets, mixins, permissions
from rest_framework.settings import api_settings

from reportcreator_api.notifications.models import UserNotification
from reportcreator_api.notifications.serializers import UserNotificationSerializer


class NotificationPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        return view.kwargs.get('pentestuser_pk') == 'self'


class NotificationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserNotificationSerializer
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES + [NotificationPermissions]

    def get_queryset(self):
        return UserNotification.objects \
            .only_permitted(self.request.user) \
            .only_visible() \
            .select_related('notification')
