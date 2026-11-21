from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from django.utils import timezone
from datetime import timedelta

from .models import InvitacionPersonal, PerfilUsuario
from workshop.models import Etiqueta, MensajeOrden, Taller, Vehiculo, OrdenFalla


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PerfilUsuarioTests(TestCase):
    def test_signal_crea_perfil_cliente(self):
        user = User.objects.create_user('nuevo', password='ClaveSegura123')
        self.assertEqual(user.perfil.rol, PerfilUsuario.Rol.CLIENTE)

    def test_superusuario_recibe_rol_admin(self):
        user = User.objects.create_superuser('root', 'root@example.com', 'ClaveSegura123')
        self.assertEqual(user.perfil.rol, PerfilUsuario.Rol.ADMIN)

    def test_registro_publico_siempre_crea_cliente(self):
        response = self.client.post(reverse('registro'), {
            'username': 'cliente_nuevo',
            'email': 'cliente_nuevo@example.com',
            'first_name': 'Nuevo',
            'last_name': 'Cliente',
            'rol': 'ADMIN',
            'password1': 'ClaveSegura123',
            'password2': 'ClaveSegura123',
        })
        self.assertRedirects(response, reverse('dashboard'), fetch_redirect_response=False)
        user = User.objects.get(username='cliente_nuevo')
        self.assertEqual(user.perfil.rol, PerfilUsuario.Rol.CLIENTE)

    def test_login_redirige_al_panel(self):
        User.objects.create_user('cliente', password='ClaveSegura123')
        response = self.client.post(reverse('login'), {
            'username': 'cliente',
            'password': 'ClaveSegura123',
        })
        self.assertRedirects(response, reverse('dashboard'), fetch_redirect_response=False)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class InicioPorRolTests(TestCase):
    def setUp(self):
        self.taller = Taller.objects.create(nombre='Taller AutoDiag')
        self.cliente = User.objects.create_user('cliente_inicio', password='ClaveSegura123')
        self.otro_cliente = User.objects.create_user('otro_cliente', password='ClaveSegura123')
        self.vehiculo = Vehiculo.objects.create(
            placa='ABC-101',
            marca='Toyota',
            modelo='Corolla',
            anio=2024,
            cliente=self.cliente,
        )

    def test_inicio_cliente_es_portada_distinta_del_panel(self):
        orden = OrdenFalla.objects.create(
            taller=self.taller,
            vehiculo=self.vehiculo,
            cliente=self.cliente,
            kilometraje_ingreso=12500,
            estado='EN_TALLER',
        )
        self.client.login(username='cliente_inicio', password='ClaveSegura123')

        response = self.client.get(reverse('home'))

        self.assertTemplateUsed(response, 'home.html')
        self.assertTemplateNotUsed(response, 'dashboard/cliente.html')
        self.assertContains(response, 'Diagnóstico inteligente')
        self.assertNotContains(response, 'Mis órdenes recientes')
        self.assertNotContains(response, 'Toyota Corolla')

    def test_inicio_cliente_no_expone_ordenes(self):
        otro_vehiculo = Vehiculo.objects.create(
            placa='XYZ-202',
            marca='Honda',
            modelo='Civic',
            anio=2023,
            cliente=self.otro_cliente,
        )
        OrdenFalla.objects.create(
            taller=self.taller,
            vehiculo=otro_vehiculo,
            cliente=self.otro_cliente,
            kilometraje_ingreso=8000,
        )
        self.client.login(username='cliente_inicio', password='ClaveSegura123')

        response = self.client.get(reverse('home'))

        self.assertTemplateUsed(response, 'home.html')
        self.assertNotContains(response, 'XYZ-202')
        self.assertNotContains(response, 'Honda Civic')


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PersonalTests(TestCase):
    def setUp(self):
        self.taller = Taller.objects.create(nombre='Taller Edición')
        self.admin = User.objects.create_superuser(
            'admin_personal',
            'admin_personal@example.com',
            'ClaveSegura123',
        )

    def test_admin_crea_usuario_mecanico(self):
        self.client.login(username='admin_personal', password='ClaveSegura123')

        response = self.client.post(reverse('gestionar_personal'), {
            'crear_personal': '1',
            'username': 'mecanico_nuevo',
            'email': 'mecanico_nuevo@example.com',
            'first_name': 'Juan',
            'last_name': 'Técnico',
            'rol': PerfilUsuario.Rol.MECANICO,
            'especialidad': 'Motor',
            'telefono': '8095550101',
            'password1': 'ClaveSegura123',
            'password2': 'ClaveSegura123',
        })

        self.assertRedirects(response, reverse('gestionar_personal'), fetch_redirect_response=False)
        mecanico = User.objects.get(username='mecanico_nuevo')
        self.assertEqual(mecanico.perfil.rol, PerfilUsuario.Rol.MECANICO)
        self.assertEqual(mecanico.perfil.especialidad, 'Motor')

    def test_codigo_mecanico_asigna_puesto_al_registrarse(self):
        invitacion = InvitacionPersonal.objects.create(
            rol=PerfilUsuario.Rol.MECANICO,
            especialidad='Electricidad',
            telefono='8095550102',
            creado_por=self.admin,
            expira_en=timezone.now() + timedelta(days=7),
        )

        response = self.client.post(reverse('registro'), {
            'username': 'mecanico_codigo',
            'email': 'mecanico_codigo@example.com',
            'first_name': 'Carlos',
            'last_name': 'Taller',
            'codigo_puesto': invitacion.codigo,
            'password1': 'ClaveSegura123',
            'password2': 'ClaveSegura123',
        })

        self.assertRedirects(response, reverse('dashboard'), fetch_redirect_response=False)
        mecanico = User.objects.get(username='mecanico_codigo')
        self.assertEqual(mecanico.perfil.rol, PerfilUsuario.Rol.MECANICO)
        invitacion.refresh_from_db()
        self.assertEqual(invitacion.usado_por, mecanico)

    def test_codigo_invalido_no_asigna_puesto_personal(self):
        response = self.client.post(reverse('registro'), {
            'username': 'cliente_codigo',
            'email': 'cliente_codigo@example.com',
            'first_name': 'Ana',
            'last_name': 'Cliente',
            'codigo_puesto': 'NO-EXISTE',
            'password1': 'ClaveSegura123',
            'password2': 'ClaveSegura123',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'El código de puesto no es válido')
        self.assertFalse(User.objects.filter(username='cliente_codigo').exists())

    def test_admin_actualiza_puesto_de_usuario_registrado(self):
        usuario = User.objects.create_user(
            'cliente_cambio',
            email='cliente_cambio@example.com',
            password='ClaveSegura123',
        )
        self.client.login(username='admin_personal', password='ClaveSegura123')

        response = self.client.post(reverse('gestionar_usuarios'), {
            'accion': 'actualizar',
            'usuario_id': usuario.pk,
            'rol': PerfilUsuario.Rol.MECANICO,
            'telefono': '8095551111',
            'especialidad': 'Suspensión',
        })

        self.assertRedirects(response, reverse('gestionar_usuarios'), fetch_redirect_response=False)
        usuario.refresh_from_db()
        self.assertEqual(usuario.perfil.rol, PerfilUsuario.Rol.MECANICO)
        self.assertEqual(usuario.perfil.especialidad, 'Suspensión')

    def test_admin_elimina_usuario_registrado(self):
        usuario = User.objects.create_user(
            'usuario_eliminable',
            email='usuario_eliminable@example.com',
            password='ClaveSegura123',
        )
        self.client.login(username='admin_personal', password='ClaveSegura123')

        response = self.client.post(reverse('gestionar_usuarios'), {
            'accion': 'eliminar',
            'usuario_id': usuario.pk,
        })

        self.assertRedirects(response, reverse('gestionar_usuarios'), fetch_redirect_response=False)
        self.assertFalse(User.objects.filter(pk=usuario.pk).exists())

    def test_usuario_no_admin_no_gestiona_usuarios(self):
        usuario = User.objects.create_user(
            'cliente_sin_permiso',
            password='ClaveSegura123',
        )
        self.client.login(username='cliente_sin_permiso', password='ClaveSegura123')

        response = self.client.get(reverse('gestionar_usuarios'))

        self.assertEqual(response.status_code, 403)

    def test_interfaz_no_muestra_django_admin(self):
        self.client.login(username='admin_personal', password='ClaveSegura123')

        response = self.client.get(reverse('gestionar_usuarios'))

        self.assertContains(response, 'Usuarios registrados')
        self.assertNotContains(response, '/admin/')

    def test_ruta_django_admin_ya_no_esta_disponible(self):
        response = self.client.get('/admin/')

        self.assertEqual(response.status_code, 404)

    def test_admin_edita_datos_y_etiquetas_de_una_orden(self):
        cliente = User.objects.create_user(
            'cliente_edicion',
            email='cliente_edicion@example.com',
            password='ClaveSegura123',
        )
        vehiculo = Vehiculo.objects.create(
            placa='OLD-001',
            marca='Toyota',
            modelo='Corolla',
            anio=2022,
            cliente=cliente,
        )
        orden = OrdenFalla.objects.create(
            taller=self.taller,
            vehiculo=vehiculo,
            cliente=cliente,
            kilometraje_ingreso=10000,
        )
        etiqueta_existente = Etiqueta.objects.create(
            nombre='#Motor',
            color='#f59e0b',
        )
        orden.etiquetas.add(etiqueta_existente)
        self.client.login(username='admin_personal', password='ClaveSegura123')

        response = self.client.post(reverse('editar_orden', args=[orden.pk]), {
            'cliente': cliente.pk,
            'nombre_cliente_walkin': '',
            'telefono_cliente_walkin': '',
            'taller': self.taller.pk,
            'mecanico_asignado': '',
            'kilometraje_ingreso': 14500,
            'etiquetas': [etiqueta_existente.pk],
            'placa': 'NEW-001',
            'marca': 'Honda',
            'modelo': 'Civic',
            'anio': 2024,
            'motor': '1.5 Turbo',
            'color': 'Gris',
            'nuevas_etiquetas': 'Urgente, Garantía',
        })

        self.assertRedirects(
            response,
            reverse('orden_detalle', args=[orden.pk]),
            fetch_redirect_response=False,
        )
        orden.refresh_from_db()
        vehiculo.refresh_from_db()
        self.assertEqual(orden.kilometraje_ingreso, 14500)
        self.assertEqual(vehiculo.placa, 'NEW-001')
        self.assertEqual(vehiculo.marca, 'Honda')
        self.assertTrue(orden.etiquetas.filter(nombre='#Urgente').exists())
        self.assertTrue(orden.etiquetas.filter(nombre='#Garantía').exists())

    def test_admin_puede_quitar_y_agregar_etiquetas_en_edicion(self):
        cliente = User.objects.create_user(
            'cliente_etiquetas',
            email='cliente_etiquetas@example.com',
            password='ClaveSegura123',
        )
        vehiculo = Vehiculo.objects.create(
            placa='TAG-001',
            marca='Mazda',
            modelo='3',
            anio=2021,
            cliente=cliente,
        )
        orden = OrdenFalla.objects.create(
            taller=self.taller,
            vehiculo=vehiculo,
            cliente=cliente,
            kilometraje_ingreso=8000,
        )
        etiqueta_vieja = Etiqueta.objects.create(nombre='#Revisión', color='#64748b')
        orden.etiquetas.add(etiqueta_vieja)
        self.client.login(username='admin_personal', password='ClaveSegura123')

        response = self.client.post(reverse('editar_orden', args=[orden.pk]), {
            'cliente': cliente.pk,
            'nombre_cliente_walkin': '',
            'telefono_cliente_walkin': '',
            'taller': self.taller.pk,
            'mecanico_asignado': '',
            'kilometraje_ingreso': 9000,
            'etiquetas': [],
            'placa': 'TAG-001',
            'marca': 'Mazda',
            'modelo': '3',
            'anio': 2021,
            'motor': '',
            'color': '',
            'nuevas_etiquetas': 'Urgente',
        })

        self.assertRedirects(
            response,
            reverse('orden_detalle', args=[orden.pk]),
            fetch_redirect_response=False,
        )
        orden.refresh_from_db()
        self.assertFalse(orden.etiquetas.filter(pk=etiqueta_vieja.pk).exists())
        self.assertTrue(orden.etiquetas.filter(nombre='#Urgente').exists())

    def test_pantallas_nueva_y_edicion_organizan_etiquetas(self):
        cliente = User.objects.create_user(
            'cliente_layout',
            email='cliente_layout@example.com',
            password='ClaveSegura123',
        )
        vehiculo = Vehiculo.objects.create(
            placa='LAY-001',
            marca='Nissan',
            modelo='Sentra',
            anio=2023,
            cliente=cliente,
        )
        orden = OrdenFalla.objects.create(
            taller=self.taller,
            vehiculo=vehiculo,
            cliente=cliente,
            kilometraje_ingreso=5000,
        )
        self.client.login(username='admin_personal', password='ClaveSegura123')

        nueva = self.client.get(reverse('orden_nueva'))
        edicion = self.client.get(reverse('editar_orden', args=[orden.pk]))

        self.assertContains(nueva, 'Etiquetas disponibles')
        self.assertContains(nueva, 'Etiquetas nuevas')
        self.assertContains(nueva, 'Etiquetas sugeridas')
        self.assertContains(edicion, 'Etiquetas existentes')
        self.assertContains(edicion, 'Etiquetas nuevas')

    def test_detalle_muestra_menu_lateral_y_chat_no_leido(self):
        cliente = User.objects.create_user(
            'cliente_menu',
            email='cliente_menu@example.com',
            password='ClaveSegura123',
        )
        mecanico = User.objects.create_user(
            'mecanico_menu',
            password='ClaveSegura123',
        )
        mecanico.perfil.rol = PerfilUsuario.Rol.MECANICO
        mecanico.perfil.save(update_fields=['rol'])
        vehiculo = Vehiculo.objects.create(
            placa='MENU-001',
            marca='Toyota',
            modelo='Hilux',
            anio=2024,
            cliente=cliente,
        )
        orden = OrdenFalla.objects.create(
            taller=self.taller,
            vehiculo=vehiculo,
            cliente=cliente,
            mecanico_asignado=mecanico,
            kilometraje_ingreso=12000,
        )
        MensajeOrden.objects.create(
            orden=orden,
            autor=cliente,
            contenido='¿Hay novedades con el trabajo?',
        )
        self.client.login(username='mecanico_menu', password='ClaveSegura123')

        detalle = self.client.get(reverse('orden_detalle', args=[orden.pk]))
        lista = self.client.get(reverse('orden_lista'))

        self.assertContains(detalle, 'data-order-section="chat"')
        self.assertContains(detalle, 'Presupuesto')
        self.assertContains(detalle, 'Diagnóstico IA')
        self.assertContains(detalle, 'Distribución')
        self.assertContains(detalle, 'unread-badge')
        self.assertEqual(detalle.context['mensajes_no_leidos'], 1)

        chat = self.client.get(reverse('mensajes_orden', args=[orden.pk]))
        self.assertEqual(chat.status_code, 200)
        mensajes = MensajeOrden.objects.filter(orden=orden).first()
        self.assertTrue(mensajes.leidos_por.filter(pk=mecanico.pk).exists())
