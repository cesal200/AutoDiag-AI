from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import rol_requerido
from accounts.models import PerfilUsuario
from accounts.permissions import es_admin_operativo, puede_ver_orden
from workshop.models import OrdenFalla

from .forms import ConfiguracionDistribucionForm
from .models import ConfiguracionDistribucion
from .services import enviar_reporte as ejecutar_envio

from taller_mecanico.permissions import staff_required

@rol_requerido(PerfilUsuario.Rol.ADMIN, PerfilUsuario.Rol.ASESOR)
def configurar_distribucion(request, orden_id):
    orden = get_object_or_404(
        OrdenFalla.objects.select_related('cliente', 'vehiculo'), pk=orden_id
    )
    config, _ = ConfiguracionDistribucion.objects.get_or_create(orden=orden)
    form = ConfiguracionDistribucionForm(request.POST or None, instance=config)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Configuración de distribución guardada.')
        return redirect('orden_detalle', orden_id=orden.pk)

    return render(request, 'distribucion/configurar_distribucion.html', {
        'title': 'Configuración de distribución',
        'orden': orden,
        'form': form,
        'config': config,
    })


@login_required
@require_POST
def enviar_reporte(request, orden_id):
    if not es_admin_operativo(request.user):
        raise PermissionDenied
    orden = get_object_or_404(
        OrdenFalla.objects.select_related('cliente', 'vehiculo'), pk=orden_id
    )
    if not puede_ver_orden(request.user, orden):
        raise PermissionDenied

    resultado = ejecutar_envio(orden)
    if resultado['ok']:
        messages.success(request, resultado['mensaje'])
    else:
        messages.error(request, resultado['mensaje'])

    return render(request, 'distribucion/enviar_reporte.html', {
        'title': 'Envío de reporte',
        'orden': orden,
        'resultado': resultado,
    })
