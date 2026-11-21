from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from taller_mecanico.permissions import staff_required


@login_required
@staff_required
def analizar_sintoma(request, orden_id):
    context = {
        'title': 'Diagnóstico IA',
        'orden_id': orden_id,
        'resultado': 'Se detectan síntomas compatibles con un problema de inyección y vibración del motor.',
    }
    return render(request, 'diagnostico_ia/analizar_sintoma.html', context)


@login_required
@staff_required
def resultado_analisis(request, analisis_id):
    context = {
        'title': 'Resultado del análisis',
        'analisis_id': analisis_id,
        'probabilidades': [
            {'causa': 'Sistema de alimentación', 'valor': '74%'},
            {'causa': 'Bujías / ignición', 'valor': '18%'},
            {'causa': 'Múltiples sensores', 'valor': '8%'},
        ],
    }
    return render(request, 'diagnostico_ia/resultado_analisis.html', context)
