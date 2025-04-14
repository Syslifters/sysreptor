from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.settings import api_settings

from sysreptor.notifications.serializers import UserNotificationSerializer
from sysreptor.users.views import UserSubresourceViewSetMixin
from sysreptor.utils.api import CursorMultiPagination


class UserNotificationPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user == view.get_user()


class UserNotificationOrderingFilter(filters.OrderingFilter):
    ordering_fields = ['created', 'group']

    def get_queryset_ordering(self, request, queryset, view):
        out = []
        for o in self.get_ordering(request, queryset, view):
            if o == 'group':
                out.extend(['group_order', 'created'])
            elif o == '-group':
                out.extend(['-group_order', '-created'])
            else:
                out.append(o)
        return out

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_queryset_ordering(request, queryset, view)
        if ordering:
            if 'group' in ''.join(ordering):
                queryset = queryset.annotate_group_order()
            return queryset.order_by(*ordering)
        return queryset


class UserNotificationViewSet(UserSubresourceViewSetMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserNotificationSerializer
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES + [UserNotificationPermissions]
    filter_backends = [DjangoFilterBackend, UserNotificationOrderingFilter]
    pagination_class = CursorMultiPagination
    filterset_fields = ['read']
    ordering = '-created'

    def get_queryset(self):
        return self.get_user().notifications \
            .only_visible() \
            .select_related('created_by', 'remotenotificationspec', 'project', 'finding', 'section', 'note', 'comment', 'comment__finding', 'comment__section')

    @extend_schema(request=Serializer, responses=Serializer)
    @action(detail=False, methods=['post'])
    def readall(self, request, *args, **kwargs):
        self.get_queryset().update(read=True)
        return Response({})
