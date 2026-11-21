from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.permissions import puede_ver_orden
from workshop.models import OrdenFalla

from .models import AnalisisSintoma
from .services import procesar_orden

from taller_mecanico.permissions import staff_required

@login_required
def analizar_sintoma(request, orden_id):
    orden = get_object_or_404(
        OrdenFalla.objects.select_related('vehiculo', 'cliente').prefetch_related(
            'evidencias', 'entradas_multimodales'
        ),
        pk=orden_id,
    )
    if not puede_ver_orden(request.user, orden):
        raise PermissionDenied

    if request.method == 'POST':
        resultado, analisis = procesar_orden(orden)
        messages.success(
            request,
            f'Análisis completado. Riesgo: {analisis.get_nivel_riesgo_display()}.',
        )
        return redirect('resultado_analisis', analisis_id=analisis.pk)

    return render(request, 'diagnostico_ia/analizar_sintoma.html', {
        'title': 'Diagnóstico IA',
        'orden': orden,
        'evidencias': orden.evidencias.all(),
        'analisis_previos': orden.analisis_ia.all()[:5],
    })


@login_required
def resultado_analisis(request, analisis_id):
    analisis = get_object_or_404(
        AnalisisSintoma.objects.select_related('orden', 'orden__vehiculo', 'orden__cliente'),
        pk=analisis_id,
    )
    if not puede_ver_orden(request.user, analisis.orden):
        raise PermissionDenied

    return render(request, 'diagnostico_ia/resultado_analisis.html', {
        'title': f'Resultado del análisis · {analisis.orden.codigo_orden}',
        'analisis': analisis,
        'orden': analisis.orden,
    })


@login_required
@require_POST
def descartar_analisis(request, analisis_id):
    analisis = get_object_or_404(AnalisisSintoma.objects.select_related('orden'), pk=analisis_id)
    if not puede_ver_orden(request.user, analisis.orden):
        raise PermissionDenied
    orden_id = analisis.orden_id
    analisis.delete()
    messages.info(request, 'Análisis eliminado.')
    return redirect(f"{reverse('orden_detalle', args=[orden_id])}")
