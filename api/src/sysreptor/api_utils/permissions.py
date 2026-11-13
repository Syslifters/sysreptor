from rest_framework.permissions import IsAuthenticated


class IsAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_admin


class BackupPermissions(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and \
            (request.user.is_admin or request.user.is_system_user)
