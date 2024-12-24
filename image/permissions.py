from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        # Разрешение на просмотр всегда
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешение на изменение только автору изображения
        return obj.created_by == request.user
