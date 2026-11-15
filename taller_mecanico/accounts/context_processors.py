from .permissions import es_admin_operativo, es_cliente, es_tecnico, obtener_perfil, rol_de


def rol_context(request):
    if not request.user.is_authenticated:
        return {}
    perfil = obtener_perfil(request.user)
    return {
        'rol_actual': rol_de(request.user),
        'rol_display': perfil.get_rol_display() if perfil else '',
        'es_admin_operativo': es_admin_operativo(request.user),
        'es_tecnico_actual': es_tecnico(request.user),
        'es_cliente_actual': es_cliente(request.user),
    }
