import functools
import json
from datetime import datetime, timedelta
from uuid import UUID

from authlib.integrations.django_client import OAuth, OAuthError
from django.conf import settings
from django.contrib.auth import SESSION_KEY, login, logout
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import ProtectedError
from django.forms import model_to_dict
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import exceptions, filters, mixins, serializers, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.settings import api_settings

from reportcreator_api.users.models import AuthIdentity, MFAMethod, PentestUser
from reportcreator_api.users.permissions import (
    APITokenViewSetPermissions,
    AuthIdentityViewSetPermissions,
    LocalUserAuthPermissions,
    MFALoginInProgressAuthentication,
    MFAMethodViewSetPermissons,
    RemoteUserAuthPermissions,
    UserViewSetPermissions,
)
from reportcreator_api.users.serializers import (
    APITokenCreateSerializer,
    APITokenSerializer,
    AuthIdentitySerializer,
    CreateUserSerializer,
    LoginMFACodeSerializer,
    LoginSerializer,
    MFAMethodRegisterBackupCodesSerializer,
    MFAMethodRegisterBeginSerializer,
    MFAMethodRegisterFIDO2Serializer,
    MFAMethodRegisterTOTPSerializer,
    MFAMethodSerializer,
    PentestUserDetailSerializer,
    PentestUserSerializer,
    ResetPasswordSerializer,
)
from reportcreator_api.utils import license

oauth = OAuth()
for name, config in settings.AUTHLIB_OAUTH_CLIENTS.items():
    oauth.register(name, **config)


class APIBadRequestError(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid input.'
    default_code = 'invalid'


@extend_schema(parameters=[OpenApiParameter(name='pentestuser_id', type={'oneOf': [{'type': 'string', 'format': 'uuid'}, {'const': 'self'}]}, location=OpenApiParameter.PATH)])
@extend_schema(parameters=[OpenApiParameter(name='id', type=UUID, location=OpenApiParameter.PATH)])
class UserSubresourceViewSetMixin(views.APIView):
    pagination_class = None

    @functools.cached_property
    def _get_user(self):
        if not self.request:
            return None

        user_pk = self.kwargs.get('pentestuser_pk')
        if user_pk == 'self':
            return self.request.user

        qs = PentestUser.objects.all()
        return get_object_or_404(qs, pk=user_pk)

    def get_user(self):
        return self._get_user

    def get_serializer_context(self):
        return super().get_serializer_context() | {
            'user': self.get_user(),
        }


@extend_schema(parameters=[OpenApiParameter(name='id', type=UUID, location=OpenApiParameter.PATH)])
class PentestUserViewSet(viewsets.ModelViewSet):
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES + [UserViewSetPermissions]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    filterset_fields = ['username', 'email']
    ordering_fields = ['created', 'username']
    ordering = ['-created']

    def get_queryset(self):
        return PentestUser.objects \
            .only_permitted(self.request.user) \
            .annotate_mfa_enabled() \
            .prefetch_related('auth_identities')

    def get_object(self):
        if self.kwargs.get('pk') == 'self':
            return self.request.user
        return super().get_object()

    def get_serializer_class(self):
        if self.action in ['change_password', 'reset_password']:
            return ResetPasswordSerializer
        elif self.action == 'create':
            return CreateUserSerializer
        elif (getattr(self.request.user, 'is_admin', False) or getattr(self.request.user, 'is_user_manager', False)) or \
             self.action in ['self', 'enable_admin_permissions', 'disable_admin_permissions']:
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

    @action(detail=False, url_path='self/admin/enable', methods=['post'])
    def enable_admin_permissions(self, request, *args, **kwargs):
        request.session['admin_permissions_enabled'] = True
        request.session.cycle_key()
        request.user.admin_permissions_enabled = True
        self.kwargs['pk'] = 'self'
        return self.retrieve(*args, request=request, **kwargs)

    @action(detail=False, url_path='self/admin/disable', methods=['post'])
    def disable_admin_permissions(self, request, *args, **kwargs):
        request.session.pop('admin_permissions_enabled', False)
        request.session.cycle_key()
        request.user.admin_permissions_enabled = False
        self.kwargs['pk'] = 'self'
        return self.retrieve(*args, request=request, **kwargs)

    @action(detail=True, url_path='reset-password', methods=['post'])
    def reset_password(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError as ex:
            raise serializers.ValidationError(
                detail='Cannot delete user because it is a member of one or more projects.',
            ) from ex


class MFAMethodViewSet(UserSubresourceViewSetMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES + [MFAMethodViewSetPermissons]

    def get_queryset(self):
        return self.get_user().mfa_methods.default_order()

    def get_serializer_class(self):
        if self.action in ['register_backup_begin', 'register_totp_begin', 'register_fido2_begin']:
            return MFAMethodRegisterBeginSerializer
        elif self.action == 'register_backup_complete':
            return MFAMethodRegisterBackupCodesSerializer
        elif self.action == 'register_totp_complete':
            return MFAMethodRegisterTOTPSerializer
        elif self.action == 'register_fido2_complete':
            return MFAMethodRegisterFIDO2Serializer
        return MFAMethodSerializer

    @extend_schema(responses=OpenApiTypes.OBJECT)
    @action(detail=False, url_path='register/backup/begin', methods=['post'])
    def register_backup_begin(self, request, *args, **kwargs):
        # if self.get_user().mfa_methods.filter(method_type=MFAMethodType.BACKUP).exists():
        #     raise APIBadRequestError('Backup codes already exist')

        instance = MFAMethod.objects.create_backup(save=False, user=self.get_user(), name='Backup Codes')
        return self.perform_register_begin(request, instance)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    @action(detail=False, url_path='register/totp/begin', methods=['post'])
    def register_totp_begin(self, request, *args, **kwargs):
        instance = MFAMethod.objects.create_totp(save=False, user=self.get_user(), name='TOTP')
        return self.perform_register_begin(request, instance, {'qrcode': instance.get_totp_qrcode()})

    @extend_schema(responses=OpenApiTypes.OBJECT)
    @action(detail=False, url_path='register/fido2/begin', methods=['post'])
    def register_fido2_begin(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = MFAMethod.objects.create_fido2_begin(user=self.get_user(), name='Security Key')
        return self.perform_register_begin(request, instance, {'state': None})

    def perform_register_begin(self, request, instance, additional_response_data=None):
        if additional_response_data is None:
            additional_response_data = {}
        request.session['mfa_register'] = json.dumps(model_to_dict(instance), cls=DjangoJSONEncoder)
        response_data = instance.data | additional_response_data
        return Response(response_data, status=status.HTTP_200_OK)

    @extend_schema(responses=MFAMethodSerializer)
    @action(detail=False, url_path='register/backup/complete', methods=['post'])
    def register_backup_complete(self, *args, **kwargs):
        return self.register_complete(*args, **kwargs)

    @extend_schema(responses=MFAMethodSerializer)
    @action(detail=False, url_path='register/totp/complete', methods=['post'])
    def register_totp_complete(self, *args, **kwargs):
        return self.register_complete(*args, **kwargs)

    @extend_schema(responses=MFAMethodSerializer)
    @action(detail=False, url_path='register/fido2/complete', methods=['post'])
    def register_fido2_complete(self, *args, **kwargs):
        return self.register_complete(*args, **kwargs)

    def register_complete(self, request, *args, **kwargs):
        if not request.session.get('mfa_register'):
            raise APIBadRequestError('No MFA registration in progress')
        mfa_register_state = json.loads(request.session['mfa_register'])
        mfa_register_state['user'] = self.get_user()
        instance = MFAMethod(**mfa_register_state)

        serializer = self.get_serializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        del request.session['mfa_register']
        return Response(MFAMethodSerializer(instance=instance).data, status=status.HTTP_201_CREATED)


class AuthIdentityViewSet(UserSubresourceViewSetMixin, viewsets.ModelViewSet):
    serializer_class = AuthIdentitySerializer
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES + [AuthIdentityViewSetPermissions, license.ProfessionalLicenseRequired]

    def get_queryset(self):
        return self.get_user().auth_identities.all()


    def get_serializer_context(self):
        return super().get_serializer_context() | {
            'user': self.get_user(),
        }


class APITokenViewSet(UserSubresourceViewSetMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = APITokenSerializer
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES + [APITokenViewSetPermissions]

    def get_queryset(self):
        return self.get_user().api_tokens.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return APITokenCreateSerializer
        return super().get_serializer_class()


class AuthViewSet(viewsets.ViewSet):
    schema = None
    authentication_classes = []
    permission_classes = []

    def get_serializer_class(self):
        if self.action == 'login':
            return LoginSerializer
        elif self.action == 'login_code':
            return LoginMFACodeSerializer
        else:
            return serializers.Serializer

    def get_serializer(self, *args, **kwargs):
        return self.get_serializer_class()(*args, context={'request': self.request}, **kwargs)

    @action(detail=False, methods=['post'], authentication_classes=[], permission_classes=[LocalUserAuthPermissions])
    def login(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        mfa_methods = list(user.mfa_methods.all().default_order())
        if not mfa_methods:
            # MFA disabled
            return self.perform_login(request, user)
        else:
            request.session['login_state'] = request.session.get('login_state', {}) | {
                'status': 'mfa-required',
                'user_id': str(user.id),
                'start': timezone.now().isoformat(),
            }
            return Response({
                'status': 'mfa-required',
                'mfa': MFAMethodSerializer(mfa_methods, many=True).data,
            }, status=200)

    @action(detail=False, methods=['post'], authentication_classes=api_settings.DEFAULT_AUTHENTICATION_CLASSES)
    def logout(self, request, *args, **kwargs):
        logout(request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, url_path='login/code', methods=['post'], authentication_classes=[MFALoginInProgressAuthentication], permission_classes=[LocalUserAuthPermissions])
    def login_code(self, request, *args, **kwargs):
        self._verify_mfa_preconditions(request)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.perform_login(request, request.user)

    @action(detail=False, url_path='login/fido2/begin', methods=['post'], authentication_classes=[MFALoginInProgressAuthentication], permission_classes=[LocalUserAuthPermissions])
    def login_fido2_begin(self, request, *args, **kwargs):
        self._verify_mfa_preconditions(request)

        credentials = MFAMethod.objects.get_fido2_user_credentials(request.user)
        if not credentials:
            raise APIBadRequestError('No FIDO2 devices registered')
        options, state = MFAMethod.get_fido2_server().authenticate_begin(credentials=credentials)
        request.session['login_state'] |= {'fido2_state': state}
        return Response(dict(options), status=status.HTTP_200_OK)

    @action(detail=False, url_path='login/fido2/complete', methods=['post'], authentication_classes=[MFALoginInProgressAuthentication], permission_classes=[LocalUserAuthPermissions])
    def login_fido2_complete(self, request, *args, **kwargs):
        self._verify_mfa_preconditions(request)
        state = request.session.get('login_state', {}).pop('fido2_state', None)
        try:
            MFAMethod.get_fido2_server().authenticate_complete(
                state=state,
                credentials=MFAMethod.objects.get_fido2_user_credentials(request.user),
                response=request.data,
            )
        except ValueError as ex:
            if ex.args and len(ex.args) == 1 and isinstance(ex.args[0], str):
                raise serializers.ValidationError(ex.args[0], 'fido2') from ex
            else:
                raise ex
        return self.perform_login(request, request.user)

    def _verify_mfa_preconditions(self, request):
        login_state = request.session.get('login_state', {})
        if login_state.get('status') != 'mfa-required':
            raise APIBadRequestError('MFA login not allowed')
        elif datetime.fromisoformat(login_state.get('start')) + settings.MFA_LOGIN_TIMEOUT < timezone.now():
            raise APIBadRequestError('Login timeout. Please restart login.')

    def perform_login(self, request, user, can_reauth=True):
        if not user.is_active:
            raise APIBadRequestError('User is inactive')
        license.validate_login_allowed(user)

        request.session.pop('login_state', None)
        first_login = not user.last_login
        is_reauth = bool(request.session.get('authentication_info', {}).get('login_time')) and str(user.id) == request.session.get(SESSION_KEY)
        if is_reauth and can_reauth:
            request.session.cycle_key()
            request.session['authentication_info'] |= {
                'reauth_time': timezone.now().isoformat(),
            }
        else:
            login(request=self.request, user=user)
            request.session['authentication_info'] = request.session.get('authentication_info', {}) | {
                'login_time': timezone.now().isoformat(),
            }
        return Response({
            'status': 'success',
            'first_login': first_login,
        }, status=status.HTTP_200_OK)

    @action(detail=False, url_path='login/oidc/(?P<oidc_provider>[a-zA-Z0-9]+)/begin', methods=['get'], permission_classes=[license.ProfessionalLicenseRequired])
    def login_oidc_begin(self, request, oidc_provider, *args, **kwargs):
        if oidc_provider not in settings.AUTHLIB_OAUTH_CLIENTS:
            raise APIBadRequestError(f'OIDC provider "{oidc_provider}" not supported')

        request.session['login_state'] = {
            'status': 'oidc-callback-required',
            'start': timezone.now().isoformat(),
        }
        redirect_uri = request.build_absolute_uri(f'/login/oidc/{oidc_provider}/callback')
        redirect_kwargs = {}
        if request.GET.get('reauth') and settings.AUTHLIB_OAUTH_CLIENTS[oidc_provider].get('reauth_supported', False):
            redirect_kwargs |= {
                'prompt': 'login',
                'max_age': 0,
            }
            if login_hint := request.session.get('authentication_info', {}).get(f'oidc_{oidc_provider}_login_hint'):
                redirect_kwargs |= {'login_hint': login_hint}

        return oauth.create_client(oidc_provider).authorize_redirect(request, redirect_uri, **redirect_kwargs)

    @action(detail=False, url_path='login/oidc/(?P<oidc_provider>[a-zA-Z0-9]+)/complete', methods=['get'], permission_classes=[license.ProfessionalLicenseRequired])
    def login_oidc_complete(self, request, oidc_provider, *args, **kwargs):
        if not request.session.get('login_state', {}).get('status') == 'oidc-callback-required':
            raise APIBadRequestError('No OIDC login in progress for session')

        try:
            token = oauth.create_client(oidc_provider).authorize_access_token(request)
        except OAuthError as ex:
            raise exceptions.AuthenticationFailed(detail=ex.description, code=ex.error) from ex

        email = token['userinfo'].get('email', 'unknown')
        identity = AuthIdentity.objects \
            .select_related('user') \
            .filter(provider=oidc_provider) \
            .filter(identifier=token['userinfo'].get('email')) \
            .first()
        if not identity:
            raise exceptions.AuthenticationFailed(detail=f'Auth identity not configured for any user: SSO provider "{oidc_provider}" identifier "{email}" ')

        can_reauth = False
        if not settings.AUTHLIB_OAUTH_CLIENTS[oidc_provider].get('reauth_supported', False):
            can_reauth = True
        elif (auth_time := token['userinfo'].get('auth_time')):
            can_reauth = (timezone.now() - timezone.make_aware(datetime.fromtimestamp(auth_time))) < timedelta(minutes=1)
        res = self.perform_login(request, identity.user, can_reauth=can_reauth)
        request.session['authentication_info'] |= {
            f'oidc_{oidc_provider}_login_hint': token['userinfo'].get('login_hint'),
        }
        return res

    @action(detail=False, url_path='login/remoteuser', methods=['post'], permission_classes=[RemoteUserAuthPermissions])
    def login_remoteuser(self, request, *args, **kwargs):
        remote_user_identifier = request.META.get('HTTP_' + settings.REMOTE_USER_AUTH_HEADER.upper().replace('-', '_'))

        identity = AuthIdentity.objects \
            .select_related('user') \
            .filter(provider=AuthIdentity.PROVIDER_REMOTE_USER) \
            .filter(identifier=remote_user_identifier) \
            .first()
        if not identity:
            raise exceptions.AuthenticationFailed()
        return self.perform_login(request, identity.user)


