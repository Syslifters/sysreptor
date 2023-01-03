import functools
import json
from datetime import datetime
from rest_framework.response import Response
from rest_framework import viewsets, views, status, filters, mixins, serializers, exceptions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.settings import api_settings
from django.conf import settings
from django.forms import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404
from django.utils import timezone

from reportcreator_api.users.models import PentestUser, MFAMethod, MFAMethodType
from reportcreator_api.users.permissions import UserViewSetPermissions, MFAMethodViewSetPermissons, MFALoginInProgressAuthentication
from reportcreator_api.users.serializers import CreateUserSerializer, PentestUserDetailSerializer, PentestUserSerializer, \
    ResetPasswordSerializer, MFAMethodSerializer, LoginSerializer, LoginMFACodeSerializer, MFAMethodRegisterBackupCodesSerializer, \
    MFAMethodRegisterTOTPSerializer, MFAMethodRegisterFIDO2Serializer


class APIBadRequestError(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid input.'
    default_code = 'invalid'


class PentestUserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = [UserViewSetPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']

    def get_queryset(self):
        return PentestUser.objects \
            .only_permitted(self.request.user) \
            .annotate_mfa_enabled()

    def get_object(self):
        if self.kwargs.get('pk') == 'self':
            return self.request.user
        return super().get_object()

    def get_serializer_class(self):
        if self.action == 'change_password':
            return ResetPasswordSerializer
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


class MFAMethodViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES + [MFAMethodViewSetPermissons]
    pagination_class = None

    @functools.cache
    def get_user(self):
        user_pk = self.kwargs['pentestuser_pk']
        if user_pk == 'self':
            return self.request.user
        
        qs = PentestUser.objects.all()
        return get_object_or_404(qs, pk=user_pk)

    def get_queryset(self):
        return MFAMethod.objects \
            .only_permitted(self.request.user) \
            .filter(user=self.get_user()) \
            .default_order()

    def get_serializer_class(self):
        if self.action in ['register_backup_begin', 'register_totp_begin', 'register_fido2_begin']:
            return serializers.Serializer
        elif self.action == 'register_backup_complete':
            return MFAMethodRegisterBackupCodesSerializer
        elif self.action == 'register_totp_complete':
            return MFAMethodRegisterTOTPSerializer
        elif self.action == 'register_fido2_complete':
            return MFAMethodRegisterFIDO2Serializer
        return MFAMethodSerializer

    def get_serializer_context(self):
        return super().get_serializer_context() | {
            'user': self.get_user()
        }

    @action(detail=False, url_path='register/backup/begin', methods=['post'])
    def register_backup_begin(self, request, *args, **kwargs):
        # if self.get_user().mfa_methods.filter(method_type=MFAMethodType.BACKUP).exists():
        #     raise APIBadRequestError('Backup codes already exist')

        instance = MFAMethod.objects.create_backup(save=False, user=self.get_user(), name='Backup Codes')
        return self.perform_register_begin(request, instance)

    @action(detail=False, url_path='register/totp/begin', methods=['post'])
    def register_totp_begin(self, request, *args, **kwargs):
        instance = MFAMethod.objects.create_totp(save=False, user=self.get_user(), name='TOTP')
        return self.perform_register_begin(request, instance, {'qrcode': instance.get_totp_qrcode()})
    
    @action(detail=False, url_path='register/fido2/begin', methods=['post'])
    def register_fido2_begin(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = MFAMethod.objects.create_fido2_begin(user=self.get_user(), name='Security Key')
        return self.perform_register_begin(request, instance, {'state': None})

    def perform_register_begin(self, request, instance, additional_response_data={}):
        request.session['mfa_register'] = json.dumps(model_to_dict(instance), cls=DjangoJSONEncoder)
        response_data = instance.data | additional_response_data
        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=False, url_path='register/backup/complete', methods=['post'])
    def register_backup_complete(self, *args, **kwargs):
        return self.register_complete(*args, **kwargs)

    @action(detail=False, url_path='register/totp/complete', methods=['post'])
    def register_totp_complete(self, *args, **kwargs):
        return self.register_complete(*args, **kwargs)

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


class AuthViewSet(viewsets.ViewSet):
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
        return self.get_serializer_class()(context={'request': self.request}, *args, **kwargs)
    
    @action(detail=False, methods=['post'])
    def login(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        mfa_methods = list(user.mfa_methods.all().default_order())
        if not mfa_methods:
            # MFA disabled
            return self.perform_login(request, user)
        else:
            request.session['login_state'] = {
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

    @action(detail=False, url_path='login/code', methods=['post'], authentication_classes=[MFALoginInProgressAuthentication])
    def login_code(self, request, *args, **kwargs):
        self._verify_mfa_preconditions(request)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.perform_login(request, request.user)

    @action(detail=False, url_path='login/fido2/begin', methods=['post'], authentication_classes=[MFALoginInProgressAuthentication])
    def login_fido2_begin(self, request, *args, **kwargs):
        self._verify_mfa_preconditions(request)

        credentials = MFAMethod.objects.get_fido2_user_credentials(request.user)
        if not credentials:
            raise APIBadRequestError('No FIDO2 devices registered')
        options, state = MFAMethod.get_fido2_server().authenticate_begin(credentials=credentials)
        request.session['login_state'] |= {'fido2_state': state}
        return Response(dict(options), status=status.HTTP_200_OK)

    @action(detail=False, url_path='login/fido2/complete', methods=['post'], authentication_classes=[MFALoginInProgressAuthentication])
    def login_fido2_complete(self, request, *args, **kwargs):
        self._verify_mfa_preconditions(request)
        state = request.session.get('login_state', {}).pop('fido2_state', None)
        MFAMethod.get_fido2_server().authenticate_complete(
            state=state, 
            credentials=MFAMethod.objects.get_fido2_user_credentials(request.user),
            response=request.data
        )
        return self.perform_login(request, request.user)

    def _verify_mfa_preconditions(self, request):
        login_state = request.session.get('login_state', {})
        if login_state.get('status') != 'mfa-required':
            raise APIBadRequestError('MFA login not allowed')
        elif datetime.fromisoformat(login_state.get('start')) + settings.MFA_LOGIN_TIMEOUT < timezone.now():
            raise APIBadRequestError('Login timeout. Please restart login.')

    def perform_login(self, request, user):
        request.session.pop('login_state', None)
        is_reauth = bool(request.session.get('authentication_info', {}).get('login_time')) and str(user.id) == request.session.get('_auth_user_id')
        if is_reauth:
            request.session['authentication_info'] |= {
                'reauth_time': timezone.now().isoformat(),
            }
        else:
            request.session['authentication_info'] = {
                'login_time': timezone.now().isoformat(),
            }
            login(request=self.request, user=user)
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
