from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import MensajeOrden, OrdenFalla


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='mecanico',
            password='Clave-segura-123',
        )

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get('/workshop/orden/nueva/')

        self.assertRedirects(
            response,
            '/login/?next=/workshop/orden/nueva/',
        )

    def test_user_can_log_in_and_view_the_homepage(self):
        response = self.client.post(
            '/login/',
            {'username': 'mecanico', 'password': 'Clave-segura-123'},
        )

        self.assertRedirects(response, '/')
        homepage = self.client.get('/')
        self.assertEqual(homepage.status_code, 200)
        self.assertContains(homepage, 'Área de cliente')
        self.assertNotContains(homepage, 'Crear orden')
        self.assertNotContains(homepage, 'Diagnóstico')

    def test_customer_cannot_open_staff_pages(self):
        self.client.force_login(self.user)

        for path in (
            '/workshop/orden/nueva/',
            '/workshop/orden/lista/',
            '/api/diagnostico/analizar/1/',
            '/api/distribucion/configurar/1/',
        ):
            with self.subTest(path=path):
                self.assertRedirects(self.client.get(path), '/')

    def test_staff_user_sees_and_can_open_staff_pages(self):
        staff_user = get_user_model().objects.create_user(
            username='administrador',
            password='Clave-segura-789',
            is_staff=True,
        )
        self.client.force_login(staff_user)

        homepage = self.client.get('/')
        self.assertContains(homepage, 'Crear orden')
        self.assertEqual(self.client.get('/workshop/orden/nueva/').status_code, 200)

    def test_public_user_can_register_and_is_logged_in(self):
        response = self.client.post(
            '/registro/',
            {
                'username': 'nuevo',
                'password1': 'Clave-segura-456',
                'password2': 'Clave-segura-456',
            },
        )

        self.assertRedirects(response, '/')
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_customer_can_create_an_order_for_their_account(self):
        self.client.force_login(self.user)

        response = self.client.post(
            '/workshop/cliente/orden/nueva/',
            {
                'vehiculo': 'Toyota Corolla 2021',
                'placa': 'ABC123',
                'kilometraje_ingreso': 54000,
                'sintoma': 'Vibra al frenar',
            },
        )

        self.assertRedirects(response, '/workshop/cliente/ordenes/')
        orden = OrdenFalla.objects.get()
        self.assertEqual(orden.cliente, self.user)
        self.assertEqual(orden.estado, 'PRE_DIAGNOSTICO')
        self.assertEqual(orden.evidencias.get().narrativa_cliente, 'Vibra al frenar')

    def test_customer_sees_only_their_own_active_orders(self):
        own_order = OrdenFalla.objects.create(
            cliente=self.user,
            taller='AutoDiag AI',
            vehiculo='Vehículo propio',
            kilometraje_ingreso=1000,
        )
        other_user = get_user_model().objects.create_user(
            username='otro-cliente',
            password='Clave-segura-456',
        )
        other_order = OrdenFalla.objects.create(
            cliente=other_user,
            taller='AutoDiag AI',
            vehiculo='Vehículo ajeno',
            kilometraje_ingreso=2000,
        )
        delivered_order = OrdenFalla.objects.create(
            cliente=self.user,
            taller='AutoDiag AI',
            vehiculo='Vehículo entregado',
            kilometraje_ingreso=3000,
            estado='ENTREGADO',
        )
        self.client.force_login(self.user)

        response = self.client.get('/workshop/cliente/ordenes/')

        self.assertContains(response, own_order.codigo_orden)
        self.assertNotContains(response, other_order.codigo_orden)
        self.assertNotContains(response, delivered_order.codigo_orden)

    def test_logout_ends_the_session(self):
        self.client.force_login(self.user)

        response = self.client.post('/logout/')

        self.assertRedirects(response, '/login/')
        self.assertRedirects(self.client.get('/'), '/login/?next=/')


class OrderManagementTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.customer = user_model.objects.create_user(
            username='cliente',
            password='Clave-segura-123',
        )
        self.mechanic = user_model.objects.create_user(
            username='mecanico_staff',
            password='Clave-segura-456',
            is_staff=True,
        )
        self.order = OrdenFalla.objects.create(
            cliente=self.customer,
            taller='AutoDiag AI',
            vehiculo='Toyota Corolla 2021',
            kilometraje_ingreso=54000,
        )
        self.client.force_login(self.mechanic)

    def test_staff_can_assign_a_mechanic_and_update_vehicle_status(self):
        response = self.client.post(
            f'/workshop/orden/{self.order.pk}/',
            {
                'estado': 'EN_TALLER',
                'mecanico_asignado': self.mechanic.pk,
            },
        )

        self.assertRedirects(response, f'/workshop/orden/{self.order.pk}/')
        self.order.refresh_from_db()
        self.assertEqual(self.order.estado, 'EN_TALLER')
        self.assertEqual(self.order.mecanico_asignado, self.mechanic)

    def test_staff_cannot_assign_a_customer_as_the_mechanic(self):
        response = self.client.post(
            f'/workshop/orden/{self.order.pk}/',
            {
                'estado': 'EN_TALLER',
                'mecanico_asignado': self.customer.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.estado, 'PRE_DIAGNOSTICO')
        self.assertIsNone(self.order.mecanico_asignado)


class TicketChatTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.customer = user_model.objects.create_user(
            username='cliente_chat',
            password='Clave-segura-123',
        )
        self.other_customer = user_model.objects.create_user(
            username='otro_cliente',
            password='Clave-segura-456',
        )
        self.mechanic = user_model.objects.create_user(
            username='mecanico_chat',
            password='Clave-segura-789',
            is_staff=True,
        )
        self.order = OrdenFalla.objects.create(
            cliente=self.customer,
            taller='AutoDiag AI',
            vehiculo='Toyota Corolla 2021',
            kilometraje_ingreso=54000,
            mecanico_asignado=self.mechanic,
        )

    def test_customer_message_is_visible_to_assigned_mechanic(self):
        self.client.force_login(self.customer)
        response = self.client.post(
            f'/workshop/orden/{self.order.pk}/enviar-mensaje/',
            {'contenido': '¿Cuándo estará listo mi vehículo?'},
        )

        self.assertRedirects(
            response,
            f'/workshop/cliente/ordenes/{self.order.pk}/',
        )
        message = MensajeOrden.objects.get()
        self.assertEqual(message.autor, self.customer)

        self.client.force_login(self.mechanic)
        response = self.client.get(f'/workshop/orden/{self.order.pk}/')
        self.assertContains(response, '¿Cuándo estará listo mi vehículo?')

    def test_mechanic_reply_is_available_to_customer_chat(self):
        self.client.force_login(self.mechanic)
        response = self.client.post(
            f'/workshop/orden/{self.order.pk}/enviar-mensaje/',
            {'contenido': 'Tu vehículo está en revisión.'},
        )

        self.assertRedirects(response, f'/workshop/orden/{self.order.pk}/')

        self.client.force_login(self.customer)
        response = self.client.get(
            f'/workshop/orden/{self.order.pk}/mensajes/',
        )
        self.assertContains(response, 'Tu vehículo está en revisión.')
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_other_customer_cannot_read_or_send_ticket_messages(self):
        self.client.force_login(self.other_customer)

        detail_response = self.client.get(
            f'/workshop/cliente/ordenes/{self.order.pk}/',
        )
        messages_response = self.client.get(
            f'/workshop/orden/{self.order.pk}/mensajes/',
        )
        send_response = self.client.post(
            f'/workshop/orden/{self.order.pk}/enviar-mensaje/',
            {'contenido': 'Mensaje no autorizado'},
        )

        self.assertEqual(detail_response.status_code, 404)
        self.assertEqual(messages_response.status_code, 403)
        self.assertEqual(send_response.status_code, 403)
        self.assertFalse(MensajeOrden.objects.exists())
