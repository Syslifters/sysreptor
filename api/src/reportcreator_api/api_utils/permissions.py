from rest_framework.permissions import IsAuthenticated


class IsAdminOrSystem(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and \
            (request.user.is_system_user or request.user.is_admin)


class IsUserManagerOrSuperuserOrSystem(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and \
            (request.user.is_user_manager or request.user.is_superuser or request.user.is_system_user)

