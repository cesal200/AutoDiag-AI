"""Entrega de reportes PDF por Telegram y correo electrónico."""

import json
import os
import time
import urllib.request
import uuid

from django.conf import settings
from django.core.mail import EmailMessage

from workshop.pdf import construir_pdf

from .models import ConfiguracionDistribucion, EnvioReportes


class DistribucionError(Exception):
    pass


def _multipart(fields, files):
    boundary = f'----AutoDiagReport{uuid.uuid4().hex}'
    lineas = []
    for nombre, valor in fields.items():
        lineas.extend([
            f'--{boundary}'.encode(),
            f'Content-Disposition: form-data; name="{nombre}"'.encode(),
            b'',
            str(valor).encode(),
        ])
    for nombre, (filename, contenido, content_type) in files.items():
        lineas.extend([
            f'--{boundary}'.encode(),
            f'Content-Disposition: form-data; name="{nombre}"; filename="{filename}"'.encode(),
            f'Content-Type: {content_type}'.encode(),
            b'',
            contenido,
        ])
    lineas.append(f'--{boundary}--'.encode())
    lineas.append(b'')
    return boundary, b'\r\n'.join(lineas)


def enviar_telegram(pdf, nombre_archivo, chat_id, caption=''):
    token = os.environ.get('TELEGRAM_BOT_TOKEN') or getattr(
        settings, 'TELEGRAM_BOT_TOKEN', ''
    )
    if not token:
        raise DistribucionError('TELEGRAM_BOT_TOKEN no está configurado.')
    if not chat_id:
        raise DistribucionError('No se indicó el chat de Telegram.')

    boundary, body = _multipart(
        {'chat_id': chat_id, 'caption': caption},
        {'document': (nombre_archivo, pdf, 'application/pdf')},
    )
    request = urllib.request.Request(
        f'https://api.telegram.org/bot{token}/sendDocument',
        data=body,
        method='POST',
    )
    request.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception as exc:
        raise DistribucionError(f'Telegram rechazó el envío: {exc}') from exc
    if not data.get('ok'):
        raise DistribucionError(data.get('description', 'Telegram devolvió un error.'))


def enviar_email(pdf, nombre_archivo, destinatario, asunto, cuerpo):
    if not destinatario:
        raise DistribucionError('No se indicó el correo de destino.')
    mensaje = EmailMessage(asunto, cuerpo, to=[destinatario])
    mensaje.attach(nombre_archivo, pdf, 'application/pdf')
    enviados = mensaje.send(fail_silently=False)
    if not enviados:
        raise DistribucionError('El servidor SMTP no aceptó el mensaje.')


def _registrar(orden, metodo, estado, error=''):
    return EnvioReportes.objects.create(
        orden=orden,
        metodo=metodo,
        estado=estado,
        mensaje_error=error,
    )


def _con_reintentos(orden, metodo, funcion, max_intentos=3):
    errores = []
    for intento in range(1, max_intentos + 1):
        try:
            funcion()
        except Exception as exc:
            errores.append(str(exc))
            _registrar(orden, metodo, 'Fallido', str(exc))
            if intento < max_intentos:
                time.sleep(min(0.2 * intento, 1))
        else:
            _registrar(orden, metodo, 'ENVIADO')
            return True, ''
    return False, errores[-1] if errores else 'Error desconocido'


def enviar_reporte(orden, config=None, max_intentos=3):
    """Envía el reporte según la configuración y devuelve un resumen."""
    config = config or getattr(orden, 'config_distribucion', None)
    if config is None:
        config, _ = ConfiguracionDistribucion.objects.get_or_create(orden=orden)

    if config.metodo == 'NINGUNO':
        return {
            'ok': True,
            'omitido': True,
            'mensaje': 'La orden está configurada sin envío automático. Usa la descarga local.',
            'resultados': [],
        }

    pdf = construir_pdf(orden)
    nombre = f'reporte-{orden.codigo_orden}.pdf'
    asunto = f'Reporte {orden.codigo_orden} - {orden.vehiculo}'
    cuerpo = (
        f'Reporte de taller {orden.codigo_orden}\n'
        f'Vehículo: {orden.vehiculo}\n'
        f'Estado: {orden.get_estado_display()}\n'
        f'Cliente: {orden.cliente_efectivo}\n'
    )
    caption = f'{orden.codigo_orden} · {orden.vehiculo} · {orden.get_estado_display()}'

    resultados = []
    if config.metodo in {'TELEGRAM', 'AMBOS'}:
        ok, error = _con_reintentos(
            orden,
            'TELEGRAM',
            lambda: enviar_telegram(pdf, nombre, config.chat_telegram_id, caption),
            max_intentos,
        )
        resultados.append({'canal': 'Telegram', 'ok': ok, 'error': error})

    if config.metodo in {'EMAIL', 'AMBOS'}:
        destino = config.email_destino or (orden.cliente.email if orden.cliente_id else '')
        ok, error = _con_reintentos(
            orden,
            'EMAIL',
            lambda: enviar_email(pdf, nombre, destino, asunto, cuerpo),
            max_intentos,
        )
        resultados.append({'canal': 'Email', 'ok': ok, 'error': error})

    return {
        'ok': all(resultado['ok'] for resultado in resultados),
        'omitido': False,
        'mensaje': 'Envío completado.' if all(r['ok'] for r in resultados) else 'Algún canal falló.',
        'pdf': pdf,
        'nombre_archivo': nombre,
        'resultados': resultados,
    }
