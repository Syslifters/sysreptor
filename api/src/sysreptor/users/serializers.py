import functools
import json
import logging
from collections import OrderedDict
from types import SimpleNamespace
from uuid import UUID

from asgiref.sync import async_to_sync
from authlib.integrations.django_client import OAuth
from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from sysreptor.users.models import APIToken, AuthIdentity, MFAMethod, MFAMethodType, PentestUser, Session
from sysreptor.users.roles import Permission, expand_permissions, get_all_roles, get_role_permissions
from sysreptor.utils import license
from sysreptor.utils.configuration import configuration
from sysreptor.utils.mail import send_mail
from sysreptor.utils.serializers import OptionalPrimaryKeyRelatedField

# Deprecated is_* API flags ↔ role IDs (persisted only as roles).
LEGACY_USER_FLAG_ROLES = {
    'is_project_admin': 'project_admin',
    'is_designer': 'designer',
    'is_template_editor': 'template_editor',
    'is_user_manager': 'user_manager',
    'is_global_archiver': 'global_archiver',
    'is_guest': 'guest',
}


def roles_from_legacy_flags(role_ids, flags: dict[str, bool]) -> list[str]:
    roles = list(dict.fromkeys(role_ids or []))
    for flag, role in LEGACY_USER_FLAG_ROLES.items():
        if flag not in flags or flag == 'is_guest':
            continue
        if flags[flag]:
            if role not in roles:
                roles.append(role)
        else:
            roles = [r for r in roles if r != role]
    if 'is_guest' in flags:
        if flags['is_guest']:
            roles = [r for r in roles if r != 'regular_user']
            if 'guest' not in roles:
                roles.append('guest')
        else:
            roles = [r for r in roles if r != 'guest']
            if 'regular_user' not in roles:
                roles.append('regular_user')
    return list(dict.fromkeys(roles))


class LegacyFlagField(serializers.BooleanField):
    """Deprecated boolean API flag backed by a role ID on PentestUser.roles."""

    def __init__(self, role_id: str, **kwargs):
        self.role_id = role_id
        kwargs.setdefault('required', False)
        kwargs['source'] = '*'
        super().__init__(**kwargs)

    def bind(self, field_name, parent):
        super().bind(field_name, parent)
        if not self._can_write():
            self.read_only = True

    def _can_write(self) -> bool:
        if not getattr(self.parent, 'legacy_flags_writable', False):
            return False
        request = self.context.get('request') if self.context else None
        user = getattr(request, 'user', None)
        instance = getattr(self.parent, 'instance', None) if self.parent else None
        return bool(
            getattr(user, 'is_admin', False)
            or (
                user
                and getattr(user, 'is_authenticated', False)
                and user.has_permission(Permission.USER_EDIT)
                and not getattr(instance, 'is_superuser', False)
            ),
        )

    def to_representation(self, value):
        return self.role_id in (getattr(value, 'roles', None) or [])

    def get_value(self, dictionary):
        if not isinstance(dictionary, dict) or self.field_name not in dictionary:
            return serializers.empty
        return dictionary

    def to_internal_value(self, data):
        if not self._can_write():
            raise serializers.SkipField()
        logging.warning(f'Deprecated user API field user.{self.field_name} in request; use user.roles instead (request.user="{self.context["request"].user.username}")')
        if 'roles' in data:
            raise serializers.ValidationError('Cannot set roles and legacy permission flags together. Fully migrate to roles')

        flag_updates = {
            name: serializers.BooleanField.to_internal_value(self, data.get(name))
            for name, field in self.parent.fields.items()
            if isinstance(field, LegacyFlagField) and name in data
        }
        roles = roles_from_legacy_flags(list(configuration.DEFAULT_USER_ROLES or []), flag_updates)
        all_roles = get_all_roles()
        if invalid_roles := [r for r in roles if r not in all_roles]:
            raise serializers.ValidationError(f'Invalid roles: {", ".join(invalid_roles)}')
        return {'roles': list(dict.fromkeys(roles))}


@functools.cache
def get_oauth():
    authlib_oauth_clients = json.loads(configuration.OIDC_AUTHLIB_OAUTH_CLIENTS or '{}')

    oauth = OAuth()
    for name, config in authlib_oauth_clients.items():
        try:
            oauth.register(name, **config)
        except Exception:
            logging.exception(f'Failed to register OAuth client {name}')
    return oauth


class PentestUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = PentestUser
        fields = ['id', 'username', 'name', 'color', 'title_before', 'first_name', 'middle_name', 'last_name', 'title_after', 'is_active']


class PentestUserDetailSerializer(serializers.ModelSerializer):
    legacy_flags_writable = False

    is_mfa_enabled = serializers.SerializerMethodField()
    is_admin = serializers.BooleanField(read_only=True)
    effective_permissions = serializers.ListField(child=serializers.CharField(), read_only=True)
    # Deprecated compatibility. Will be removed in the future
    is_project_admin = LegacyFlagField(role_id='project_admin')
    is_designer = LegacyFlagField(role_id='designer')
    is_template_editor = LegacyFlagField(role_id='template_editor')
    is_user_manager = LegacyFlagField(role_id='user_manager')
    is_global_archiver = LegacyFlagField(role_id='global_archiver')
    is_guest = LegacyFlagField(role_id='guest')

    class Meta:
        model = PentestUser
        fields = [
            'id', 'created', 'updated', 'last_login', 'is_active',
            'username', 'name', 'title_before', 'first_name', 'middle_name', 'last_name', 'title_after',
            'email', 'phone', 'mobile', 'color', 'must_change_password',
            'is_superuser', 'is_admin', 'is_system_user', 'roles', 'effective_permissions',
            'is_mfa_enabled', 'has_password', 'can_login_local', 'can_login_sso',
            *list(LEGACY_USER_FLAG_ROLES.keys()),
        ]
        read_only_fields = ['last_login', 'is_system_user']

    def get_is_mfa_enabled(self, obj) -> bool:
        if (is_mfa_enabled := getattr(obj, 'is_mfa_enabled', None)) is not None:
            return is_mfa_enabled
        return obj.mfa_methods.all().exists()

    def validate_roles(self, value):
        all_roles = get_all_roles()
        if invalid_roles := [r for r in value if r not in all_roles]:
            raise serializers.ValidationError(f'Invalid roles: {", ".join(invalid_roles)}')
        return list(dict.fromkeys(value))

    def get_extra_kwargs(self):
        user = self.context['request'].user
        read_only = not (getattr(user, 'is_admin', False) or (user.is_authenticated and user.has_permission(Permission.USER_EDIT) and not getattr(self.instance, 'is_superuser', False)))
        return super().get_extra_kwargs() | {
            'is_superuser': {'read_only': not getattr(user, 'is_admin', False)},
            'roles': {'read_only': read_only},
            'username': {'read_only': read_only},
            'email': {'read_only': read_only},
            'is_active': {'read_only': read_only},
            'must_change_password': {'read_only': read_only},
            'can_login_local': {'read_only': read_only},
        }

    def validate_is_active(self, value):
        if self.instance and self.instance.id == self.context['request'].user.id:
            if not value:
                raise serializers.ValidationError('Cannot deactivate yourself')
        return value


class CreateUserSerializer(PentestUserDetailSerializer):
    legacy_flags_writable = True

    password = serializers.CharField(write_only=True, required=False, allow_null=True, default=None, trim_whitespace=False)

    class Meta(PentestUserDetailSerializer.Meta):
        fields = PentestUserDetailSerializer.Meta.fields + ['password']

    def validate_password(self, value):
        if value:
            validate_password(value, user=self.instance)
        return make_password(value)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if 'roles' not in attrs:
            attrs['roles'] = list(configuration.DEFAULT_USER_ROLES or [])
        return attrs


@extend_schema_field(PentestUserSerializer)
class RelatedUserSerializer(serializers.PrimaryKeyRelatedField):
    requires_context = True

    def __init__(self, user_serializer=PentestUserSerializer, **kwargs):
        self.user_serializer=user_serializer
        super().__init__(**kwargs)

    def get_queryset(self):
        qs = PentestUser.objects.all()
        if request := self.context.get('request'):
            qs = qs.only_permitted(request.user)
        return qs

    def use_pk_only_optimization(self):
        return False

    def to_internal_value(self, data):
        try:
            if isinstance(data, dict) and 'id' in data:
                return self.get_queryset().get(pk=data['id'])
            elif isinstance(data, str|UUID):
                return self.get_queryset().get(pk=data)
            else:
                return data
        except ObjectDoesNotExist as ex:
            raise serializers.ValidationError('Invalid user') from ex

    def to_representation(self, value):
        return self.user_serializer(value).to_representation(value)

    def get_choices(self, cutoff=None):
        queryset = self.get_queryset()
        if queryset is None:
            # Ensure that field.choices returns something sensible
            # even when accessed with a read-only field.
            return {}

        if cutoff is not None:
            queryset = queryset[:cutoff]

        return OrderedDict([(str(item.pk), self.display_value(item)) for item in queryset])


class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = PentestUser
        fields = ['password']

    def validate_password(self, value):
        validate_password(value, user=self.instance)

        if self.instance and self.instance.check_password(value):
            raise serializers.ValidationError('The new password must be different from the current password.')

        return value

    def update(self, instance, validated_data):
        instance.set_password(validated_data.pop('password'))
        instance = super().update(instance, {
            'must_change_password': False,
        } | validated_data)

        request = self.context.get('request')
        keep_session_key = None
        if (
            request
            and getattr(request, 'user', None) == instance
            and getattr(request, 'session', None)
            and request.session.session_key
        ):
            update_session_auth_hash(request, instance)
            keep_session_key = request.session.session_key

        Session.objects.clear_for_user(instance, keep_session_key=keep_session_key)
        return instance


class ResetPasswordSerializer(ChangePasswordSerializer):
    class Meta(ChangePasswordSerializer.Meta):
        fields = ChangePasswordSerializer.Meta.fields + ['must_change_password']


class ForgotPasswordSendSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def create(self, validated_data):
        user = PentestUser.objects \
            .filter(email=validated_data['email']) \
            .first()
        if user and user.email and user.is_active:
            async_to_sync(send_mail)(
                to=user.email,
                subject='SysReptor Password Reset',
                template_name='email/forgot_password.html',
                template_context={
                    'user': {
                        'id': str(user.id),
                        'email': user.email,
                        'username': user.username,
                        'name': user.name,
                    },
                    'confirmation_link': self.context['request'].build_absolute_uri(
                        f'/login/set-password/#user={user.id}&token={default_token_generator.make_token(user)}'),
                    'confirmation_link_valid_hours': settings.PASSWORD_RESET_TIMEOUT // 3600,
                },
            )
        return {}


class ForgotPasswordCheckSerializer(serializers.Serializer):
    user = OptionalPrimaryKeyRelatedField(queryset=PentestUser.objects.all(), pk_field=serializers.UUIDField())
    token = serializers.CharField()

    def validate(self, attrs):
        user = attrs.get('user')
        if not user or not default_token_generator.check_token(user, attrs.get('token')):
            raise serializers.ValidationError('The link is invalid or expired.')
        if not user.is_active:
            raise serializers.ValidationError('User is disabled or deleted.')

        return super().validate(attrs) | {
            'user': user,
        }


class MFAMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = MFAMethod
        fields = ['id', 'method_type', 'is_primary', 'name']
        read_only_fields = ['method_type']

    @transaction.atomic()
    def update(self, instance, validated_data):
        if validated_data.get('is_primary', False):
            self.instance.user.mfa_methods.update(is_primary=False)

        return super().update(instance, validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(trim_whitespace=False)
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

    def validate(self, attrs):
        try:
            user = PentestUser.objects.get(username=attrs['username'])
        except PentestUser.DoesNotExist:
            user = PentestUser()

        if not user.check_password(attrs['password']):
            raise serializers.ValidationError('Invalid username or password')

        if not user.is_active:
            raise serializers.ValidationError('User is disabled. Contact an administrator to reactivate it.')

        return user


class MFAMethodRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return self.context['request'].user.mfa_methods.all()


class LoginMFACodeSerializer(serializers.Serializer):
    id = MFAMethodRelatedField()
    code = serializers.CharField()

    def validate(self, attrs):
        mfa_method = attrs['id']
        if not mfa_method.verify_code(attrs['code']):
            PentestUser.objects.record_failed_mfa_attempt(user=self.context['request'].user)
            raise serializers.ValidationError('Invalid code')
        return mfa_method


class MFAMethodRegisterBeginSerializer(serializers.Serializer):
    pass


class MFAMethodRegisterSerializerBase(serializers.Serializer):
    @property
    def method_type(self):
        return None

    def validate(self, attrs):
        if self.instance.method_type != self.method_type:
            raise serializers.ValidationError('Invalid MFA Method')
        if self.instance.user != self.context['user']:
            raise serializers.ValidationError('Invalid user')
        return super().validate(attrs)

    def update(self, instance, validated_data):
        instance.is_primary = self.method_type != MFAMethodType.BACKUP and not instance.user.mfa_methods.filter(is_primary=True).exists()
        instance.save()
        return instance


class MFAMethodRegisterBackupCodesSerializer(MFAMethodRegisterSerializerBase):
    method_type = MFAMethodType.BACKUP


class MFAMethodRegisterTOTPSerializer(MFAMethodRegisterSerializerBase):
    method_type = MFAMethodType.TOTP
    code = serializers.CharField()

    def validate(self, attrs):
        if not self.instance.verify_code(attrs['code']):
            raise serializers.ValidationError('Invalid code')
        return attrs


class MFAMethodRegisterFIDO2Serializer(MFAMethodRegisterSerializerBase):
    method_type = MFAMethodType.FIDO2

    def update(self, instance, validated_data):
        try:
            instance = MFAMethod.objects.create_fido2_complete(instance=instance, response=self.initial_data, save=False)
        except ValueError as ex:
            if ex.args and len(ex.args) == 1 and isinstance(ex.args[0], str):
                raise serializers.ValidationError(ex.args[0], 'fido2') from ex
            else:
                raise ex
        return super().update(instance, validated_data)


class AuthIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthIdentity
        fields = ['id', 'created', 'updated', 'provider', 'identifier']

    def create(self, validated_data):
        return super().create(validated_data | {'user': self.context['user']})


class APITokenProjectSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()


def attach_api_token_resolved_projects(tokens):
    """
    Resolve token.projects (uuid[]) to {id, name} for all linked projects.
    Sets token.resolved_projects in-memory for APITokenProjectsField / APITokenSerializer.
    """
    from sysreptor.pentests.models import PentestProject

    tokens = list(tokens)
    project_ids = {pid for t in tokens if t.projects for pid in t.projects}
    by_id = {
        p.id: p
        for p in (
            PentestProject.objects.filter(id__in=project_ids).only('id', 'name')
            if project_ids else []
        )
    }
    for token in tokens:
        if token.projects is None:
            token.resolved_projects = None
        else:
            token.resolved_projects = [
                by_id.get(pid) or SimpleNamespace(id=pid, name='[unknown]')
                for pid in token.projects
            ]
    return tokens


@extend_schema_field(APITokenProjectSerializer(many=True, allow_null=True))
class APITokenProjectsField(serializers.Field):
    default_error_messages = {
        'not_a_list': 'Expected a list of items but got type "{input_type}".',
        'invalid_uuid': '"{value}" is not a valid UUID.',
        'not_member': 'You must be a direct member of every selected project.',
    }

    def get_attribute(self, instance):
        # Pass the token (instead of the raw project IDs) to to_representation,
        # because the bulk-resolved projects are attached to the token instance (also in list views).
        if super().get_attribute(instance) is None:
            return None
        return instance

    def to_representation(self, value):
        if value is None:
            return None
        if getattr(value, 'resolved_projects', None) is None:
            attach_api_token_resolved_projects([value])
        return [{'id': str(p.id), 'name': p.name} for p in value.resolved_projects]

    def to_internal_value(self, data):
        from sysreptor.pentests.models import PentestProject

        if data is None:
            return None
        if not isinstance(data, list):
            self.fail('not_a_list', input_type=type(data).__name__)

        ids = []
        for item in data:
            if isinstance(item, dict):
                item = item.get('id')
            try:
                ids.append(UUID(str(item)))
            except (TypeError, ValueError):
                self.fail('invalid_uuid', value=item)
        ids = list(dict.fromkeys(ids))  # dedupe, preserve order

        # Direct membership only — admins / project admins are not exempt.
        user = self.context['request'].user
        member_ids = set(
            PentestProject.objects
            .only_permitted(user)
            .filter(members__user=user, id__in=ids)
            .values_list('id', flat=True),
        )
        if set(ids) - member_ids:
            self.fail('not_member')
        return ids


class APITokenListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        return super().to_representation(attach_api_token_resolved_projects(data))


class APITokenSerializer(serializers.ModelSerializer):
    projects = APITokenProjectsField(allow_null=True, required=False)

    class Meta:
        model = APIToken
        fields = [
            'id', 'created', 'updated', 'name', 'expire_date', 'last_used', 'admin_permissions_enabled',
            'permissions', 'projects',
        ]
        list_serializer_class = APITokenListSerializer

    def to_representation(self, instance):
        if not hasattr(instance, 'resolved_projects'):
            attach_api_token_resolved_projects([instance])
        return super().to_representation(instance)

    def validate_expire_date(self, value):
        if value and value < timezone.now().date():
            raise serializers.ValidationError('Invalid expire date. It has to be in the future.')
        return value


class APITokenCreateSerializer(APITokenSerializer):
    token = serializers.ReadOnlyField(source='token_formatted')

    class Meta(APITokenSerializer.Meta):
        fields = APITokenSerializer.Meta.fields + ['token']

    def validate_admin_permissions_enabled(self, value):
        if value and not getattr(self.context['request'].user, 'is_admin', False):
            raise serializers.ValidationError('Cannot create API tokens with admin permissions enabled.')
        return value

    def validate_permissions(self, value):
        if value is None:
            return None
        if not isinstance(value, list):
            raise serializers.ValidationError('Expected a list of permissions or null.')
        unknown = [p for p in value if not expand_permissions([p])]
        if unknown:
            raise serializers.ValidationError(f'Unknown permissions: {", ".join(unknown)}')
        expanded = expand_permissions(value)
        # Compare against role permissions only. Ignore elevated admin permissions.
        user = self.context['request'].user
        user_perms = set(user.effective_permissions).intersection(get_role_permissions(user.roles))
        missing = {p.value for p in expanded} - user_perms
        if missing:
            raise serializers.ValidationError(f'Permissions exceed the current user permissions: {", ".join(sorted(missing))}')
        return [p.value for p in expanded]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        permissions = attrs.get('permissions', None)
        projects = attrs.get('projects', None)

        if attrs.get('admin_permissions_enabled') and (permissions is not None or projects is not None):
            raise serializers.ValidationError({'admin_permissions_enabled': 'Restricted tokens cannot enable admin permissions.'})

        if permissions is not None or projects is not None:
            if not license.is_professional():
                raise license.LicenseError('Restricted API tokens require a Professional license.')

            perm_set = expand_permissions(permissions or [])
            if projects is not None:
                # Project-restricted: only project.* except create/restore
                allowed = {
                    p for p in Permission
                    if p.value.startswith('project.') and p not in {Permission.PROJECT_CREATE, Permission.PROJECT_RESTORE}
                }
                if invalid := sorted(p.value for p in perm_set - allowed):
                    raise serializers.ValidationError({'permissions': f'Not allowed for project-restricted tokens: {", ".join(invalid)}.'})
                if Permission.PROJECT_READ not in perm_set:
                    raise serializers.ValidationError({'permissions': f'Project-restricted tokens require {Permission.PROJECT_READ}.'})
            else:
                if Permission.ARCHIVE_ALWAYS_ADD_ARCHIVING_KEY_TO_PROJECT in perm_set:
                    raise serializers.ValidationError({'permissions': f'{Permission.ARCHIVE_ALWAYS_ADD_ARCHIVING_KEY_TO_PROJECT} is not supported for API tokens.'})

        return attrs | {
            'permissions': permissions,
            'projects': projects,
        }

    def create(self, validated_data):
        return super().create(validated_data | {
            'user': self.context['user'],
        })

