import io
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import PerfilUsuario
from workshop.models import EvidenciaSintoma, OrdenFalla, Taller, Vehiculo

from .models import AnalisisSintoma
from .services import (
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


class DiagnosticoViewsTests(BaseDiagnosticoTest):
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
