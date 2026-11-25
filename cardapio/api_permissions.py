from rest_framework.permissions import BasePermission, SAFE_METHODS


class PodeGerenciarRecurso(BasePermission):
    """Operadores atendem comandas; só administradores alteram o cadastro do restaurante."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        if view.basename in {"mesa", "prato", "combo"}:
            return request.user.perfil.papel == "admin"
        return True
