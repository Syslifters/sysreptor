from rest_framework.permissions import IsAuthenticated

class IsSuperuser(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_superuser

