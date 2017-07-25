from rest_framework import permissions
from rest_framework.compat import is_authenticated


class IsSuperuserOrReadOnly(permissions.BasePermission):
    """
    Allows access only to super users.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user and
            is_authenticated(request.user) and
            request.user.is_superuser
        )
