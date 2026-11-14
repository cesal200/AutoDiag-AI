from django.shortcuts import render


def orden_nueva(request):
    context = {
        'title': 'Nueva orden',
        'subtitle': 'Registra un vehículo y el síntoma del cliente.',
    }
    return render(request, 'workshop/orden_nueva.html', context)


def orden_lista(request):
    context = {
        'title': 'Órdenes activas',
        'ordenes': [
            {'id': 101, 'cliente': 'Ana García', 'vehiculo': 'Toyota Corolla', 'estado': 'Diagnóstico IA', 'prioridad': 'Alta'},
            {'id': 102, 'cliente': 'Luis Pérez', 'vehiculo': 'Honda Civic', 'estado': 'En taller', 'prioridad': 'Media'},
            {'id': 103, 'cliente': 'Elena Torres', 'vehiculo': 'BMW X5', 'estado': 'Listo para entrega', 'prioridad': 'Baja'},
        ],
    }
    return render(request, 'workshop/orden_lista.html', context)


def orden_detalle(request, orden_id):
    context = {
        'title': f'Orden #{orden_id}',
        'orden_id': orden_id,
        'vehiculo': 'Toyota Corolla 2021',
        'cliente': 'Ana García',
        'sintoma': 'Vibración al acelerar y luz de motor encendida',
        'riesgo': 'Precaución',
    }
    return render(request, 'workshop/orden_detalle.html', context)


def generar_pdf(request, orden_id):
    context = {
        'title': f'PDF de orden #{orden_id}',
        'orden_id': orden_id,
        'cliente': 'Ana García',
        'fecha': '14/11/2026',
    }
    return render(request, 'workshop/generar_pdf.html', context)
