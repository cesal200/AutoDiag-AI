"""Pruebas específicas del taller."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import PerfilUsuario

from .models import EvidenciaSintoma, OrdenFalla, Taller, Vehiculo


class GestionEvidenciasTests(TestCase):
    def setUp(self):
        self.cliente = User.objects.create_user(
            username='cliente-evidencia',
            password='test-password',
        )
        PerfilUsuario.objects.update_or_create(
            user=self.cliente,
            defaults={'rol': PerfilUsuario.Rol.CLIENTE},
        )
        self.otro_cliente = User.objects.create_user(
            username='otro-cliente',
            password='test-password',
        )
        PerfilUsuario.objects.update_or_create(
            user=self.otro_cliente,
            defaults={'rol': PerfilUsuario.Rol.CLIENTE},
        )
        self.admin = User.objects.create_superuser(
            username='admin-evidencia',
            email='admin-evidencia@example.com',
            password='test-password',
        )
        taller = Taller.objects.create(nombre='Taller de pruebas')
        vehiculo = Vehiculo.objects.create(
            placa='EVI001',
            marca='Toyota',
            modelo='Corolla',
            anio=2020,
            cliente=self.cliente,
        )
        self.orden = OrdenFalla.objects.create(
            taller=taller,
            vehiculo=vehiculo,
            cliente=self.cliente,
            kilometraje_ingreso=10000,
        )
        self.evidencia = EvidenciaSintoma.objects.create(
            orden=self.orden,
            narrativa_cliente='Ruido al girar.',
            nivel_riesgo='PRECAUCION',
        )

    def test_cliente_puede_editar_evidencia_de_su_orden(self):
        self.client.force_login(self.cliente)
        url = reverse(
            'editar_evidencia',
            args=[self.orden.pk, self.evidencia.pk],
        )
        detalle_url = reverse('orden_detalle', args=[self.orden.pk])

        respuesta = self.client.get(detalle_url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, url)
        self.assertContains(
            respuesta,
            reverse(
                'eliminar_evidencia',
                args=[self.orden.pk, self.evidencia.pk],
            ),
        )

        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Ruido al girar.')

        respuesta = self.client.post(url, {
            'narrativa_cliente': 'Vibración al girar.',
            'nivel_riesgo': 'PRECAUCION',
        })

        self.assertRedirects(
            respuesta,
            f'{detalle_url}#evidencias',
            fetch_redirect_response=False,
        )
        self.evidencia.refresh_from_db()
        self.assertEqual(self.evidencia.narrativa_cliente, 'Vibración al girar.')

    def test_cliente_puede_eliminar_evidencia_de_su_orden(self):
        self.client.force_login(self.cliente)

        respuesta = self.client.post(reverse(
            'eliminar_evidencia',
            args=[self.orden.pk, self.evidencia.pk],
        ))

        self.assertRedirects(
            respuesta,
            f'{reverse("orden_detalle", args=[self.orden.pk])}#evidencias',
            fetch_redirect_response=False,
        )
        self.assertFalse(
            EvidenciaSintoma.objects.filter(pk=self.evidencia.pk).exists()
        )

    def test_admin_puede_eliminar_evidencia(self):
        self.client.force_login(self.admin)

        respuesta = self.client.post(reverse(
            'eliminar_evidencia',
            args=[self.orden.pk, self.evidencia.pk],
        ))

        self.assertEqual(respuesta.status_code, 302)
        self.assertFalse(
            EvidenciaSintoma.objects.filter(pk=self.evidencia.pk).exists()
        )

    def test_cliente_no_puede_editar_evidencia_de_otra_orden(self):
        self.client.force_login(self.otro_cliente)

        respuesta = self.client.post(
            reverse(
                'editar_evidencia',
                args=[self.orden.pk, self.evidencia.pk],
            ),
            {
                'narrativa_cliente': 'Texto no autorizado.',
                'nivel_riesgo': 'PRECAUCION',
            },
        )

        self.assertEqual(respuesta.status_code, 403)
        self.evidencia.refresh_from_db()
        self.assertEqual(self.evidencia.narrativa_cliente, 'Ruido al girar.')
