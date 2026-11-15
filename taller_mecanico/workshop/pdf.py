"""Generación de reportes PDF del taller."""

from io import BytesIO

from django.template.loader import render_to_string
from django.utils import timezone


def construir_pdf(orden):
    """Renderiza el informe HTML y devuelve los bytes del PDF."""
    from xhtml2pdf import pisa

    analisis = orden.analisis_ia.first()
    contexto = {
        'orden': orden,
        'analisis': analisis,
        'evidencias': orden.evidencias.all(),
        'items_presupuesto': orden.items_presupuesto.all(),
        'total_presupuesto': orden.total_presupuesto,
        'fecha_generacion': timezone.localtime(),
    }
    html = render_to_string('pdf/informe_taller.html', contexto)
    salida = BytesIO()
    resultado = pisa.CreatePDF(src=html, dest=salida, encoding='utf-8')
    if resultado.err:
        raise RuntimeError('No se pudo generar el PDF del reporte.')
    return salida.getvalue()
