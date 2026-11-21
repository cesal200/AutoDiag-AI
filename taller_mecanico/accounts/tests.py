from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import PerfilUsuario
from workshop.models import Taller, Vehiculo, OrdenFalla


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
