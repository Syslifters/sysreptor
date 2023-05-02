from rest_framework.permissions import IsAuthenticated

class IsSystemUser(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_system_user


class IsUserManagerOrSuperuser(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and (request.user.is_user_manager or request.user.is_superuser)

