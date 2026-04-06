from rest_framework import permissions


class IsInstructor(permissions.BasePermission):
    
    """
    solo entrar rol instructor
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.rol == 'instructor')
    
    
    
# el instructor elimina tareas