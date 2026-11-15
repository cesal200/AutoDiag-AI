from .models import PerfilUsuario

ROLES_ADMIN_OPERATIVO = {PerfilUsuario.Rol.ADMIN, PerfilUsuario.Rol.ASESOR}
ROLES_TECNICO = {PerfilUsuario.Rol.MECANICO}
ROLES_CLIENTE = {PerfilUsuario.Rol.CLIENTE}


def obtener_perfil(user):
    """Devuelve el perfil del usuario, creándolo si no existe."""
    if not user or not user.is_authenticated:
        return None
    perfil, _ = PerfilUsuario.objects.get_or_create(
        user=user,
        defaults={'rol': PerfilUsuario.Rol.ADMIN if user.is_superuser else PerfilUsuario.Rol.CLIENTE},
    )
    return perfil


def rol_de(user):
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return PerfilUsuario.Rol.ADMIN
    perfil = obtener_perfil(user)
    return perfil.rol if perfil else None


def es_admin_operativo(user):
    return user.is_authenticated and (
        user.is_superuser or rol_de(user) in ROLES_ADMIN_OPERATIVO
    )


def es_tecnico(user):
    return user.is_authenticated and rol_de(user) in ROLES_TECNICO


def es_cliente(user):
    return user.is_authenticated and rol_de(user) in ROLES_CLIENTE


def puede_ver_orden(user, orden):
    if not user.is_authenticated:
        return False
    if es_admin_operativo(user):
        return True
    return orden.cliente_id == user.id or orden.mecanico_asignado_id == user.id


def puede_editar_estado(user, orden):
    if es_admin_operativo(user):
        return True
    return es_tecnico(user) and orden.mecanico_asignado_id == user.id
