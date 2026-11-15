from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import PerfilUsuario
from workshop.models import OrdenFalla, Taller, Vehiculo

from .forms import ConfiguracionDistribucionForm
from .models import ConfiguracionDistribucion, EnvioReportes
from .services import enviar_reporte


class BaseDistribucionTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create(
            username='admin', email='admin@example.com', is_staff=True, is_superuser=True
        )
        self.cliente = User.objects.create(
            username='cliente', email='cliente@example.com'
        )
        self.taller = Taller.objects.create(nombre='Taller AutoDiag')
        self.vehiculo = Vehiculo.objects.create(
            placa='DIST01', marca='Toyota', modelo='Corolla', anio=2020
        )
        self.orden = OrdenFalla.objects.create(
            taller=self.taller,
            vehiculo=self.vehiculo,
            cliente=self.cliente,
            kilometraje_ingreso=50000,
        )

    def config(self, **kwargs):
        datos = {
            'metodo': 'TELEGRAM',
            'chat_telegram_id': '123456',
            'email_destino': 'cliente@example.com',
        }
        datos.update(kwargs)
        return ConfiguracionDistribucion.objects.create(orden=self.orden, **datos)


class ConfiguracionTests(BaseDistribucionTest):
    def test_formulario_requiere_chat_para_telegram(self):
        form = ConfiguracionDistribucionForm(data={
            'metodo': 'TELEGRAM',
            'chat_telegram_id': '',
            'email_destino': '',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('chat_telegram_id', form.errors)

    def test_formulario_requiere_email_para_email(self):
        form = ConfiguracionDistribucionForm(data={
            'metodo': 'EMAIL',
            'chat_telegram_id': '',
            'email_destino': '',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email_destino', form.errors)

    def test_vista_guarda_configuracion(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('configurar_distribucion', args=[self.orden.pk]), {
            'metodo': 'AMBOS',
            'chat_telegram_id': '987654',
            'email_destino': 'destino@example.com',
        })
        self.assertEqual(response.status_code, 302)
        config = ConfiguracionDistribucion.objects.get(orden=self.orden)
        self.assertEqual(config.metodo, 'AMBOS')
        self.assertEqual(config.chat_telegram_id, '987654')


class EnvioTests(BaseDistribucionTest):
    def test_metodo_ninguno_no_envia(self):
        self.config(metodo='NINGUNO')
        resultado = enviar_reporte(self.orden)
        self.assertTrue(resultado['ok'])
        self.assertTrue(resultado['omitido'])
        self.assertFalse(EnvioReportes.objects.exists())

    @patch('distribucion.services.enviar_email')
    @patch('distribucion.services.enviar_telegram')
    def test_ambos_canales_envian(self, telegram, email):
        self.config(metodo='AMBOS')
        resultado = enviar_reporte(self.orden)
        self.assertTrue(resultado['ok'])
        telegram.assert_called_once()
        email.assert_called_once()
        self.assertEqual(EnvioReportes.objects.filter(estado='ENVIADO').count(), 2)

    @patch('distribucion.services.enviar_telegram')
    def test_reintenta_y_luego_envia(self, telegram):
        self.config(metodo='TELEGRAM')
        telegram.side_effect = [RuntimeError('fallo temporal'), None]
        resultado = enviar_reporte(self.orden, max_intentos=3)
        self.assertTrue(resultado['ok'])
        self.assertEqual(telegram.call_count, 2)
        self.assertEqual(EnvioReportes.objects.filter(estado='Fallido').count(), 1)
        self.assertEqual(EnvioReportes.objects.filter(estado='ENVIADO').count(), 1)

    @patch('distribucion.services.enviar_telegram')
    def test_falla_tras_reintentos(self, telegram):
        self.config(metodo='TELEGRAM')
        telegram.side_effect = RuntimeError('sin red')
        resultado = enviar_reporte(self.orden, max_intentos=2)
        self.assertFalse(resultado['ok'])
        self.assertEqual(telegram.call_count, 2)
        self.assertEqual(EnvioReportes.objects.filter(estado='Fallido').count(), 2)

    @patch('distribucion.services.enviar_telegram')
    def test_vista_envia_reporte(self, telegram):
        self.config(metodo='TELEGRAM')
        self.client.force_login(self.admin)
        response = self.client.post(reverse('enviar_reporte', args=[self.orden.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Envío completado')
