from rest_framework.permissions import BasePermission

class IsAdminUserOrSuperuser(BasePermission):
    """
    Custom permission to only allow admins or superusers
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_staff or request.user.is_superuser