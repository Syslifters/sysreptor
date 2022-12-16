from rest_framework.response import Response
from rest_framework import viewsets, views, status, filters, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from reportcreator_api.users.models import PentestUser
from reportcreator_api.users.permissions import UserViewSetPermissions
from reportcreator_api.users.serializers import ChangePasswordSerializer, CreateUserSerializer, PentestUserDetailSerializer, PentestUserSerializer, ResetPasswordSerializer


class PentestUserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = [UserViewSetPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']

    def get_queryset(self):
        return PentestUser.objects \
            .only_permitted(self.request.user)

    def get_object(self):
        if self.kwargs.get('pk') == 'self':
            return self.request.user
        return super().get_object()

    def get_serializer_class(self):
        if self.action == 'change_password':
            return ChangePasswordSerializer
        elif self.action == 'reset_password':
            return ResetPasswordSerializer
        elif self.action == 'create':
            return CreateUserSerializer
        elif self.request.user.is_superuser or self.request.user.is_user_manager or self.action == 'self':
            return PentestUserDetailSerializer
        else:
            return PentestUserSerializer

    @action(detail=False, methods=['get', 'put', 'patch'])
    def self(self, request, *args, **kwargs):
        self.kwargs['pk'] = 'self'
        if request.method == 'PUT':
            return self.update(request, *args, **kwargs)
        elif request.method == 'PATCH':
            return self.partial_update(request, *args, **kwargs)
        else:
            return self.retrieve(request, *args, **kwargs)

    @action(detail=False, url_path='self/change-password', methods=['post'])
    def change_password(self, request, *args, **kwargs):
        self.kwargs['pk'] = 'self'
        return self.update(request, *args, **kwargs)

    @action(detail=True, url_path='reset-password', methods=['post'])
    def reset_password(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class TokenLogoutView(views.APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

