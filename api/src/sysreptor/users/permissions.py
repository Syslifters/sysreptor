from datetime import datetime

from django.conf import settings
from django.utils import timezone
from rest_framework import authentication, exceptions, permissions

from sysreptor.users.auth import forbidden_with_apitoken_auth, is_restricted_api_token
from sysreptor.users.models import PentestUser
from sysreptor.users.roles import Permission
from sysreptor.utils import license
from sysreptor.utils.configuration import configuration


def _is_eligible_user(user) -> bool:
    if not user or getattr(user, 'is_anonymous', True):
        return False
    if getattr(user, 'is_system_user', False):
        return False
    return True


def check_sensitive_operation_timeout(request):
    """
    Check if the current session was fully authenticated (password + MFA) before a short period of time (settings.SENSITIVE_OPERATION_REAUTHENTICATION_TIMEOUT).
    """
    forbidden_with_apitoken_auth(request)
    try:
        reauth_time = datetime.fromisoformat(request.session.get('authentication_info', {}).get('reauth_time'))
        if reauth_time + settings.SENSITIVE_OPERATION_REAUTHENTICATION_TIMEOUT >= timezone.now():
            return True
    except (ValueError, TypeError):
        pass
    raise exceptions.PermissionDenied(detail='Autentication timeout for sensitive operation. Log in again.', code='reauth-required')


class UserSubresourcePermissions(permissions.BasePermission):
    @classmethod
    def has_read_permissions(cls, target_user, user) -> bool:
        if not _is_eligible_user(user):
            return False
        if user == target_user:
            return True
        if not user.has_permission(Permission.USER_EDIT):
            return False
        return True

    @classmethod
    def has_write_permissions(cls, target_user, user) -> bool:
        if not cls.has_read_permissions(target_user=target_user, user=user):
            return False
        if target_user == user:
            return True
        if not user.has_permission(Permission.USER_EDIT):
            return False
        if target_user.is_system_user:
            return False
        if target_user.is_superuser and not user.is_admin:
            return False
        return True

    def has_permission(self, request, view):
        target_user = view.get_user()
        if request.method in permissions.SAFE_METHODS:
            return self.has_read_permissions(target_user=target_user, user=request.user)
        return self.has_write_permissions(target_user=target_user, user=request.user)


class UserViewSetPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if view.action == 'destroy':
            return request.user.has_permission(Permission.USER_DELETE)
        elif view.action == 'create':
            return request.user.has_permission(Permission.USER_CREATE)
        elif view.action == 'self':
            # Restricted tokens may read the profile, but not update it.
            if is_restricted_api_token(request) and request.method not in permissions.SAFE_METHODS:
                return False
            return True
        elif view.action == 'change_password' and (configuration.LOCAL_USER_AUTH_ENABLED or not license.is_professional()):
            return check_sensitive_operation_timeout(request)
        elif view.action == 'enable_admin_permissions':
            return license.ProfessionalLicenseRequired().has_permission(request, view) and request.user.is_superuser and check_sensitive_operation_timeout(request)
        elif view.action == 'disable_admin_permissions':
            forbidden_with_apitoken_auth(request)
            return license.ProfessionalLicenseRequired().has_permission(request, view) and request.user.is_admin
        return request.user.has_permission(Permission.USER_EDIT)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if view.action == 'destroy':
            # Prevent deleting yourself
            if request.user == obj:
                return False
            # Prevent deleting superusers without admin permissions
            if obj.is_superuser and not request.user.is_admin:
                return False
            return True
        return UserSubresourcePermissions.has_write_permissions(target_user=obj, user=request.user)


class MFAMethodViewSetPermissons(permissions.BasePermission):
    def has_permission(self, request, view):
        forbidden_with_apitoken_auth(request)
        if not configuration.LOCAL_USER_AUTH_ENABLED and license.is_professional():
            return False

        user = view.get_user()
        if user == request.user:
            check_sensitive_operation_timeout(request)
            return True

        if request.method in permissions.SAFE_METHODS:
            return UserSubresourcePermissions.has_read_permissions(target_user=user, user=request.user)
        if view.action not in ['list', 'retrieve', 'destroy']:
            return False
        return UserSubresourcePermissions.has_write_permissions(target_user=user, user=request.user)


class AuthIdentityViewSetPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        user = view.get_user()
        if request.method in permissions.SAFE_METHODS:
            return UserSubresourcePermissions.has_read_permissions(target_user=user, user=request.user)

        # Users cannot edit their own identities; only user managers / admins can
        if not UserSubresourcePermissions.has_write_permissions(target_user=user, user=request.user):
            return False
        if not request.user.has_permission(Permission.USER_EDIT):
            return False
        return True


class APITokenViewSetPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        forbidden_with_apitoken_auth(request)
        user = view.get_user()
        if view.kwargs.get('pentestuser_pk') == 'self':
            return check_sensitive_operation_timeout(request)
        if request.method in permissions.SAFE_METHODS:
            return UserSubresourcePermissions.has_read_permissions(target_user=user, user=request.user)
        if view.action not in ['list', 'retrieve', 'destroy']:
            return False
        return UserSubresourcePermissions.has_write_permissions(target_user=user, user=request.user)


class MFALoginInProgressAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        if user_id := request.session.get('login_state', {}).get('user_id'):
            return PentestUser.objects.get(id=user_id), None


class RemoteUserAuthPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        return configuration.REMOTE_USER_AUTH_ENABLED and license.ProfessionalLicenseRequired().has_permission(request, view)


class LocalUserAuthPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        return configuration.LOCAL_USER_AUTH_ENABLED or not license.is_professional()


class ForgotPasswordPermissions(LocalUserAuthPermissions):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and \
              license.ProfessionalLicenseRequired().has_permission(request, view) and \
              configuration.FORGOT_PASSWORD_ENABLED and \
              configuration.LOCAL_USER_AUTH_ENABLED and \
              settings.EMAIL_HOST and \
              '*' not in settings.ALLOWED_HOSTS


class UserNotebookPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user == view.get_user():
            return True
        if request.user.is_admin and (request.method in permissions.SAFE_METHODS or view.action in ['export_pdf']):
            return True
        return False
