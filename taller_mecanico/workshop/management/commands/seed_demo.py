from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import PerfilUsuario
from diagnostico_ia.services import procesar_orden
from workshop.models import (
    Etiqueta,
    EvidenciaSintoma,
    ItemPresupuestoRepuestos,
    OrdenFalla,
    Taller,
    Vehiculo,
)

DEMO_PASSWORD = 'demo12345'


class Command(BaseCommand):
    help = 'Crea usuarios y órdenes de demostración para probar los roles y paneles.'

    def _crear_usuario(self, username, email, rol, **extra):
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={'email': email, **extra},
        )
        user.set_password(DEMO_PASSWORD)
        for campo, valor in extra.items():
            setattr(user, campo, valor)
        user.save()

        perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
        perfil.rol = rol
        perfil.save(update_fields=['rol'])
        return user

    def _crear_orden(self, vehiculo, taller, cliente=None, walkin_nombre='', walkin_telefono='', **extra):
        orden = OrdenFalla.objects.filter(vehiculo=vehiculo).first()
        if orden:
            return orden, False
        orden = OrdenFalla.objects.create(
            vehiculo=vehiculo,
            cliente=cliente,
            nombre_cliente_walkin=walkin_nombre,
            telefono_cliente_walkin=walkin_telefono,
            taller=taller,
            kilometraje_ingreso=extra.pop('kilometraje_ingreso', 85000),
            **extra,
        )
        return orden, True

    def handle(self, *args, **options):
        admin = self._crear_usuario(
            'admin', 'admin@autodiag.local', PerfilUsuario.Rol.ADMIN,
            is_staff=True, is_superuser=True, first_name='Administrador',
        )
        asesor = self._crear_usuario(
            'asesor', 'asesor@autodiag.local', PerfilUsuario.Rol.ASESOR,
            first_name='Asesor',
        )
        tecnico = self._crear_usuario(
            'tecnico', 'tecnico@autodiag.local', PerfilUsuario.Rol.MECANICO,
            first_name='Técnico',
        )
        cliente = self._crear_usuario(
            'cliente', 'cliente@autodiag.local', PerfilUsuario.Rol.CLIENTE,
            first_name='Ana', last_name='García',
        )

        motor, _ = Etiqueta.objects.get_or_create(nombre='#Motor', defaults={'color': '#f59e0b'})
        frenos, _ = Etiqueta.objects.get_or_create(nombre='#Frenos', defaults={'color': '#ef4444'})
        taller, _ = Taller.objects.get_or_create(nombre='Taller AutoDiag')
        vehiculo_cliente, _ = Vehiculo.objects.get_or_create(
            placa='DEMO001',
            defaults={
                'marca': 'Toyota',
                'modelo': 'Corolla',
                'anio': 2021,
                'motor': '1.8',
                'cliente': cliente,
            },
        )
        vehiculo_walkin, _ = Vehiculo.objects.get_or_create(
            placa='DEMO002',
            defaults={'marca': 'Honda', 'modelo': 'Civic', 'anio': 2018, 'motor': '1.5'},
        )
        vehiculo_entregado, _ = Vehiculo.objects.get_or_create(
            placa='DEMO003',
            defaults={'marca': 'BMW', 'modelo': 'X5', 'anio': 2020, 'motor': '3.0'},
        )

        orden_cliente, creada = self._crear_orden(
            vehiculo_cliente,
            taller,
            cliente=cliente,
            kilometraje_ingreso=45200,
            estado='EN_TALLER',
            mecanico_asignado=tecnico,
        )
        if creada:
            orden_cliente.etiquetas.add(motor)
            EvidenciaSintoma.objects.create(
                orden=orden_cliente,
                narrativa_cliente='Vibración al acelerar y luz de motor encendida.',
                nivel_riesgo='PRECAUCION',
            )
            ItemPresupuestoRepuestos.objects.create(
                orden=orden_cliente,
                tipo='REPUESTO',
                descripcion='Juego de bujías',
                cantidad=4,
                precio_unitario=Decimal('12.50'),
            )
            ItemPresupuestoRepuestos.objects.create(
                orden=orden_cliente,
                tipo='MANO_OBRA',
                descripcion='Diagnóstico y ajuste de inyección',
                cantidad=1,
                precio_unitario=Decimal('80.00'),
            )
            procesar_orden(orden_cliente)

        orden_walkin, creada = self._crear_orden(
            vehiculo_walkin,
            taller,
            walkin_nombre='Luis Pérez',
            walkin_telefono='+58 412 555 0101',
            kilometraje_ingreso=91000,
            estado='PRE_DIAGNOSTICO',
        )
        if creada:
            orden_walkin.etiquetas.add(frenos)
            EvidenciaSintoma.objects.create(
                orden=orden_walkin,
                narrativa_cliente='Ruido al frenar y pedal esponjoso.',
                nivel_riesgo='NO_MOVER_GRUA',
            )
            procesar_orden(orden_walkin)

        orden_entregada, creada = self._crear_orden(
            vehiculo_entregado,
            taller,
            cliente=cliente,
            kilometraje_ingreso=38000,
            estado='ENTREGADO',
            mecanico_asignado=tecnico,
        )
        if creada:
            orden_entregada.etiquetas.add(motor)

        self.stdout.write(self.style.SUCCESS('Datos demo listos.'))
        self.stdout.write('  admin / demo12345   (ADMIN, superuser)')
        self.stdout.write('  asesor / demo12345  (ASESOR)')
        self.stdout.write('  tecnico / demo12345 (MECANICO)')
        self.stdout.write('  cliente / demo12345 (CLIENTE)')
        self.stdout.write(f'  Orden walk-in: {orden_walkin.codigo_orden}')
        self.stdout.write(f'  Token walk-in: /seguimiento/{orden_walkin.token_publico}/')
