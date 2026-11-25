from django.core.exceptions import PermissionDenied


def org_atual(request):
    try:
        return request.user.perfil.organizacao
    except AttributeError as exc:
        raise PermissionDenied("Usuário sem perfil de organização.") from exc


def eh_admin(request):
    return request.user.perfil.papel == "admin"
