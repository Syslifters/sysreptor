from rest_framework import permissions


class UserViewSetPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        if view.action in ['self', 'change_password']:
            # Allow updating your own user
            return True
        return request.user.is_user_manager or request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        if obj == request.user:
            return True
        if view.action == 'reset_password' and obj.is_superuser and not request.user.is_superuser:
            # Prevent user_managers from resetting superuser password
            # This would be a privilege escalation
            return False
        return True

