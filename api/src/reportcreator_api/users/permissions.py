from datetime import datetime
from django.conf import settings
from django.utils import timezone
from rest_framework import permissions, authentication, exceptions
from reportcreator_api.users.models import PentestUser


def check_sensitive_operation_timeout(request):
    """
    Check if the current session was fully authenticated (password + MFA) before a short period of time (settings.SENSITIVE_OPERATION_REAUTHENTICATION_TIMEOUT).
    """
    try: 
        reauth_time = datetime.fromisoformat(request.session.get('authentication_info', {}).get('reauth_time'))
        if reauth_time + settings.SENSITIVE_OPERATION_REAUTHENTICATION_TIMEOUT >= timezone.now():
            return True
    except (ValueError, TypeError):
        pass
    raise exceptions.PermissionDenied(detail='Autentication timeout for sensitive operation. Log in again.', code='reauth-required')


class UserViewSetPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        if view.action == 'self':
            # Allow updating your own user
            return True
        elif view.action == 'change_password':
            return check_sensitive_operation_timeout(request)
        return request.user.is_user_manager or request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if obj.is_system_user and obj != request.user:
            return False
        if view.action == 'reset_password':
            if obj.is_superuser and not request.user.is_superuser:
                # Prevent user_managers from resetting superuser password
                # This would be a privilege escalation
                return False
            check_sensitive_operation_timeout(request)
        return True


class MFAMethodViewSetPermissons(permissions.BasePermission):
    def has_permission(self, request, view):
        user = view.get_user()

        check_sensitive_operation_timeout(request)
        if user == request.user:
            return True
        elif (request.user.is_superuser or (request.user.is_user_manager and not user.is_superuser)) and not user.is_system_user and view.action in ['list', 'retrieve', 'destroy']:
            return True
        return False


class MFALoginInProgressAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        if user_id := request.session.get('login_state', {}).get('user_id'):
            return PentestUser.objects.get(id=user_id), None

