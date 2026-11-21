"""Entrega de reportes PDF por Telegram y correo electrónico."""

import json
import os
import time
import urllib.request
import uuid
from urllib.parse import quote

from django.conf import settings
from django.core.mail import EmailMessage

from workshop.pdf import construir_pdf

from .models import (
    ConfiguracionDistribucion,
    ConfiguracionRemitente,
    EnvioReportes,
)


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


def enviar_email(pdf, nombre_archivo, destinatario, asunto, cuerpo, from_email=None):
    if not destinatario:
        raise DistribucionError('No se indicó el correo de destino.')
    mensaje = EmailMessage(asunto, cuerpo, from_email=from_email, to=[destinatario])
    mensaje.attach(nombre_archivo, pdf, 'application/pdf')
    enviados = mensaje.send(fail_silently=False)
    if not enviados:
        raise DistribucionError('El servidor SMTP no aceptó el mensaje.')


def obtener_telefono_whatsapp(orden, config=None):
    if config and config.telefono_whatsapp:
        return config.telefono_whatsapp
    if orden.telefono_cliente_walkin:
        return orden.telefono_cliente_walkin
    if orden.cliente_id:
        perfil = getattr(orden.cliente, 'perfil', None)
        if perfil and perfil.telefono:
            return perfil.telefono
    return ''


def construir_mensaje_whatsapp(
    orden,
    enlace_seguimiento='',
    enlace_pdf='',
    telefono_taller='',
):
    presupuesto = orden.total_presupuesto
    aprobados = orden.items_presupuesto.filter(aprobado_cliente=True).count()
    pendientes = orden.items_presupuesto.count() - aprobados
    partes = [
        'Hola, te compartimos el estado de tu orden.',
        '',
        f'Orden: {orden.codigo_orden}',
        f'Ticket / seguimiento: {orden.ticket}',
        f'Vehículo: {orden.vehiculo}',
        f'Placa: {orden.vehiculo.placa}',
        f'Estado: {orden.get_estado_display()}',
        f'Mecánico: {orden.mecanico_asignado.get_full_name() if orden.mecanico_asignado and orden.mecanico_asignado.get_full_name() else (orden.mecanico_asignado.get_username() if orden.mecanico_asignado else "Sin asignar")}',
        f'Presupuesto total: ${presupuesto}',
        f'Ítems aprobados: {aprobados}',
        f'Ítems pendientes: {pendientes}',
    ]
    if enlace_seguimiento:
        partes.extend(['', f'Seguimiento: {enlace_seguimiento}'])
    if enlace_pdf:
        partes.append(f'Reporte PDF: {enlace_pdf}')
    if telefono_taller:
        partes.append(f'Contacto del taller: {telefono_taller}')
    partes.extend(['', 'AutoDiag AI · Taller mecánico'])
    return '\n'.join(partes)


def construir_url_whatsapp(telefono, mensaje):
    numero = ''.join(caracter for caracter in str(telefono) if caracter.isdigit())
    if not numero:
        raise DistribucionError('No se indicó un teléfono válido para WhatsApp.')
    return f'https://wa.me/{numero}?text={quote(mensaje)}'


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


def enviar_reporte(
    orden,
    config=None,
    max_intentos=3,
    enlace_seguimiento='',
    enlace_pdf='',
):
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
    if config.metodo == 'WHATSAPP':
        return {
            'ok': False,
            'omitido': False,
            'requiere_accion': True,
            'mensaje': (
                'WhatsApp Web no envía el mensaje ni adjunta archivos automáticamente. '
                'Abre la conversación y confirma el envío del enlace seguro al PDF.'
            ),
            'resultados': [],
        }

    pdf = construir_pdf(orden)
    nombre = f'reporte-{orden.codigo_orden}.pdf'
    asunto = f'Reporte {orden.codigo_orden} - {orden.vehiculo}'
    remitente = ConfiguracionRemitente.obtener()
    cuerpo = (
        f'Reporte del taller - AutoDiag AI\n\n'
        f'Orden: {orden.codigo_orden}\n'
        f'Ticket / seguimiento: {orden.ticket}\n'
        f'Cliente: {orden.cliente_efectivo}\n'
        f'Vehículo: {orden.vehiculo}\n'
        f'Placa: {orden.vehiculo.placa}\n'
        f'Estado: {orden.get_estado_display()}\n'
        f'Mecánico: {orden.mecanico_asignado.get_full_name() if orden.mecanico_asignado and orden.mecanico_asignado.get_full_name() else (orden.mecanico_asignado.get_username() if orden.mecanico_asignado else "Sin asignar")}\n'
        f'Presupuesto total: ${orden.total_presupuesto}\n'
        f'Ítems aprobados: {orden.items_presupuesto.filter(aprobado_cliente=True).count()}\n'
        f'Ítems pendientes: {orden.items_presupuesto.filter(aprobado_cliente=False).count()}\n'
        f'Enlace de seguimiento: {enlace_seguimiento or "No disponible"}\n'
        f'Descarga del reporte PDF: {enlace_pdf or "No disponible"}\n'
        f'Contacto del taller: {remitente.telefono_whatsapp or "No disponible"}\n'
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

    if config.metodo in {'EMAIL', 'AMBOS', 'WHATSAPP_EMAIL'}:
        destino = config.email_destino or (orden.cliente.email if orden.cliente_id else '')
        ok, error = _con_reintentos(
            orden,
            'EMAIL',
            lambda: enviar_email(
                pdf,
                nombre,
                destino,
                asunto,
                cuerpo,
                remitente.email_remitente or settings.DEFAULT_FROM_EMAIL,
            ),
            max_intentos,
        )
        resultados.append({'canal': 'Email', 'ok': ok, 'error': error})

    if config.metodo == 'WHATSAPP_EMAIL':
        resultados.append({
            'canal': 'WhatsApp Web',
            'ok': False,
            'error': 'Requiere confirmación manual; usa el botón para abrir WhatsApp Web.',
        })

    resultados_automaticos = [
        resultado for resultado in resultados
        if resultado['canal'] != 'WhatsApp Web'
    ]
    correo_enviado = any(
        resultado['canal'] == 'Email' and resultado['ok']
        for resultado in resultados
    )
    return {
        'ok': bool(resultados_automaticos)
        and all(resultado['ok'] for resultado in resultados_automaticos),
        'omitido': False,
        'requiere_accion': config.metodo == 'WHATSAPP_EMAIL',
        'correo_enviado': correo_enviado,
        'mensaje': (
            (
                'Correo enviado con el PDF adjunto; WhatsApp requiere confirmación manual.'
                if correo_enviado
                else 'No se pudo enviar el correo; WhatsApp requiere confirmación manual.'
            )
            if config.metodo == 'WHATSAPP_EMAIL'
            else 'Envío completado.' if all(r['ok'] for r in resultados)
            else 'Algún canal falló.'
        ),
        'pdf': pdf,
        'nombre_archivo': nombre,
        'resultados': resultados,
    }
