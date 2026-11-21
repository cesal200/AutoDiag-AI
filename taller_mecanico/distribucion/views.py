from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.decorators import rol_requerido
from accounts.models import PerfilUsuario
from accounts.permissions import es_admin_operativo, puede_ver_orden
from workshop.models import OrdenFalla

from .forms import ConfiguracionDistribucionForm, ConfiguracionRemitenteForm
from .models import ConfiguracionDistribucion, ConfiguracionRemitente
from .services import enviar_reporte as ejecutar_envio
from .services import (
    construir_mensaje_whatsapp,
    construir_url_whatsapp,
    obtener_telefono_whatsapp,
)

@rol_requerido(PerfilUsuario.Rol.ADMIN, PerfilUsuario.Rol.ASESOR)
def configurar_distribucion(request, orden_id):
    orden = get_object_or_404(
        OrdenFalla.objects.select_related('cliente', 'vehiculo'), pk=orden_id
    )
    config, _ = ConfiguracionDistribucion.objects.get_or_create(orden=orden)
    initial = {}
    if not config.email_destino and orden.cliente_id:
        initial['email_destino'] = orden.cliente.email
    if not config.telefono_whatsapp:
        initial['telefono_whatsapp'] = obtener_telefono_whatsapp(orden)
    form = ConfiguracionDistribucionForm(
        request.POST or None,
        instance=config,
        initial=initial,
    )
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


@rol_requerido(PerfilUsuario.Rol.ADMIN)
def configurar_remitente(request):
    config = ConfiguracionRemitente.obtener()
    form = ConfiguracionRemitenteForm(request.POST or None, instance=config)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Los datos de contacto del taller se guardaron.')
        return redirect('configurar_remitente')

    return render(request, 'distribucion/configurar_remitente.html', {
        'title': 'Contacto del taller',
        'form': form,
        'email_predeterminado': settings.DEFAULT_FROM_EMAIL,
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

    config, _ = ConfiguracionDistribucion.objects.get_or_create(orden=orden)
    enlace_seguimiento = ''
    enlace_pdf = ''
    if orden.token_publico and orden.token_vigente:
        enlace_seguimiento = request.build_absolute_uri(
            reverse('seguimiento_publico', args=[orden.token_publico])
        )
        enlace_pdf = request.build_absolute_uri(
            reverse('descargar_pdf_publico', args=[orden.token_publico])
        )
    resultado = ejecutar_envio(
        orden,
        config=config,
        enlace_seguimiento=enlace_seguimiento,
        enlace_pdf=enlace_pdf,
    )
    if resultado.get('requiere_accion'):
        resultado['url_whatsapp'] = reverse('abrir_whatsapp', args=[orden.pk])
        messages.info(request, resultado['mensaje'])
    elif resultado['ok']:
        messages.success(request, resultado['mensaje'])
    else:
        messages.error(request, resultado['mensaje'])

    return render(request, 'distribucion/enviar_reporte.html', {
        'title': 'Envío de reporte',
        'orden': orden,
        'resultado': resultado,
    })


@login_required
def abrir_whatsapp(request, orden_id):
    orden = get_object_or_404(
        OrdenFalla.objects.select_related(
            'cliente', 'vehiculo', 'mecanico_asignado', 'taller'
        ).prefetch_related('items_presupuesto'),
        pk=orden_id,
    )
    if not puede_ver_orden(request.user, orden):
        raise PermissionDenied

    config = getattr(orden, 'config_distribucion', None)
    telefono = obtener_telefono_whatsapp(orden, config)
    if not telefono:
        messages.error(
            request,
            'No hay teléfono de WhatsApp configurado. Puedes agregarlo en Configurar distribución.',
        )
        return redirect('configurar_distribucion', orden_id=orden.pk)

    enlace = request.build_absolute_uri(
        reverse('seguimiento_publico', args=[orden.token_publico])
    ) if orden.token_publico and orden.token_vigente else ''
    enlace_pdf = request.build_absolute_uri(
        reverse('descargar_pdf_publico', args=[orden.token_publico])
    ) if orden.token_publico and orden.token_vigente else ''
    contacto = ConfiguracionRemitente.obtener()
    mensaje = construir_mensaje_whatsapp(
        orden,
        enlace_seguimiento=enlace,
        enlace_pdf=enlace_pdf,
        telefono_taller=contacto.telefono_whatsapp,
    )
    return redirect(construir_url_whatsapp(telefono, mensaje))
