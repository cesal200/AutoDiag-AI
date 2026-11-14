from django.shortcuts import render


def analizar_sintoma(request, orden_id):
    context = {
        'title': 'Diagnóstico IA',
        'orden_id': orden_id,
        'resultado': 'Se detectan síntomas compatibles con un problema de inyección y vibración del motor.',
    }
    return render(request, 'diagnostico_ia/analizar_sintoma.html', context)


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
