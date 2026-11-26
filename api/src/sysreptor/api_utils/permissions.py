from rest_framework.permissions import IsAuthenticated

from sysreptor.users.auth import is_restricted_api_token


class IsAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_admin


class BackupPermissions(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and \
            (request.user.is_admin or request.user.is_system_user)


class SpellcheckPermissions(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if is_restricted_api_token(request):
            return False
        return True
