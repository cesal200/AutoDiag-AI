import time
import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import PerfilUsuario
from diagnostico_ia.services import procesar_orden

from .models import (
    EvidenciaSintoma,
    ItemPresupuestoRepuestos,
    MensajeOrden,
    OrdenFalla,
    Taller,
    Vehiculo,
)


class BaseWorkshopTest(TestCase):
    def setUp(self):
        self.taller = Taller.objects.create(nombre='Taller AutoDiag')
        self.admin = User.objects.create(
            username='admin', email='admin@example.com', is_staff=True, is_superuser=True
        )
        self.asesor = User.objects.create(username='asesor', email='asesor@example.com')
        self.asesor.perfil.rol = PerfilUsuario.Rol.ASESOR
        self.asesor.perfil.save(update_fields=['rol'])
        self.tecnico = User.objects.create(username='tecnico', email='tecnico@example.com')
        self.tecnico.perfil.rol = PerfilUsuario.Rol.MECANICO
        self.tecnico.perfil.save(update_fields=['rol'])
        self.cliente = User.objects.create(username='cliente', email='cliente@example.com')
        self.otro_cliente = User.objects.create(username='otro', email='otro@example.com')
        self._secuencia_placa = 0
        self.vehiculo = self.crear_vehiculo(cliente=self.cliente)

    def crear_vehiculo(self, placa=None, **kwargs):
        self._secuencia_placa += 1
        datos = {
            'placa': placa or f'ABC{self._secuencia_placa:03d}',
            'marca': 'Toyota',
            'modelo': 'Corolla',
            'anio': 2022,
            'motor': '1.8',
            'color': 'Gris',
        }
        datos.update(kwargs)
        return Vehiculo.objects.create(**datos)

    def crear_orden(self, vehiculo=None, cliente=None, mecanico=None, **kwargs):
        datos = {
            'taller': self.taller,
            'vehiculo': vehiculo or self.crear_vehiculo(),
            'cliente': cliente,
            'mecanico_asignado': mecanico,
            'kilometraje_ingreso': 50000,
        }
        datos.update(kwargs)
        return OrdenFalla.objects.create(**datos)


class OrdenModelTests(BaseWorkshopTest):
    def test_genera_codigo_secuencial_y_ticket(self):
        primera = self.crear_orden()
        segunda = self.crear_orden()
        self.assertNotEqual(primera.codigo_orden, segunda.codigo_orden)
        self.assertTrue(primera.codigo_orden.startswith('OR-'))
        self.assertTrue(segunda.codigo_orden.endswith('002'))
        self.assertTrue(primera.ticket.startswith('TKT-'))
        self.assertNotEqual(primera.ticket, segunda.ticket)

    def test_genera_token_y_expiracion(self):
        orden = self.crear_orden(cliente=self.cliente)
        self.assertIsNotNone(orden.token_publico)
        self.assertIsNotNone(orden.token_expira_en)
        self.assertTrue(orden.token_vigente)

    def test_transiciones_validas_e_invalidas(self):
        orden = self.crear_orden(cliente=self.cliente)
        self.assertTrue(orden.puede_transicionar_a('EN_TALLER'))
        self.assertFalse(orden.puede_transicionar_a('ENTREGADO'))
        with self.assertRaises(ValidationError):
            orden.cambiar_estado('ENTREGADO')
        orden.cambiar_estado('EN_TALLER')
        self.assertEqual(orden.estado, 'EN_TALLER')

    def test_walkin_sin_identificacion_no_valida(self):
        orden = OrdenFalla(
            taller=self.taller,
            vehiculo=self.vehiculo,
            kilometraje_ingreso=1000,
        )
        with self.assertRaises(ValidationError):
            orden.full_clean()

    def test_vehiculo_placa_unica(self):
        with self.assertRaises(Exception):
            self.crear_vehiculo(placa=self.vehiculo.placa)

    def test_item_presupuesto_rechaza_cantidad_negativa(self):
        orden = self.crear_orden(cliente=self.cliente)
        item = ItemPresupuestoRepuestos(
            orden=orden,
            tipo='REPUESTO',
            descripcion='Filtro',
            cantidad=0,
            precio_unitario='10.00',
        )
        with self.assertRaises(ValidationError):
            item.full_clean()


class OrdenPermissionTests(BaseWorkshopTest):
    def test_cliente_solo_ve_sus_ordenes(self):
        vehiculo_propio = self.crear_vehiculo(placa='PROPIA')
        vehiculo_ajeno = self.crear_vehiculo(placa='AJENA')
        propia = self.crear_orden(vehiculo=vehiculo_propio, cliente=self.cliente)
        ajena = self.crear_orden(vehiculo=vehiculo_ajeno, cliente=self.otro_cliente)
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('orden_lista'))
        self.assertContains(response, propia.vehiculo.placa)
        self.assertNotContains(response, ajena.vehiculo.placa)

    def test_tecnico_solo_ve_asignadas(self):
        asignada = self.crear_orden(cliente=self.cliente, mecanico=self.tecnico)
        no_asignada = self.crear_orden(cliente=self.cliente)
        self.client.force_login(self.tecnico)
        response = self.client.get(reverse('orden_lista'))
        self.assertContains(response, asignada.vehiculo.placa)
        self.assertNotContains(response, no_asignada.vehiculo.placa)

    def test_cliente_no_ve_orden_ajena(self):
        ajena = self.crear_orden(cliente=self.otro_cliente)
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('orden_detalle', args=[ajena.pk]))
        self.assertEqual(response.status_code, 403)

    def test_pdf_ajeno_devuelve_403(self):
        ajena = self.crear_orden(cliente=self.otro_cliente)
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('generar_pdf', args=[ajena.pk]))
        self.assertEqual(response.status_code, 403)

    def test_tecnico_no_puede_crear_orden(self):
        self.client.force_login(self.tecnico)
        response = self.client.post(reverse('orden_nueva'), {
            'taller': self.taller.pk,
            'placa': 'NEW001',
            'marca': 'Honda',
            'modelo': 'Civic',
            'anio': 2020,
            'kilometraje_ingreso': 1000,
        })
        self.assertEqual(response.status_code, 403)

    def test_cliente_crea_orden_propia_con_vehiculo(self):
        self.client.force_login(self.cliente)
        response = self.client.post(reverse('orden_nueva'), {
            'taller': self.taller.pk,
            'placa': 'NEW123',
            'marca': 'Toyota',
            'modelo': 'Corolla',
            'anio': 2022,
            'kilometraje_ingreso': 12000,
        })
        self.assertEqual(response.status_code, 302)
        orden = OrdenFalla.objects.get(vehiculo__placa='NEW123')
        self.assertEqual(orden.cliente, self.cliente)
        self.assertEqual(orden.estado, 'PRE_DIAGNOSTICO')

    def test_admin_crea_orden_walkin(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('orden_nueva'), {
            'taller': self.taller.pk,
            'placa': 'WALK01',
            'marca': 'Honda',
            'modelo': 'Civic',
            'anio': 2018,
            'nombre_cliente_walkin': 'Luis Pérez',
            'telefono_cliente_walkin': '+58 412 555 0101',
            'kilometraje_ingreso': 91000,
        })
        self.assertEqual(response.status_code, 302)
        orden = OrdenFalla.objects.get(vehiculo__placa='WALK01')
        self.assertIsNone(orden.cliente)
        self.assertEqual(orden.nombre_cliente_walkin, 'Luis Pérez')
        self.assertTrue(orden.es_walkin)

    def test_walkin_sin_nombre_no_se_crea(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('orden_nueva'), {
            'taller': self.taller.pk,
            'placa': 'WALK02',
            'marca': 'Honda',
            'modelo': 'Civic',
            'anio': 2018,
            'kilometraje_ingreso': 1000,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(OrdenFalla.objects.filter(vehiculo__placa='WALK02').exists())

    def test_tecnico_no_asigna_mecanico(self):
        orden = self.crear_orden(cliente=self.cliente, mecanico=self.tecnico)
        self.client.force_login(self.tecnico)
        response = self.client.post(reverse('asignar_mecanico', args=[orden.pk]), {
            'mecanico_asignado': '',
        })
        self.assertEqual(response.status_code, 403)

    def test_cliente_aprueba_su_item(self):
        orden = self.crear_orden(cliente=self.cliente)
        item = ItemPresupuestoRepuestos.objects.create(
            orden=orden, tipo='REPUESTO', descripcion='Filtro', cantidad=1, precio_unitario='10.00'
        )
        self.client.force_login(self.cliente)
        response = self.client.post(reverse('aprobar_item', args=[orden.pk, item.pk]))
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertTrue(item.aprobado_cliente)

    def test_tecnico_no_aprueba_item(self):
        orden = self.crear_orden(cliente=self.cliente, mecanico=self.tecnico)
        item = ItemPresupuestoRepuestos.objects.create(
            orden=orden, tipo='REPUESTO', descripcion='Filtro', cantidad=1, precio_unitario='10.00'
        )
        self.client.force_login(self.tecnico)
        response = self.client.post(reverse('aprobar_item', args=[orden.pk, item.pk]))
        self.assertEqual(response.status_code, 403)

    def test_cliente_puede_agregar_evidencia(self):
        orden = self.crear_orden(cliente=self.cliente)
        self.client.force_login(self.cliente)
        response = self.client.post(reverse('agregar_evidencia', args=[orden.pk]), {
            'narrativa_cliente': 'El motor hace un ruido leve y vibra al acelerar.',
            'nivel_riesgo': 'PRECAUCION',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(orden.evidencias.exists())
        self.assertTrue(orden.analisis_ia.exists())

    def test_filtros_de_orden(self):
        vehiculo = self.crear_vehiculo(placa='FILT01', marca='Mazda', modelo='3')
        orden = self.crear_orden(vehiculo=vehiculo, cliente=self.cliente, mecanico=self.tecnico)
        self.client.force_login(self.admin)
        response = self.client.get(reverse('orden_lista'), {'q': 'FILT01'})
        self.assertContains(response, orden.codigo_orden)
        response = self.client.get(reverse('orden_lista'), {'mecanico': self.tecnico.pk})
        self.assertContains(response, orden.codigo_orden)
        response = self.client.get(reverse('orden_lista'), {'estado': 'PRE_DIAGNOSTICO'})
        self.assertContains(response, orden.codigo_orden)


class TrackingTests(BaseWorkshopTest):
    def test_token_valido_muestra_seguimiento(self):
        orden = self.crear_orden(cliente=self.cliente)
        response = self.client.get(reverse('seguimiento_publico', args=[orden.token_publico]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, orden.codigo_orden)


class ChatTicketTests(BaseWorkshopTest):
    def test_cliente_envia_mensaje_a_su_ticket(self):
        orden = self.crear_orden(cliente=self.cliente)
        self.client.force_login(self.cliente)

        response = self.client.post(
            reverse('enviar_mensaje_orden', args=[orden.pk]),
            {'contenido': 'Necesito una actualización del diagnóstico.'},
        )

        self.assertEqual(response.status_code, 302)
        mensaje = MensajeOrden.objects.get(orden=orden)
        self.assertEqual(mensaje.autor, self.cliente)
        self.assertIn('actualización', mensaje.contenido)

    def test_cliente_no_envia_mensaje_en_ticket_ajeno(self):
        orden = self.crear_orden(cliente=self.otro_cliente)
        self.client.force_login(self.cliente)

        response = self.client.post(
            reverse('enviar_mensaje_orden', args=[orden.pk]),
            {'contenido': 'Mensaje no autorizado'},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(MensajeOrden.objects.filter(orden=orden).exists())

    def test_refresco_muestra_mensajes_del_ticket(self):
        orden = self.crear_orden(cliente=self.cliente)
        MensajeOrden.objects.create(
            orden=orden,
            autor=self.asesor,
            contenido='El vehículo ya está en revisión.',
        )
        self.client.force_login(self.cliente)

        response = self.client.get(reverse('mensajes_orden', args=[orden.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'El vehículo ya está en revisión.')

    def test_token_expirado_devuelve_404(self):
        orden = self.crear_orden(cliente=self.cliente)
        OrdenFalla.objects.filter(pk=orden.pk).update(
            token_expira_en=timezone.now() - timedelta(days=1)
        )
        response = self.client.get(reverse('seguimiento_publico', args=[orden.token_publico]))
        self.assertEqual(response.status_code, 404)

    def test_token_desconocido_devuelve_404(self):
        response = self.client.get(reverse('seguimiento_publico', args=[uuid.uuid4()]))
        self.assertEqual(response.status_code, 404)

    def test_regenerar_token_invalida_el_anterior(self):
        orden = self.crear_orden(cliente=self.cliente)
        token_anterior = orden.token_publico
        self.client.force_login(self.admin)
        response = self.client.post(reverse('regenerar_token', args=[orden.pk]))
        self.assertEqual(response.status_code, 302)
        orden.refresh_from_db()
        self.assertNotEqual(orden.token_publico, token_anterior)
        response = self.client.get(reverse('seguimiento_publico', args=[token_anterior]))
        self.assertEqual(response.status_code, 404)


class ClienteRapidoTests(BaseWorkshopTest):
    def test_admin_crea_cliente_rapido(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('cliente_rapido'), {
            'nombre_completo': 'María López',
            'email': 'maria@example.com',
            'telefono': '+58 414 000 0000',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='maria@example.com')
        self.assertEqual(user.perfil.rol, PerfilUsuario.Rol.CLIENTE)
        self.assertFalse(user.has_usable_password())

    def test_email_duplicado_se_rechaza(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('cliente_rapido'), {
            'nombre_completo': 'Cliente Duplicado',
            'email': self.cliente.email,
            'telefono': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email=self.cliente.email).count(), 1)

    def test_cliente_no_puede_crear_cliente_rapido(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('cliente_rapido'))
        self.assertEqual(response.status_code, 403)


class DashboardTests(BaseWorkshopTest):
    def test_redireccion_por_rol(self):
        casos = [
            (self.admin, 'dashboard_admin'),
            (self.asesor, 'dashboard_admin'),
            (self.tecnico, 'dashboard_tecnico'),
            (self.cliente, 'dashboard_cliente'),
        ]
        for user, destino in casos:
            self.client.force_login(user)
            response = self.client.get(reverse('dashboard'))
            self.assertRedirects(response, reverse(destino), fetch_redirect_response=False)

    def test_cliente_no_accede_al_panel_admin(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('dashboard_admin'))
        self.assertEqual(response.status_code, 403)

    def test_anonimo_redirige_al_login(self):
        response = self.client.get(reverse('orden_lista'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)


class VehiculoTests(BaseWorkshopTest):
    def test_admin_registra_vehiculo(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('vehiculo_nueva'), {
            'placa': 'VEH001',
            'marca': 'Ford',
            'modelo': 'Focus',
            'anio': 2019,
            'motor': '2.0',
            'color': 'Azul',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Vehiculo.objects.filter(placa='VEH001').exists())

    def test_cliente_solo_puede_registrar_su_vehiculo(self):
        self.client.force_login(self.cliente)
        response = self.client.post(reverse('vehiculo_nueva'), {
            'placa': 'VEH002',
            'marca': 'Ford',
            'modelo': 'Focus',
            'anio': 2019,
            'cliente': self.otro_cliente.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Vehiculo.objects.get(placa='VEH002').cliente, self.cliente)


class EvidenciaYPDFTests(BaseWorkshopTest):
    def test_evidencia_guardada(self):
        orden = self.crear_orden(cliente=self.cliente)
        evidencia = EvidenciaSintoma.objects.create(
            orden=orden,
            narrativa_cliente='Ruido en la suspensión delantera.',
        )
        self.assertEqual(evidencia.orden, orden)

    def test_descarga_pdf(self):
        orden = self.crear_orden(cliente=self.cliente)
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('descargar_pdf', args=[orden.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_pdf_completo_con_evidencias_presupuesto_y_analisis(self):
        orden = self.crear_orden(cliente=self.cliente, mecanico=self.tecnico)
        EvidenciaSintoma.objects.create(
            orden=orden,
            narrativa_cliente='Vibración del motor y testigo de falla encendido.',
            nivel_riesgo='PRECAUCION',
        )
        ItemPresupuestoRepuestos.objects.create(
            orden=orden, tipo='REPUESTO', descripcion='Bujías', cantidad=4,
            precio_unitario='12.50',
        )
        procesar_orden(orden)
        self.client.force_login(self.admin)
        response = self.client.get(reverse('descargar_pdf', args=[orden.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF'))
        self.assertGreater(len(response.content), 1000)

    def test_pdf_sin_datos_opcionales(self):
        orden = self.crear_orden(cliente=None, nombre_cliente_walkin='Cliente sin cuenta')
        self.client.force_login(self.admin)
        response = self.client.get(reverse('descargar_pdf', args=[orden.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_pdf_en_menos_de_30_segundos(self):
        orden = self.crear_orden(cliente=self.cliente)
        self.client.force_login(self.cliente)
        inicio = time.monotonic()
        response = self.client.get(reverse('descargar_pdf', args=[orden.pk]))
        duracion = time.monotonic() - inicio
        self.assertEqual(response.status_code, 200)
        self.assertLess(duracion, 30)


class CicloOrdenTests(BaseWorkshopTest):
    def test_ciclo_completo_de_orden(self):
        orden = self.crear_orden(cliente=self.cliente)
        self.client.force_login(self.admin)

        response = self.client.post(reverse('asignar_mecanico', args=[orden.pk]), {
            'mecanico_asignado': self.tecnico.pk,
        })
        self.assertEqual(response.status_code, 302)

        for estado in ['EN_TALLER', 'ESPERA_REPUESTO', 'LISTO', 'ENTREGADO']:
            response = self.client.post(reverse('cambiar_estado', args=[orden.pk]), {
                'estado': estado,
            })
            self.assertEqual(response.status_code, 302)

        orden.refresh_from_db()
        self.assertEqual(orden.estado, 'ENTREGADO')
        self.assertEqual(orden.mecanico_asignado, self.tecnico)

        response = self.client.post(reverse('agregar_item', args=[orden.pk]), {
            'tipo': 'MANO_OBRA',
            'descripcion': 'Diagnóstico final',
            'cantidad': 1,
            'precio_unitario': '50.00',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(orden.items_presupuesto.exists())

        response = self.client.post(reverse('agregar_evidencia', args=[orden.pk]), {
            'narrativa_cliente': 'Ruido en la suspensión delantera.',
            'nivel_riesgo': 'PRECAUCION',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(orden.analisis_ia.exists())

        response = self.client.get(reverse('generar_pdf', args=[orden.pk]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('descargar_pdf', args=[orden.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF'))
