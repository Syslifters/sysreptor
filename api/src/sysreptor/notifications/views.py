from rest_framework import mixins, permissions, viewsets
from rest_framework.settings import api_settings

from sysreptor.notifications.serializers import UserNotificationSerializer
from sysreptor.users.views import UserSubresourceViewSetMixin


class NotificationPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user == view.get_user()


class NotificationViewSet(UserSubresourceViewSetMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserNotificationSerializer
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES + [NotificationPermissions]
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get_queryset(self):
        return self.get_user().notifications \
            .only_visible() \
            .select_related('notification')
