"""Servicio de prediagnóstico multimodal con Ollama, Gemini o reglas locales."""

import base64
import json
import math
import os
import uuid
from statistics import mean
from urllib.error import HTTPError

from django.conf import settings

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
RIESGOS_VALIDOS = set(RIESGO_PRIORIDAD)


class DiagnosticoIAError(Exception):
    """Error de configuración o respuesta del proveedor de prediagnóstico."""


class OllamaEndpointAccessError(DiagnosticoIAError):
    """Ollama rechazó el acceso a un endpoint por autorización o facturación."""


def _openai_api_key():
    return settings.OPENAI_API_KEY


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


def _post_json(url, payload, headers=None, timeout=60):
    import urllib.request

    data = json.dumps(payload).encode('utf-8')
    request = urllib.request.Request(url, data=data, method='POST')
    request.add_header('Content-Type', 'application/json')
    for clave, valor in (headers or {}).items():
        request.add_header(clave, valor)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))


def _proveedor_configurado():
    proveedor = settings.DIAGNOSTICO_IA_PROVIDER.strip().lower()
    if proveedor not in {'ollama', 'gemini', 'local'}:
        raise DiagnosticoIAError(
            'DIAGNOSTICO_IA_PROVIDER debe ser ollama, gemini o local.'
        )
    return proveedor


def proveedor_diagnostico():
    proveedor = _proveedor_configurado()
    if proveedor == 'ollama':
        cloud_count = (
            len(getattr(settings, 'OLLAMA_MODELS', [settings.OLLAMA_MODEL]))
            if settings.OLLAMA_CLOUD_ENABLED
            else 0
        )
        local_count = (
            len(getattr(settings, 'OLLAMA_LOCAL_MODELS', []))
            if settings.OLLAMA_LOCAL_ENABLED
            else 0
        )
        if local_count:
            if cloud_count:
                return f'Ollama · {cloud_count} modelos Cloud → {local_count} locales'
            return f'Ollama local · respaldo ({local_count} modelos)'
        return f'Ollama Cloud · respaldo ({cloud_count} modelos)'
    if proveedor == 'gemini':
        if not settings.GEMINI_API_KEY:
            return 'Gemini API · falta configurar GEMINI_API_KEY'
        return f'Gemini API · {settings.GEMINI_MODEL}'
    return 'Motor local por reglas (sin modelo generativo)'


INSTRUCCION_DIAGNOSTICO = (
    'Eres un asistente de prediagnóstico automotriz para un taller. Analiza el relato '
    'del cliente junto con los datos del vehículo. No afirmes que una causa está '
    'confirmada; presenta hipótesis para revisión del técnico. Prioriza la seguridad: '
    'si hay posible riesgo de frenos, dirección, combustible, sobrecalentamiento o '
    'pérdida de control, usa NO_MOVER_GRUA. Responde únicamente un objeto JSON válido '
    'con síntomas_normalizados como lista de objetos {codigo, componente, sintoma, '
    'gravedad}, causas_probables como exactamente tres objetos {causa, probabilidad, '
    'ranking}, nivel_riesgo con valor PUEDE_RODAR, PRECAUCION o NO_MOVER_GRUA, y '
    'pruebas_taller_sugeridas como lista de objetos {prueba, procedimiento, '
    'valor_esperado}. Las probabilidades son estimaciones, deben sumar 100 y estar '
    'ordenadas de mayor a menor. No recomiendes conducir si la seguridad no está clara.'
)


def _prompt_diagnostico(texto, orden):
    vehiculo = orden.vehiculo
    datos_vehiculo = (
        f'Marca: {vehiculo.marca}; modelo: {vehiculo.modelo}; año: {vehiculo.anio}; '
        f'motor: {vehiculo.motor or "no indicado"}; '
        f'kilometraje: {orden.kilometraje_ingreso} km.'
    )
    return (
        f'Datos del vehículo:\n{datos_vehiculo}\n\n'
        f'Síntomas y evidencia reportados:\n{texto or "El cliente no describió síntomas."}'
    )


def _consultar_ollama(prompt, model=None, base_url=None, api_key=None):
    model = model or settings.OLLAMA_MODEL
    base_url = settings.OLLAMA_BASE_URL if base_url is None else base_url
    api_key = settings.OLLAMA_API_KEY if api_key is None else api_key
    url = f'{base_url.rstrip("/")}/api/chat'
    headers = (
        {'Authorization': f'Bearer {api_key}'}
        if api_key
        else None
    )
    try:
        respuesta = _post_json(
            url,
            {
                'model': model,
                'messages': [
                    {'role': 'system', 'content': INSTRUCCION_DIAGNOSTICO},
                    {'role': 'user', 'content': prompt},
                ],
                'format': 'json',
                'stream': False,
                'options': {'temperature': 0.2},
            },
            headers=headers,
            timeout=90,
        )
    except HTTPError as exc:
        if exc.code == 401:
            detalle = 'Ollama rechazó la API key (401); verifica ollama.api_key.'
        elif exc.code == 402:
            detalle = 'Ollama requiere pago o acceso adicional (402).'
        elif exc.code == 403:
            detalle = 'Ollama denegó el acceso (403); verifica los permisos de la cuenta.'
        else:
            detalle = f'HTTP Error {exc.code}: {exc.reason}'
        raise OllamaEndpointAccessError(
            f'No se pudo consultar Ollama en {url}: {detalle}'
        ) from exc
    except Exception as exc:
        raise DiagnosticoIAError(
            f'No se pudo consultar Ollama en {url}: {exc}'
        ) from exc
    mensaje = respuesta.get('message') if isinstance(respuesta, dict) else None
    content = mensaje.get('content') if isinstance(mensaje, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise DiagnosticoIAError('Ollama devolvió una respuesta vacía.')
    return content


def _ollama_modelos_respaldo():
    modelos_cloud = (
        getattr(settings, 'OLLAMA_MODELS', [settings.OLLAMA_MODEL])
        if settings.OLLAMA_CLOUD_ENABLED
        else []
    )
    modelos_locales = (
        getattr(settings, 'OLLAMA_LOCAL_MODELS', [])
        if settings.OLLAMA_LOCAL_ENABLED
        else []
    )
    destinos = [
        (modelo, settings.OLLAMA_BASE_URL, settings.OLLAMA_API_KEY)
        for modelo in modelos_cloud
    ]
    destinos.extend(
        (modelo, settings.OLLAMA_LOCAL_BASE_URL, '')
        for modelo in modelos_locales
    )
    return destinos


def _consultar_gemini(prompt):
    if not settings.GEMINI_API_KEY:
        raise DiagnosticoIAError(
            'Seleccionaste Gemini, pero GEMINI_API_KEY no está configurada.'
        )
    url = (
        'https://generativelanguage.googleapis.com/v1beta/models/'
        f'{settings.GEMINI_MODEL}:generateContent'
    )
    try:
        respuesta = _post_json(
            url,
            {
                'systemInstruction': {
                    'parts': [{'text': INSTRUCCION_DIAGNOSTICO}],
                },
                'contents': [{
                    'role': 'user',
                    'parts': [{'text': prompt}],
                }],
                'generationConfig': {
                    'temperature': 0.2,
                    'responseMimeType': 'application/json',
                    'maxOutputTokens': 1200,
                },
            },
            headers={'x-goog-api-key': settings.GEMINI_API_KEY},
            timeout=60,
        )
    except Exception as exc:
        raise DiagnosticoIAError(f'No se pudo consultar Gemini API: {exc}') from exc

    try:
        content = ''.join(
            parte.get('text', '')
            for parte in respuesta['candidates'][0]['content']['parts']
        ).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise DiagnosticoIAError(
            'Gemini no devolvió contenido de diagnóstico.'
        ) from exc
    if not content:
        raise DiagnosticoIAError('Gemini devolvió una respuesta vacía.')
    return content


def _validar_respuesta_modelo(contenido):
    if not isinstance(contenido, str):
        raise DiagnosticoIAError('El modelo devolvió una respuesta en formato no válido.')
    texto = contenido.strip()
    if texto.startswith('```'):
        texto = texto.removeprefix('```json').removeprefix('```').strip()
        if texto.endswith('```'):
            texto = texto[:-3].strip()
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise DiagnosticoIAError(
            'El modelo no devolvió un resultado JSON válido. Vuelve a intentar el análisis.'
        ) from exc
    if not isinstance(datos, dict):
        raise DiagnosticoIAError('La respuesta del modelo no tiene el formato esperado.')

    sintomas = datos.get('sintomas_normalizados')
    if not isinstance(sintomas, list) or not sintomas:
        raise DiagnosticoIAError('El modelo no identificó síntomas en un formato válido.')
    sintomas_normalizados = []
    for indice, sintoma in enumerate(sintomas[:10], start=1):
        if not isinstance(sintoma, dict):
            raise DiagnosticoIAError('Un síntoma devuelto por el modelo no es válido.')
        componente = str(sintoma.get('componente', '')).strip()
        descripcion = str(sintoma.get('sintoma', '')).strip()
        gravedad = str(sintoma.get('gravedad', 'PRECAUCION')).strip().upper()
        if not componente or not descripcion or gravedad not in RIESGOS_VALIDOS:
            raise DiagnosticoIAError('Un síntoma devuelto por el modelo no es válido.')
        sintomas_normalizados.append({
            'codigo': str(sintoma.get('codigo') or f'SINT-{indice:02d}').strip(),
            'componente': componente,
            'sintoma': descripcion,
            'gravedad': gravedad,
        })

    causas = datos.get('causas_probables')
    if not isinstance(causas, list) or len(causas) < 3:
        raise DiagnosticoIAError('El modelo no devolvió tres causas probables.')
    causas_limpias = []
    for causa in causas[:3]:
        if not isinstance(causa, dict) or not str(causa.get('causa', '')).strip():
            raise DiagnosticoIAError('Una causa probable devuelta por el modelo no es válida.')
        try:
            probabilidad = float(causa['probabilidad'])
        except (KeyError, TypeError, ValueError) as exc:
            raise DiagnosticoIAError('Una probabilidad devuelta por el modelo no es válida.') from exc
        if not math.isfinite(probabilidad) or probabilidad < 0:
            raise DiagnosticoIAError('Una probabilidad devuelta por el modelo no es válida.')
        causas_limpias.append({
            'causa': str(causa['causa']).strip(),
            'probabilidad': probabilidad,
        })
    total_probabilidad = sum(causa['probabilidad'] for causa in causas_limpias)
    if total_probabilidad <= 0:
        raise DiagnosticoIAError('Las probabilidades devueltas por el modelo no son válidas.')
    for causa in causas_limpias:
        causa['probabilidad'] = round(causa['probabilidad'] * 100 / total_probabilidad)
    diferencia = 100 - sum(causa['probabilidad'] for causa in causas_limpias)
    causas_limpias[0]['probabilidad'] += diferencia
    causas_limpias.sort(key=lambda causa: causa['probabilidad'], reverse=True)
    causas_probables = [
        {
            **causa,
            'probabilidad': int(causa['probabilidad']),
            'ranking': indice,
        }
        for indice, causa in enumerate(causas_limpias, start=1)
    ]

    nivel_riesgo = str(datos.get('nivel_riesgo', '')).strip().upper()
    if nivel_riesgo not in RIESGOS_VALIDOS:
        raise DiagnosticoIAError('El nivel de riesgo devuelto por el modelo no es válido.')
    pruebas = datos.get('pruebas_taller_sugeridas')
    if not isinstance(pruebas, list) or not pruebas:
        raise DiagnosticoIAError('El modelo no devolvió pruebas de taller sugeridas.')
    pruebas_limpias = []
    for prueba in pruebas[:4]:
        if not isinstance(prueba, dict):
            raise DiagnosticoIAError('Una prueba sugerida por el modelo no es válida.')
        elementos = {
            clave: str(prueba.get(clave, '')).strip()
            for clave in ('prueba', 'procedimiento', 'valor_esperado')
        }
        if not all(elementos.values()):
            raise DiagnosticoIAError('Una prueba sugerida por el modelo no es válida.')
        pruebas_limpias.append(elementos)

    return {
        'sintomas_normalizados': sintomas_normalizados,
        'causas_probables': causas_probables,
        'nivel_riesgo': nivel_riesgo,
        'pruebas_taller_sugeridas': pruebas_limpias,
    }


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
    proveedor = _proveedor_configurado()
    if proveedor == 'local':
        normalizados = normalizar_sintomas(texto)
        causas = rankear_causas(normalizados, orden.vehiculo)
        riesgo, justificacion = clasificar_riesgo(normalizados, texto)
        resultado = {
            'sintomas_normalizados': normalizados,
            'causas_probables': causas,
            'nivel_riesgo': riesgo,
            'pruebas_taller_sugeridas': sugerir_pruebas(normalizados, justificacion),
        }
    else:
        prompt = _prompt_diagnostico(texto, orden)
        if proveedor == 'ollama':
            errores_modelos = []
            resultado = None
            endpoints_bloqueados = set()
            for modelo, base_url, api_key in _ollama_modelos_respaldo():
                endpoint = base_url.rstrip('/')
                if endpoint in endpoints_bloqueados:
                    continue
                try:
                    contenido = _consultar_ollama(
                        prompt,
                        modelo,
                        base_url,
                        api_key,
                    )
                    resultado = _validar_respuesta_modelo(contenido)
                    break
                except OllamaEndpointAccessError as exc:
                    errores_modelos.append(f'{modelo}: {exc}')
                    endpoints_bloqueados.add(endpoint)
                except DiagnosticoIAError as exc:
                    errores_modelos.append(f'{modelo}: {exc}')
            if resultado is None:
                detalle = ' | '.join(errores_modelos)
                raise DiagnosticoIAError(
                    f'Ningún modelo de Ollama produjo un análisis válido. {detalle}'
                )
        else:
            contenido = _consultar_gemini(prompt)
            resultado = _validar_respuesta_modelo(contenido)

        sintomas_locales = normalizar_sintomas(texto)
        riesgo_seguridad, _ = clasificar_riesgo(sintomas_locales, texto)
        if RIESGO_PRIORIDAD[riesgo_seguridad] > RIESGO_PRIORIDAD[resultado['nivel_riesgo']]:
            resultado['nivel_riesgo'] = riesgo_seguridad

    analisis = AnalisisSintoma.objects.create(
        orden=orden,
        sintomas_normalizados=resultado['sintomas_normalizados'],
        causas_probables=resultado['causas_probables'],
        nivel_riesgo=resultado['nivel_riesgo'],
        pruebas_taller_sugeridas=resultado['pruebas_taller_sugeridas'],
        transcripcion_confianza=round(mean(confianzas), 3) if confianzas else 0.0,
    )

    for evidencia in orden.evidencias.all():
        evidencia.diagnostico_ia_json = resultado
        evidencia.nivel_riesgo = resultado['nivel_riesgo']
        evidencia.save(update_fields=['diagnostico_ia_json', 'nivel_riesgo'])

    return resultado, analisis
