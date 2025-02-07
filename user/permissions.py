from rest_framework import permissions


class IsSelfOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        # Разрешение на просмотр всегда
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj == request.user

class IsSelf(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user