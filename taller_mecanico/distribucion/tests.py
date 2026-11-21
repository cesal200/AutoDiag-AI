from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from accounts.models import PerfilUsuario
from workshop.models import OrdenFalla, Taller, Vehiculo

from .forms import ConfiguracionDistribucionForm
from .models import ConfiguracionDistribucion, ConfiguracionRemitente, EnvioReportes
from .services import enviar_reporte


class BaseDistribucionTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create(
            username='admin', email='admin@example.com', is_staff=True, is_superuser=True
        )
        self.cliente = User.objects.create(
            username='cliente', email='cliente@example.com'
        )
        self.cliente.perfil.telefono = '+18095550102'
        self.cliente.perfil.save(update_fields=['telefono'])
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
    def test_formulario_whatsapp_admite_numero_del_perfil_o_override(self):
        form = ConfiguracionDistribucionForm(data={
            'metodo': 'WHATSAPP',
            'chat_telegram_id': '',
            'email_destino': '',
            'telefono_whatsapp': '',
        })
        self.assertTrue(form.is_valid())

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

    def test_admin_configura_contacto_remitente_del_taller(self):
        self.client.force_login(self.admin)

        response = self.client.post(reverse('configurar_remitente'), {
            'telefono_whatsapp': '+18095550101',
            'email_remitente': 'reportes@taller.com',
        })

        self.assertRedirects(
            response,
            reverse('configurar_remitente'),
            fetch_redirect_response=False,
        )
        config = ConfiguracionRemitente.objects.get(pk=1)
        self.assertEqual(config.telefono_whatsapp, '+18095550101')
        self.assertEqual(config.email_remitente, 'reportes@taller.com')

    def test_no_admin_no_puede_configurar_remitente(self):
        self.client.force_login(self.cliente)

        response = self.client.get(reverse('configurar_remitente'))

        self.assertEqual(response.status_code, 403)


class EnvioTests(BaseDistribucionTest):
    def test_abre_whatsapp_web_con_datos_de_seguimiento(self):
        self.config(
            metodo='WHATSAPP',
            telefono_whatsapp='+18095550101',
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse('abrir_whatsapp', args=[self.orden.pk]))

        self.assertEqual(response.status_code, 302)
        ubicacion = response['Location']
        self.assertIn('https://wa.me/18095550101', ubicacion)
        self.assertIn('DIST01', ubicacion)
        self.assertIn('seguimiento', ubicacion)
        self.assertIn('reporte.pdf', ubicacion)

    @patch('workshop.views.construir_pdf', return_value=b'%PDF-1.4 test')
    def test_descarga_publica_del_pdf_usa_token_vigente(self, construir_pdf):
        response = self.client.get(reverse(
            'descargar_pdf_publico',
            args=[self.orden.token_publico],
        ))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertEqual(response.content, b'%PDF-1.4 test')
        construir_pdf.assert_called_once_with(self.orden)

    def test_descarga_publica_rechaza_token_expirado(self):
        self.orden.token_expira_en = timezone.now() - timedelta(seconds=1)
        self.orden.save(update_fields=['token_expira_en'])

        response = self.client.get(reverse(
            'descargar_pdf_publico',
            args=[self.orden.token_publico],
        ))

        self.assertEqual(response.status_code, 404)

    def test_whatsapp_web_no_se_reporta_como_envio_automatico(self):
        self.config(
            metodo='WHATSAPP',
            telefono_whatsapp='+18095550101',
        )

        resultado = enviar_reporte(self.orden)

        self.assertFalse(resultado['ok'])
        self.assertTrue(resultado['requiere_accion'])
        self.assertFalse(EnvioReportes.objects.exists())

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

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='default@example.com',
    )
    @patch('distribucion.services.construir_pdf', return_value=b'%PDF-1.4 sample')
    def test_email_adjunta_pdf_y_usa_remitente_configurado(self, construir_pdf):
        self.config(metodo='EMAIL', email_destino='destino@example.com')
        ConfiguracionRemitente.objects.create(
            pk=1,
            email_remitente='reportes@taller.com',
            telefono_whatsapp='+18095550101',
        )

        resultado = enviar_reporte(
            self.orden,
            enlace_seguimiento='https://taller.example/seguimiento/token/',
            enlace_pdf='https://taller.example/seguimiento/token/reporte.pdf',
        )

        self.assertTrue(resultado['ok'])
        self.assertEqual(len(mail.outbox), 1)
        mensaje = mail.outbox[0]
        self.assertEqual(mensaje.from_email, 'reportes@taller.com')
        self.assertEqual(mensaje.to, ['destino@example.com'])
        self.assertEqual(
            mensaje.attachments[0],
            (resultado['nombre_archivo'], b'%PDF-1.4 sample', 'application/pdf'),
        )
        self.assertIn('https://taller.example/seguimiento/token/', mensaje.body)
        self.assertIn('https://taller.example/seguimiento/token/reporte.pdf', mensaje.body)
        construir_pdf.assert_called_once_with(self.orden)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='default@example.com',
    )
    @patch('distribucion.services.construir_pdf', return_value=b'%PDF-1.4 sample')
    def test_correo_y_whatsapp_envia_pdf_por_correo_y_pide_confirmacion_manual(
        self,
        construir_pdf,
    ):
        self.config(metodo='WHATSAPP_EMAIL', email_destino='')

        resultado = enviar_reporte(
            self.orden,
            enlace_pdf='https://taller.example/seguimiento/token/reporte.pdf',
        )

        self.assertTrue(resultado['ok'])
        self.assertTrue(resultado['requiere_accion'])
        self.assertTrue(resultado['correo_enviado'])
        self.assertEqual(mail.outbox[0].to, ['cliente@example.com'])
        self.assertEqual(
            mail.outbox[0].attachments[0][1],
            b'%PDF-1.4 sample',
        )
        self.assertEqual(
            [item['canal'] for item in resultado['resultados']],
            ['Email', 'WhatsApp Web'],
        )
        self.assertFalse(resultado['resultados'][1]['ok'])
        self.assertEqual(EnvioReportes.objects.filter(estado='ENVIADO').count(), 1)
        construir_pdf.assert_called_once_with(self.orden)

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
