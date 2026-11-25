from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required


def papel_obrigatorio(*papeis):
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            try:
                permitido = request.user.perfil.papel in papeis
            except AttributeError:
                permitido = False
            if not permitido:
                raise PermissionDenied("Você não tem permissão para esta ação.")
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
