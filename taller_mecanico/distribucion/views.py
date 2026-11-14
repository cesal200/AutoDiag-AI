from django.shortcuts import render


def configurar_distribucion(request, orden_id):
    context = {
        'title': 'Configuración de distribución',
        'orden_id': orden_id,
        'canales': ['Telegram', 'Correo electrónico', 'Ambos'],
    }
    return render(request, 'distribucion/configurar_distribucion.html', context)


def enviar_reporte(request, orden_id):
    context = {
        'title': 'Enviar reporte',
        'orden_id': orden_id,
        'estado': 'Reporte listo para enviar',
    }
    return render(request, 'distribucion/enviar_reporte.html', context)
