from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from taller_mecanico.permissions import staff_required

from .forms import MensajeOrdenForm, OrdenClienteForm, OrdenGestionForm
from .models import EvidenciaSintoma, MensajeOrden, OrdenFalla


def _verificar_acceso_chat(usuario, orden):
    if not (
        usuario.is_staff
        or orden.cliente_id == usuario.pk
        or orden.mecanico_asignado_id == usuario.pk
    ):
        raise PermissionDenied


@login_required
def orden_cliente_nueva(request):
    form = OrdenClienteForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            orden = OrdenFalla.objects.create(
                cliente=request.user,
                taller='AutoDiag AI',
                vehiculo=form.cleaned_data['vehiculo'],
                placa=form.cleaned_data['placa'],
                kilometraje_ingreso=form.cleaned_data['kilometraje_ingreso'],
            )
            EvidenciaSintoma.objects.create(
                orden=orden,
                narrativa_cliente=form.cleaned_data['sintoma'],
            )
        return redirect('cliente_orden_lista')

    return render(request, 'workshop/cliente_orden_nueva.html', {
        'form': form,
        'title': 'Nueva orden de servicio',
    })


@login_required
def orden_cliente_lista(request):
    ordenes = OrdenFalla.objects.filter(
        cliente=request.user,
    ).exclude(
        estado='ENTREGADO',
    ).order_by('-pk')
    return render(request, 'workshop/cliente_orden_lista.html', {
        'ordenes': ordenes,
        'title': 'Mis órdenes activas',
    })


@login_required
def orden_cliente_detalle(request, orden_id):
    orden = get_object_or_404(
        OrdenFalla.objects.select_related('mecanico_asignado'),
        pk=orden_id,
        cliente=request.user,
    )
    evidencia = orden.evidencias.order_by('-pk').first()
    return render(request, 'workshop/cliente_orden_detalle.html', {
        'orden': orden,
        'sintoma': evidencia.narrativa_cliente if evidencia else '',
        'mensaje_form': MensajeOrdenForm(),
        'mensajes': orden.mensajes.select_related('autor').all(),
        'usuario_id': request.user.pk,
    })


@login_required
@require_GET
def mensajes_orden(request, orden_id):
    orden = get_object_or_404(
        OrdenFalla.objects.select_related('cliente', 'mecanico_asignado'),
        pk=orden_id,
    )
    _verificar_acceso_chat(request.user, orden)
    response = render(request, 'workshop/_mensajes_orden.html', {
        'mensajes': orden.mensajes.select_related('autor').all(),
        'usuario_id': request.user.pk,
    })
    response['Cache-Control'] = 'no-store'
    return response


@login_required
@require_POST
def enviar_mensaje_orden(request, orden_id):
    orden = get_object_or_404(OrdenFalla, pk=orden_id)
    _verificar_acceso_chat(request.user, orden)
    form = MensajeOrdenForm(request.POST)
    if form.is_valid():
        MensajeOrden.objects.create(
            orden=orden,
            autor=request.user,
            contenido=form.cleaned_data['contenido'],
        )
        messages.success(request, 'Mensaje enviado.')
    else:
        messages.error(request, 'Escribe un mensaje válido de hasta 4000 caracteres.')

    if request.user.is_staff:
        return redirect('orden_detalle', orden_id=orden.pk)
    return redirect('cliente_orden_detalle', orden_id=orden.pk)


@login_required
@staff_required
def orden_nueva(request):
    context = {
        'title': 'Nueva orden',
        'subtitle': 'Registra un vehículo y el síntoma del cliente.',
    }
    return render(request, 'workshop/orden_nueva.html', context)


@login_required
@staff_required
def orden_lista(request):
    ordenes = OrdenFalla.objects.select_related('cliente').exclude(
        estado='ENTREGADO',
    ).order_by('-pk')
    return render(request, 'workshop/orden_lista.html', {
        'title': 'Órdenes activas',
        'ordenes': ordenes,
    })


@login_required
@staff_required
def orden_detalle(request, orden_id):
    orden = get_object_or_404(
        OrdenFalla.objects.select_related('cliente', 'mecanico_asignado').prefetch_related('evidencias'),
        pk=orden_id,
    )
    if request.method == 'POST':
        form = OrdenGestionForm(request.POST, instance=orden)
        if form.is_valid():
            form.save()
            messages.success(request, 'La orden se actualizó correctamente.')
            return redirect('orden_detalle', orden_id=orden.pk)
    else:
        form = OrdenGestionForm(instance=orden)

    evidencia = orden.evidencias.order_by('-pk').first()
    return render(request, 'workshop/orden_detalle.html', {
        'title': f'Orden {orden.codigo_orden}',
        'orden': orden,
        'orden_id': orden.pk,
        'sintoma': evidencia.narrativa_cliente if evidencia else '',
        'form': form,
        'mensaje_form': MensajeOrdenForm(),
        'mensajes': orden.mensajes.select_related('autor').all(),
        'usuario_id': request.user.pk,
    })


@login_required
@staff_required
def generar_pdf(request, orden_id):
    context = {
        'title': f'PDF de orden #{orden_id}',
        'orden_id': orden_id,
        'cliente': 'Ana García',
        'fecha': '14/11/2026',
    }
    return render(request, 'workshop/generar_pdf.html', context)
