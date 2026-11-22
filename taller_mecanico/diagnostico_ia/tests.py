import io
import json
import shutil
import tempfile
from unittest.mock import patch
from urllib.error import HTTPError

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import PerfilUsuario
from workshop.models import EvidenciaSintoma, OrdenFalla, Taller, Vehiculo

from .models import AnalisisSintoma
from .services import (
    DiagnosticoIAError,
    analizar_imagen,
    clasificar_riesgo,
    normalizar_sintomas,
    procesar_orden,
    rankear_causas,
    transcribir_audio,
)


class BaseDiagnosticoTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create(
            username='admin', email='admin@example.com', is_staff=True, is_superuser=True
        )
        self.cliente = User.objects.create(username='cliente', email='cliente@example.com')
        self.taller = Taller.objects.create(nombre='Taller AutoDiag')
        self.vehiculo = Vehiculo.objects.create(
            placa='IA001',
            marca='Toyota',
            modelo='Corolla',
            anio=2015,
            motor='1.8',
        )
        self.orden = OrdenFalla.objects.create(
            taller=self.taller,
            vehiculo=self.vehiculo,
            cliente=self.cliente,
            kilometraje_ingreso=120000,
        )

    def crear_evidencia(self, texto):
        return EvidenciaSintoma.objects.create(
            orden=self.orden,
            narrativa_cliente=texto,
            nivel_riesgo='PRECAUCION',
        )


@override_settings(DIAGNOSTICO_IA_PROVIDER='local')
class PipelineTests(BaseDiagnosticoTest):
    def test_normalizacion_detecta_componentes(self):
        sintomas = normalizar_sintomas('El motor vibra y el freno hace ruido')
        componentes = {sintoma['componente'] for sintoma in sintomas}
        self.assertIn('Motor y combustión', componentes)
        self.assertIn('Sistema de frenos', componentes)
        self.assertTrue(all('codigo' in sintoma for sintoma in sintomas))

    def test_rankings_tres_causas_descendentes_y_suman_cien(self):
        causas = rankear_causas(normalizar_sintomas('motor vibra y humo'), self.vehiculo)
        self.assertEqual(len(causas), 3)
        probabilidades = [causa['probabilidad'] for causa in causas]
        self.assertEqual(sum(probabilidades), 100)
        self.assertEqual(probabilidades, sorted(probabilidades, reverse=True))

    def test_riesgo_alto_para_frenos(self):
        normalizados = normalizar_sintomas('El pedal del freno está esponjoso y hay fuga')
        riesgo, justificacion = clasificar_riesgo(normalizados, 'freno con fuga')
        self.assertEqual(riesgo, 'NO_MOVER_GRUA')
        self.assertTrue(justificacion)

    def test_procesar_orden_genera_json_esperado(self):
        self.crear_evidencia('El motor hace un ruido y vibra al acelerar. Revisar bujías.')
        resultado, analisis = procesar_orden(self.orden)
        self.assertEqual(
            set(resultado.keys()),
            {'sintomas_normalizados', 'causas_probables', 'nivel_riesgo', 'pruebas_taller_sugeridas'},
        )
        self.assertIn(resultado['nivel_riesgo'], {'PUEDE_RODAR', 'PRECAUCION', 'NO_MOVER_GRUA'})
        self.assertEqual(len(resultado['causas_probables']), 3)
        self.assertTrue(resultado['pruebas_taller_sugeridas'])
        self.assertIsInstance(analisis, AnalisisSintoma)
        self.assertEqual(analisis.orden, self.orden)
        self.assertTrue(self.orden.evidencias.first().diagnostico_ia_json)

    def test_transcripcion_sin_api_key_no_bloquea(self):
        resultado = transcribir_audio(None)
        self.assertEqual(resultado['texto'], '')

    def test_transcripcion_con_archivo_sin_api_key_usa_narrativa(self):
        audio = SimpleUploadedFile(
            'nota.mp3', b'ID3\x04\x00\x00\x00\x00\x00\x00', content_type='audio/mpeg'
        )
        resultado = transcribir_audio(audio)
        self.assertEqual(resultado['texto'], '')
        self.assertEqual(resultado['confianza'], 0.0)
        self.assertIn('narrativa escrita', resultado['advertencia'])

    def test_imagen_local_genera_descripcion_sin_api_key(self):
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media, True)
        with override_settings(MEDIA_ROOT=media):
            buffer = io.BytesIO()
            Image.new('RGB', (80, 60), 'red').save(buffer, format='JPEG')
            imagen = SimpleUploadedFile(
                'foto.jpg', buffer.getvalue(), content_type='image/jpeg'
            )
            evidencia = EvidenciaSintoma.objects.create(
                orden=self.orden,
                imagen=imagen,
                narrativa_cliente='Testigo de motor encendido.',
                nivel_riesgo='PRECAUCION',
            )
            resultado = analizar_imagen(evidencia.imagen)

        self.assertIn('80x60', resultado['descripcion'])
        self.assertGreater(resultado['confianza'], 0)


@override_settings(DIAGNOSTICO_IA_PROVIDER='local')
class DiagnosticoViewsTests(BaseDiagnosticoTest):
    def test_cliente_crea_orden_y_narrativa_queda_guardada_como_evidencia(self):
        vehiculo = Vehiculo.objects.create(
            placa='IA-002',
            marca='Honda',
            modelo='Civic',
            anio=2022,
            cliente=self.cliente,
        )
        self.client.force_login(self.cliente)
        narrativa = 'El pedal del freno se siente esponjoso y tiene fuga de líquido.'

        response = self.client.post(reverse('orden_nueva'), {
            'vehiculo': vehiculo.pk,
            'taller': self.taller.pk,
            'kilometraje_ingreso': 85000,
            'narrativa_cliente': narrativa,
        })

        self.assertEqual(response.status_code, 302)
        orden = OrdenFalla.objects.get(cliente=self.cliente, vehiculo=vehiculo)
        self.assertTrue(response['Location'].endswith('#evidencias'))
        evidencia = orden.evidencias.get()
        self.assertEqual(evidencia.narrativa_cliente, narrativa)
        analisis = orden.analisis_ia.get()
        self.assertEqual(analisis.nivel_riesgo, 'NO_MOVER_GRUA')

    def test_cliente_agrega_evidencia_y_se_muestra_el_analisis_mas_reciente(self):
        self.crear_evidencia('El motor vibra al acelerar.')
        _, analisis_anterior = procesar_orden(self.orden)
        self.client.force_login(self.cliente)
        narrativa = 'El pedal del freno se siente esponjoso y tiene fuga de líquido.'

        response = self.client.post(
            reverse('agregar_evidencia', args=[self.orden.pk]),
            {
                'narrativa_cliente': narrativa,
                'nivel_riesgo': 'PRECAUCION',
            },
        )

        detalle_url = reverse('orden_detalle', args=[self.orden.pk])
        self.assertRedirects(
            response,
            f'{detalle_url}#evidencias',
            fetch_redirect_response=False,
        )
        evidencia = self.orden.evidencias.order_by('-pk').first()
        self.assertEqual(evidencia.narrativa_cliente, narrativa)
        analisis_reciente = self.orden.analisis_ia.order_by('-creado_en', '-pk').first()
        self.assertGreater(analisis_reciente.pk, analisis_anterior.pk)
        self.assertEqual(analisis_reciente.nivel_riesgo, 'NO_MOVER_GRUA')

        respuesta_detalle = self.client.get(detalle_url)
        self.assertEqual(
            respuesta_detalle.context['ultimo_analisis'].pk,
            analisis_reciente.pk,
        )
        contenido = respuesta_detalle.content.decode()
        self.assertIn(narrativa, contenido)
        self.assertLess(
            contenido.index('data-section="resumen"'),
            contenido.index('data-section="evidencias"'),
        )
        self.assertLess(
            contenido.index('data-section="evidencias"'),
            contenido.index('data-section="diagnostico"'),
        )

        tecnico = User.objects.create_user('tecnico_evidencia')
        tecnico.perfil.rol = PerfilUsuario.Rol.MECANICO
        tecnico.perfil.save(update_fields=['rol'])
        self.orden.mecanico_asignado = tecnico
        self.orden.save(update_fields=['mecanico_asignado'])
        self.client.force_login(tecnico)
        respuesta_tecnico = self.client.get(detalle_url)
        self.assertContains(respuesta_tecnico, narrativa)

    def test_analizar_endpoint_crea_analisis(self):
        self.crear_evidencia('El vehículo pierde potencia y tiene testigo de motor.')
        self.client.force_login(self.cliente)
        response = self.client.post(reverse('analizar_sintoma', args=[self.orden.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AnalisisSintoma.objects.filter(orden=self.orden).exists())

    def test_resultado_visible_para_dueno(self):
        self.crear_evidencia('Ruido en la suspensión trasera.')
        self.client.force_login(self.cliente)
        self.client.post(reverse('analizar_sintoma', args=[self.orden.pk]))
        analisis = AnalisisSintoma.objects.get(orden=self.orden)
        response = self.client.get(reverse('resultado_analisis', args=[analisis.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.orden.codigo_orden)

    def test_otro_cliente_no_ve_analisis(self):
        otro = User.objects.create(username='otro', email='otro@example.com')
        self.crear_evidencia('Ruido en la suspensión trasera.')
        analisis = AnalisisSintoma.objects.create(
            orden=self.orden,
            sintomas_normalizados=[],
            causas_probables=[],
            nivel_riesgo='PRECAUCION',
            pruebas_taller_sugeridas=[],
        )
        self.client.force_login(otro)
        response = self.client.get(reverse('resultado_analisis', args=[analisis.pk]))
        self.assertEqual(response.status_code, 403)


class ModelProviderTests(BaseDiagnosticoTest):
    RESPUESTA_MODELO = {
        'sintomas_normalizados': [{
            'codigo': 'FRENO-01',
            'componente': 'Sistema de frenos',
            'sintoma': 'Pedal esponjoso',
            'gravedad': 'PRECAUCION',
        }],
        'causas_probables': [
            {'causa': 'Aire en el sistema hidráulico', 'probabilidad': 60, 'ranking': 1},
            {'causa': 'Fuga de líquido', 'probabilidad': 30, 'ranking': 2},
            {'causa': 'Desgaste de componentes', 'probabilidad': 10, 'ranking': 3},
        ],
        'nivel_riesgo': 'PRECAUCION',
        'pruebas_taller_sugeridas': [{
            'prueba': 'Inspeccionar frenos',
            'procedimiento': 'Revisar el circuito hidráulico y sus componentes.',
            'valor_esperado': 'Sin fugas y pedal firme.',
        }],
    }

    def crear_entrada(self):
        return EvidenciaSintoma.objects.create(
            orden=self.orden,
            narrativa_cliente='El pedal del freno se siente esponjoso.',
        )

    @override_settings(
        DIAGNOSTICO_IA_PROVIDER='ollama',
        OLLAMA_BASE_URL='http://localhost:11434',
        OLLAMA_MODEL='modelo-prueba',
        OLLAMA_MODELS=['modelo-prueba'],
        OLLAMA_CLOUD_ENABLED=True,
        OLLAMA_LOCAL_ENABLED=False,
        OLLAMA_LOCAL_MODELS=[],
        OLLAMA_API_KEY='',
    )
    @patch('diagnostico_ia.services._post_json')
    def test_procesa_narrativa_con_modelo_ollama(self, post_json):
        self.crear_entrada()
        post_json.return_value = {
            'message': {'content': json.dumps(self.RESPUESTA_MODELO)},
        }

        resultado, analisis = procesar_orden(self.orden)

        args, kwargs = post_json.call_args
        self.assertEqual(args[0], 'http://localhost:11434/api/chat')
        self.assertEqual(args[1]['model'], 'modelo-prueba')
        self.assertFalse(args[1]['stream'])
        self.assertIn('pedal del freno', args[1]['messages'][1]['content'])
        self.assertIsNone(kwargs['headers'])
        self.assertEqual(kwargs['timeout'], 90)
        self.assertEqual(analisis.sintomas_normalizados, resultado['sintomas_normalizados'])

    @override_settings(
        DIAGNOSTICO_IA_PROVIDER='ollama',
        OLLAMA_BASE_URL='https://ollama.com',
        OLLAMA_MODEL='deepseek-v4.1-flash:cloud',
        OLLAMA_MODELS=['deepseek-v4.1-flash:cloud'],
        OLLAMA_CLOUD_ENABLED=True,
        OLLAMA_LOCAL_ENABLED=False,
        OLLAMA_LOCAL_MODELS=[],
        OLLAMA_API_KEY='test-ollama-key',
    )
    @patch('diagnostico_ia.services._post_json')
    def test_ollama_cloud_envia_bearer_token(self, post_json):
        self.crear_entrada()
        post_json.return_value = {
            'message': {'content': json.dumps(self.RESPUESTA_MODELO)},
        }

        procesar_orden(self.orden)

        args, kwargs = post_json.call_args
        self.assertEqual(args[0], 'https://ollama.com/api/chat')
        self.assertEqual(args[1]['model'], 'deepseek-v4.1-flash:cloud')
        self.assertEqual(
            kwargs['headers'],
            {'Authorization': 'Bearer test-ollama-key'},
        )

    @override_settings(
        DIAGNOSTICO_IA_PROVIDER='ollama',
        OLLAMA_CLOUD_ENABLED=False,
        OLLAMA_LOCAL_ENABLED=True,
        OLLAMA_MODELS=[],
        OLLAMA_LOCAL_MODELS=['qwen2.5:1.5b'],
        OLLAMA_LOCAL_BASE_URL='http://localhost:11434',
        OLLAMA_API_KEY='test-ollama-key',
    )
    @patch('diagnostico_ia.services._post_json')
    def test_cloud_desactivado_consulta_solo_modelo_local(self, post_json):
        self.crear_entrada()
        post_json.return_value = {
            'message': {'content': json.dumps(self.RESPUESTA_MODELO)},
        }

        procesar_orden(self.orden)

        args, kwargs = post_json.call_args
        self.assertEqual(args[0], 'http://localhost:11434/api/chat')
        self.assertEqual(args[1]['model'], 'qwen2.5:1.5b')
        self.assertIsNone(kwargs['headers'])

    @override_settings(
        DIAGNOSTICO_IA_PROVIDER='ollama',
        OLLAMA_BASE_URL='https://ollama.com',
        OLLAMA_MODEL='modelo-cloud',
        OLLAMA_MODELS=['modelo-cloud', 'modelo-cloud-respaldo'],
        OLLAMA_CLOUD_ENABLED=True,
        OLLAMA_LOCAL_ENABLED=True,
        OLLAMA_LOCAL_MODELS=['modelo-local', 'modelo-local-respaldo'],
        OLLAMA_LOCAL_BASE_URL='http://localhost:11434',
        OLLAMA_API_KEY='test-ollama-key',
    )
    @patch('diagnostico_ia.services._post_json')
    def test_ollama_pasa_de_cloud_a_local_si_cloud_falla(
        self,
        post_json,
    ):
        self.crear_entrada()
        post_json.side_effect = [
            HTTPError('https://ollama.com/api/chat', 401, 'Unauthorized', None, None),
            {'message': {'content': json.dumps(self.RESPUESTA_MODELO)}},
        ]

        procesar_orden(self.orden)

        llamadas = post_json.call_args_list
        self.assertEqual(
            [llamada.args[0] for llamada in llamadas],
            [
                'https://ollama.com/api/chat',
                'http://localhost:11434/api/chat',
            ],
        )
        self.assertEqual(
            [llamada.args[1]['model'] for llamada in llamadas],
            ['modelo-cloud', 'modelo-local'],
        )
        self.assertEqual(len(llamadas), 2)
        self.assertEqual(
            llamadas[0].kwargs['headers'],
            {'Authorization': 'Bearer test-ollama-key'},
        )
        self.assertIsNone(llamadas[1].kwargs['headers'])

    @override_settings(
        DIAGNOSTICO_IA_PROVIDER='ollama',
        OLLAMA_BASE_URL='https://ollama.com',
        OLLAMA_MODEL='modelo-principal',
        OLLAMA_MODELS=['modelo-principal', 'modelo-respaldo'],
        OLLAMA_CLOUD_ENABLED=True,
        OLLAMA_LOCAL_ENABLED=False,
        OLLAMA_LOCAL_MODELS=[],
        OLLAMA_API_KEY='test-ollama-key',
    )
    @patch(
        'diagnostico_ia.services._post_json',
        side_effect=OSError('sin conexión'),
    )
    def test_ollama_informa_si_fallan_todos_los_modelos(self, post_json):
        self.crear_entrada()

        with self.assertRaisesRegex(
            DiagnosticoIAError,
            'Ningún modelo de Ollama produjo un análisis válido.*modelo-principal.*modelo-respaldo',
        ):
            procesar_orden(self.orden)

        self.assertFalse(AnalisisSintoma.objects.filter(orden=self.orden).exists())
        self.assertEqual(post_json.call_count, 2)

    @override_settings(
        DIAGNOSTICO_IA_PROVIDER='gemini',
        GEMINI_API_KEY='fake-test-key',
        GEMINI_MODEL='gemini-test',
    )
    @patch('diagnostico_ia.services._post_json')
    def test_procesa_narrativa_con_gemini_api(self, post_json):
        self.crear_entrada()
        post_json.return_value = {
            'candidates': [{
                'content': {'parts': [{'text': json.dumps(self.RESPUESTA_MODELO)}]},
            }],
        }

        resultado, _ = procesar_orden(self.orden)

        args, kwargs = post_json.call_args
        self.assertEqual(
            args[0],
            'https://generativelanguage.googleapis.com/v1beta/models/'
            'gemini-test:generateContent',
        )
        self.assertEqual(kwargs['headers']['x-goog-api-key'], 'fake-test-key')
        self.assertEqual(
            args[1]['generationConfig']['responseMimeType'],
            'application/json',
        )
        self.assertEqual(resultado['causas_probables'][0]['probabilidad'], 60)

    @override_settings(
        DIAGNOSTICO_IA_PROVIDER='ollama',
        OLLAMA_MODEL='modelo-prueba',
        OLLAMA_MODELS=['modelo-prueba'],
        OLLAMA_CLOUD_ENABLED=True,
        OLLAMA_LOCAL_ENABLED=False,
        OLLAMA_LOCAL_MODELS=[],
        OLLAMA_API_KEY='',
    )
    @patch('diagnostico_ia.services._post_json', return_value={'message': {'content': 'not json'}})
    def test_respuesta_invalida_del_modelo_no_se_guarda_como_analisis(self, post_json):
        self.crear_entrada()

        with self.assertRaisesRegex(DiagnosticoIAError, 'JSON válido'):
            procesar_orden(self.orden)

        self.assertFalse(AnalisisSintoma.objects.filter(orden=self.orden).exists())
