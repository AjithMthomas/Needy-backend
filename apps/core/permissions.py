"""Generic permissions shared across apps."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """Write access only to the object's owner (``owner_field`` attr or `owner`)."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, getattr(view, "owner_field", "owner"), None)
        return owner == request.user
