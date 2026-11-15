from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import PerfilUsuario


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
