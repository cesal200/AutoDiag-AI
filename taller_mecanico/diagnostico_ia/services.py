"""Servicio de pre-diagnóstico multimodal.

El motor local usa una taxonomía determinista para funcionar sin servicios
externos. Si existe ``OPENAI_API_KEY`` se intenta enriquecer la transcripción de
audio y la descripción de imágenes; ante cualquier error se usa el resultado
local para no bloquear la recepción del vehículo.
"""

import base64
import json
import os
import uuid
from statistics import mean

from .models import AnalisisSintoma
from .taxonomy import (
    CAUSAS_GENERALES,
    PALABRAS_RIESGO_ALTO,
    PALABRAS_RIESGO_BAJO,
    TAXONOMIA,
    componentes_detectados,
    normalizar_texto,
)

RIESGO_PRIORIDAD = {'PUEDE_RODAR': 1, 'PRECAUCION': 2, 'NO_MOVER_GRUA': 3}
RIESGO_POR_DEFECTO = 'PRECAUCION'


def _openai_api_key():
    return os.environ.get('OPENAI_API_KEY', '').strip()


def _multipart(fields, files):
    boundary = f'----AutoDiag{uuid.uuid4().hex}'
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


def _post_json(url, payload, headers=None):
    import urllib.request

    data = json.dumps(payload).encode('utf-8')
    request = urllib.request.Request(url, data=data, method='POST')
    request.add_header('Content-Type', 'application/json')
    for clave, valor in (headers or {}).items():
        request.add_header(clave, valor)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode('utf-8'))


def transcribir_audio(archivo):
    """Transcribe una nota de voz. Devuelve texto, confianza y advertencia."""
    if not archivo:
        return {'texto': '', 'confianza': 0.0, 'advertencia': ''}

    api_key = _openai_api_key()
    if not api_key:
        return {
            'texto': '',
            'confianza': 0.0,
            'advertencia': 'Transcripción automática desactivada; se usará la narrativa escrita.',
        }

    try:
        contenido = archivo.read()
        if hasattr(archivo, 'seek'):
            archivo.seek(0)
        boundary, body = _multipart(
            {'model': 'whisper-1', 'language': 'es'},
            {'file': (os.path.basename(archivo.name), contenido, 'audio/mpeg')},
        )
        import urllib.request

        request = urllib.request.Request(
            'https://api.openai.com/v1/audio/transcriptions',
            data=body,
            method='POST',
        )
        request.add_header('Authorization', f'Bearer {api_key}')
        request.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode('utf-8'))
        texto = (data.get('text') or '').strip()
        return {
            'texto': texto,
            'confianza': 0.9 if texto else 0.0,
            'advertencia': '',
        }
    except Exception as exc:
        return {
            'texto': '',
            'confianza': 0.0,
            'advertencia': f'No se pudo transcribir el audio: {exc}',
        }


def analizar_imagen(imagen):
    """Describe una imagen de evidencia usando IA opcional o análisis local."""
    if not imagen:
        return {'descripcion': '', 'confianza': 0.0}

    api_key = _openai_api_key()
    if api_key:
        try:
            with imagen.open('rb') as archivo:
                contenido = base64.b64encode(archivo.read()).decode('ascii')
            data = _post_json(
                'https://api.openai.com/v1/chat/completions',
                {
                    'model': 'gpt-4o-mini',
                    'messages': [{
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': (
                                    'Describe en español los síntomas mecánicos visibles en esta '
                                    'foto de un vehículo. Sé breve y técnico.'
                                ),
                            },
                            {
                                'type': 'image_url',
                                'image_url': {'url': f'data:image/jpeg;base64,{contenido}'},
                            },
                        ],
                    }],
                    'max_tokens': 180,
                },
                {'Authorization': f'Bearer {api_key}'},
            )
            descripcion = data['choices'][0]['message']['content'].strip()
            return {'descripcion': descripcion, 'confianza': 0.85}
        except Exception:
            pass

    try:
        from PIL import Image

        with Image.open(imagen) as foto:
            ancho, alto = foto.size
            gris = foto.convert('L').resize((64, 64))
            brillo = round(mean(gris.getdata()), 1)
        return {
            'descripcion': (
                f'Imagen de {ancho}x{alto} px con brillo medio {brillo}/255. '
                'No se detectan elementos adicionales sin un modelo de visión externo.'
            ),
            'confianza': 0.35,
        }
    except Exception:
        return {'descripcion': '', 'confianza': 0.0}


def normalizar_sintomas(texto):
    """Convierte texto libre en síntomas normalizados con identificadores."""
    detectados = componentes_detectados(texto)
    if not detectados:
        return [{
            'codigo': 'GENERAL-01',
            'componente': 'General',
            'sintoma': 'Síntoma no clasificado',
            'gravedad': 'PRECAUCION',
        }]

    normalizados = []
    for clave, datos, coincidencias in detectados:
        for indice, sintoma in enumerate(dict.fromkeys(coincidencias), start=1):
            normalizados.append({
                'codigo': f'{clave.upper()}-{indice:02d}',
                'componente': datos['etiqueta'],
                'sintoma': sintoma,
                'gravedad': datos['riesgo'],
            })
    return normalizados


def _ajuste_vehiculo(vehiculo):
    ajustes = {}
    if not vehiculo:
        return ajustes
    if getattr(vehiculo, 'anio', 0) and vehiculo.anio < 2010:
        ajustes['Desgaste natural de componentes'] = 5
    return ajustes


def rankear_causas(normalizados, vehiculo=None):
    """Genera exactamente tres causas ordenadas por probabilidad descendente."""
    puntajes = {}
    for sintoma in normalizados:
        for clave, datos in TAXONOMIA.items():
            if sintoma['componente'] == datos['etiqueta']:
                for causa, peso in datos['causas']:
                    puntajes[causa] = puntajes.get(causa, 0) + peso
                break

    for causa, ajuste in _ajuste_vehiculo(vehiculo).items():
        puntajes[causa] = puntajes.get(causa, 0) + ajuste

    if len(puntajes) < 3:
        for causa, peso in CAUSAS_GENERALES:
            if causa not in puntajes:
                puntajes[causa] = peso
            if len(puntajes) >= 3:
                break

    ordenadas = sorted(puntajes.items(), key=lambda item: item[1], reverse=True)[:3]
    total = sum(peso for _, peso in ordenadas) or 1
    probabilidades = [max(1, round(peso / total * 100)) for _, peso in ordenadas]
    probabilidades[-1] = 100 - sum(probabilidades[:-1])
    if probabilidades[-1] < 1:
        probabilidades = [34, 33, 33]

    return [
        {
            'causa': causa,
            'probabilidad': probabilidad,
            'ranking': indice,
        }
        for indice, ((causa, _), probabilidad) in enumerate(zip(ordenadas, probabilidades), start=1)
    ]


def clasificar_riesgo(normalizados, texto=''):
    texto_normalizado = normalizar_texto(texto)
    if any(normalizar_texto(palabra) in texto_normalizado for palabra in PALABRAS_RIESGO_ALTO):
        return 'NO_MOVER_GRUA', 'Se detectaron síntomas o palabras asociadas a un riesgo alto.'

    riesgo = RIESGO_POR_DEFECTO
    for sintoma in normalizados:
        if RIESGO_PRIORIDAD.get(sintoma.get('gravedad'), 0) > RIESGO_PRIORIDAD[riesgo]:
            riesgo = sintoma['gravedad']

    if (
        riesgo == 'PRECAUCION'
        and any(normalizar_texto(palabra) in texto_normalizado for palabra in PALABRAS_RIESGO_BAJO)
    ):
        riesgo = 'PUEDE_RODAR'

    justificaciones = {
        'PUEDE_RODAR': 'Los síntomas reportados no impiden mover el vehículo con precaución.',
        'PRECAUCION': 'Se recomienda mover el vehículo solo para una inspección cercana.',
        'NO_MOVER_GRUA': 'El vehículo no debe moverse por sus propios medios; requiere grúa.',
    }
    return riesgo, justificaciones[riesgo]


def sugerir_pruebas(normalizados, justificacion_riesgo=''):
    pruebas = []
    vistos = set()
    for sintoma in normalizados:
        for clave, datos in TAXONOMIA.items():
            if sintoma['componente'] != datos['etiqueta']:
                continue
            for prueba, procedimiento, esperado in datos['pruebas']:
                if prueba in vistos:
                    continue
                vistos.add(prueba)
                pruebas.append({
                    'prueba': prueba,
                    'procedimiento': procedimiento,
                    'valor_esperado': esperado,
                })

    if not pruebas:
        pruebas = [{
            'prueba': 'Inspección visual y entrevista técnica',
            'procedimiento': 'Revisar el vehículo y confirmar el relato del cliente.',
            'valor_esperado': 'Identificar el componente afectado antes de intervenir.',
        }]

    if justificacion_riesgo:
        pruebas.append({
            'prueba': 'Verificación de seguridad previa',
            'procedimiento': justificacion_riesgo,
            'valor_esperado': 'Confirmar que el vehículo puede moverse o requiere grúa.',
        })
    return pruebas[:4]


def _textos_de_orden(orden):
    narrativas = []
    transcripciones = []
    imagenes = []
    confianzas = []

    for evidencia in orden.evidencias.all():
        if evidencia.narrativa_cliente:
            narrativas.append(evidencia.narrativa_cliente)
        if evidencia.archivo_audio:
            resultado = transcribir_audio(evidencia.archivo_audio)
            if resultado['texto']:
                transcripciones.append(resultado['texto'])
            confianzas.append(resultado['confianza'])
        if evidencia.imagen:
            resultado = analizar_imagen(evidencia.imagen)
            if resultado['descripcion']:
                imagenes.append(resultado['descripcion'])

    for entrada in orden.entradas_multimodales.all():
        if entrada.modo == 'NARRATIVA':
            narrativas.append(entrada.contenido)
        elif entrada.modo == 'VOZ':
            transcripciones.append(entrada.contenido)
        elif entrada.modo == 'IMAGEN':
            imagenes.append(entrada.contenido)

    return narrativas, transcripciones, imagenes, confianzas


def procesar_orden(orden):
    """Ejecuta el pipeline y persiste el análisis. Devuelve (resultado, analisis)."""
    narrativas, transcripciones, imagenes, confianzas = _textos_de_orden(orden)
    texto = ' '.join(narrativas + transcripciones + imagenes)
    normalizados = normalizar_sintomas(texto)
    causas = rankear_causas(normalizados, orden.vehiculo)
    riesgo, justificacion = clasificar_riesgo(normalizados, texto)
    pruebas = sugerir_pruebas(normalizados, justificacion)

    resultado = {
        'sintomas_normalizados': normalizados,
        'causas_probables': causas,
        'nivel_riesgo': riesgo,
        'pruebas_taller_sugeridas': pruebas,
    }

    analisis = AnalisisSintoma.objects.create(
        orden=orden,
        sintomas_normalizados=normalizados,
        causas_probables=causas,
        nivel_riesgo=riesgo,
        pruebas_taller_sugeridas=pruebas,
        transcripcion_confianza=round(mean(confianzas), 3) if confianzas else 0.0,
    )

    for evidencia in orden.evidencias.all():
        evidencia.diagnostico_ia_json = resultado
        evidencia.nivel_riesgo = riesgo
        evidencia.save(update_fields=['diagnostico_ia_json', 'nivel_riesgo'])

    return resultado, analisis
