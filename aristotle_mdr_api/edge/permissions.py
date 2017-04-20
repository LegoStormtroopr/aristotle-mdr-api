from rest_framework import permissions

class IsSuperuser(permissions.BasePermission):
    """
    Allows access only to super users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_superuser
