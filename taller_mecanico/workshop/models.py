import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import IntegrityError, models, transaction
from django.utils import timezone


class Taller(models.Model):
    """Taller o centro de diagnóstico al que pertenece una orden."""

    nombre = models.CharField('Nombre', max_length=100, unique=True)
    direccion = models.CharField('Dirección', max_length=200, blank=True)
    telefono = models.CharField('Teléfono', max_length=30, blank=True)
    activo = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Taller'
        verbose_name_plural = 'Talleres'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Vehiculo(models.Model):
    """Vehículo registrado con los datos necesarios para el pre-diagnóstico."""

    placa = models.CharField('Placa', max_length=20, unique=True)
    marca = models.CharField('Marca', max_length=50)
    modelo = models.CharField('Modelo', max_length=50)
    anio = models.PositiveIntegerField('Año')
    motor = models.CharField('Motor', max_length=50, blank=True)
    color = models.CharField('Color', max_length=30, blank=True)
    cliente = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehiculos',
        verbose_name='Cliente',
    )
    creado_en = models.DateTimeField('Creado En', auto_now_add=True)

    class Meta:
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'
        ordering = ['placa']

    def __str__(self):
        return f'{self.placa} - {self.marca} {self.modelo} ({self.anio})'

    @property
    def descripcion(self):
        return f'{self.marca} {self.modelo} {self.anio}'


ESTADO_CHOICES = [
    ('PRE_DIAGNOSTICO', 'Pre-Diagnóstico'),
    ('EN_TALLER', 'En Taller'),
    ('ESPERA_REPUESTO', 'Espera Repuesto'),
    ('LISTO', 'Listo'),
    ('ENTREGADO', 'Entregado'),
]

RIESGO_CHOICES = [
    ('PUEDE_RODAR', 'Puede Rodar'),
    ('PRECAUCION', 'Precaución'),
    ('NO_MOVER_GRUA', 'No Mover Grúa'),
]

TRANSICIONES_ESTADO = {
    'PRE_DIAGNOSTICO': ['EN_TALLER'],
    'EN_TALLER': ['ESPERA_REPUESTO', 'LISTO'],
    'ESPERA_REPUESTO': ['EN_TALLER', 'LISTO'],
    'LISTO': ['ENTREGADO'],
    'ENTREGADO': [],
}

TOKEN_DIAS_VIGENCIA = 30


class OrdenFalla(models.Model):
    """Orden de reparación con pre-diagnóstico asistido por IA."""

    ticket = models.CharField(
        'Ticket', max_length=20, unique=True, default='', editable=False
    )
    codigo_orden = models.CharField(
        'Código de Orden', max_length=20, unique=True, default='', editable=False
    )
    taller = models.ForeignKey(
        Taller, on_delete=models.PROTECT, related_name='ordenes', verbose_name='Taller'
    )
    vehiculo = models.ForeignKey(
        Vehiculo, on_delete=models.PROTECT, related_name='ordenes', verbose_name='Vehículo'
    )
    cliente = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordenes_como_cliente',
        verbose_name='Cliente',
    )
    nombre_cliente_walkin = models.CharField(
        'Nombre del cliente (sin cuenta)', max_length=150, blank=True
    )
    telefono_cliente_walkin = models.CharField(
        'Teléfono del cliente (sin cuenta)', max_length=30, blank=True
    )
    mecanico_asignado = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordenes_asignadas',
        verbose_name='Mecánico Asignado',
    )
    kilometraje_ingreso = models.PositiveIntegerField(
        'Kilometraje Ingreso', validators=[MinValueValidator(0)]
    )
    estado = models.CharField(
        'Estado', max_length=20, choices=ESTADO_CHOICES, default='PRE_DIAGNOSTICO'
    )
    etiquetas = models.ManyToManyField('Etiqueta', blank=True, verbose_name='Etiquetas')
    token_publico = models.UUIDField(
        'Token Público', unique=True, null=True, blank=True, editable=False
    )
    token_expira_en = models.DateTimeField(
        'Token Expira En', null=True, blank=True, editable=False
    )
    creado_en = models.DateTimeField('Creado En', auto_now_add=True)
    actualizado_en = models.DateTimeField('Actualizado En', auto_now=True)

    class Meta:
        verbose_name = 'Orden de Fallo'
        verbose_name_plural = 'Órdenes de Fallo'
        ordering = ['-creado_en']

    def __str__(self):
        return f'{self.codigo_orden} - {self.vehiculo}'

    def clean(self):
        super().clean()
        if not self.cliente_id and not (self.nombre_cliente_walkin or '').strip():
            raise ValidationError({
                'nombre_cliente_walkin': (
                    'Selecciona un cliente registrado o indica el nombre del cliente walk-in.'
                )
            })

    @classmethod
    def _generar_secuencial(cls, campo, prefijo):
        with transaction.atomic():
            ultimo = (
                cls.objects.select_for_update()
                .filter(**{f'{campo}__startswith': prefijo})
                .order_by(f'-{campo}')
                .first()
            )
        consecutivo = 1
        if ultimo:
            try:
                consecutivo = int(getattr(ultimo, campo).split('-')[-1]) + 1
            except (TypeError, ValueError):
                consecutivo = cls.objects.filter(**{f'{campo}__startswith': prefijo}).count() + 1
        return f'{prefijo}{consecutivo:03d}'

    @classmethod
    def generar_codigo_orden(cls):
        anio = timezone.localdate().year
        return cls._generar_secuencial('codigo_orden', f'OR-{anio}-')

    @classmethod
    def generar_ticket(cls):
        anio = timezone.localdate().year
        return cls._generar_secuencial('ticket', f'TKT-{anio}-')

    def save(self, *args, **kwargs):
        if not self.codigo_orden:
            self.codigo_orden = self.generar_codigo_orden()
        if not self.ticket:
            self.ticket = self.generar_ticket()
        if not self.token_publico:
            self.token_publico = uuid.uuid4()
        if not self.token_expira_en:
            self.token_expira_en = timezone.now() + timedelta(days=TOKEN_DIAS_VIGENCIA)

        try:
            return super().save(*args, **kwargs)
        except IntegrityError:
            if not self._state.adding:
                raise
            if not self.codigo_orden or self.codigo_orden.startswith('OR-'):
                self.codigo_orden = self.generar_codigo_orden()
            if not self.ticket or self.ticket.startswith('TKT-'):
                self.ticket = self.generar_ticket()
            return super().save(*args, **kwargs)

    @property
    def cliente_efectivo(self):
        if self.cliente_id:
            return self.cliente.get_full_name() or self.cliente.get_username()
        return self.nombre_cliente_walkin or 'Cliente sin identificar'

    @property
    def es_walkin(self):
        return self.cliente_id is None

    @property
    def estados_siguientes(self):
        etiquetas = dict(ESTADO_CHOICES)
        return [(estado, etiquetas[estado]) for estado in TRANSICIONES_ESTADO.get(self.estado, [])]

    def puede_transicionar_a(self, nuevo_estado):
        return nuevo_estado in TRANSICIONES_ESTADO.get(self.estado, [])

    def cambiar_estado(self, nuevo_estado):
        if not self.puede_transicionar_a(nuevo_estado):
            raise ValidationError(
                f'No se puede pasar de {self.get_estado_display()} a {nuevo_estado}.'
            )
        self.estado = nuevo_estado
        self.save(update_fields=['estado', 'actualizado_en'])

    @property
    def total_presupuesto(self):
        return sum((item.subtotal for item in self.items_presupuesto.all()), 0)

    @property
    def token_vigente(self):
        if not self.token_publico:
            return False
        return not self.token_expira_en or self.token_expira_en > timezone.now()

    def regenerar_token(self):
        self.token_publico = uuid.uuid4()
        self.token_expira_en = timezone.now() + timedelta(days=TOKEN_DIAS_VIGENCIA)
        self.save(update_fields=['token_publico', 'token_expira_en', 'actualizado_en'])
        return self.token_publico


class EvidenciaSintoma(models.Model):
    """Evidencia y síntomas asociados a una orden."""

    orden = models.ForeignKey(
        OrdenFalla, on_delete=models.CASCADE, related_name='evidencias', verbose_name='Orden'
    )
    archivo_audio = models.FileField('Archivo de Audio', upload_to='audios/', null=True, blank=True)
    imagen = models.ImageField('Imagen', upload_to='fotos/', null=True, blank=True)
    narrativa_cliente = models.TextField('Narrativa del Cliente', null=True, blank=True)
    diagnostico_ia_json = models.JSONField('Diagnóstico IA JSON', null=True, blank=True)
    nivel_riesgo = models.CharField(
        'Nivel de Riesgo', max_length=20, choices=RIESGO_CHOICES, default='PRECAUCION'
    )
    creado_en = models.DateTimeField('Creado En', auto_now_add=True)

    class Meta:
        verbose_name = 'Evidencia de Síntoma'
        verbose_name_plural = 'Evidencias de Síntoma'
        ordering = ['-creado_en']

    def __str__(self):
        return f'Evidencia {self.id} - {self.orden.codigo_orden}'


class MensajeOrden(models.Model):
    orden = models.ForeignKey(OrdenFalla, on_delete=models.CASCADE, related_name='mensajes', verbose_name='Orden')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='Autor')
    contenido = models.TextField('Mensaje')
    creado_en = models.DateTimeField('Enviado', auto_now_add=True)

    class Meta:
        ordering = ('creado_en', 'pk')
        verbose_name = 'Mensaje de orden'
        verbose_name_plural = 'Mensajes de orden'

    def __str__(self):
        return f'Mensaje de {self.autor} en {self.orden.codigo_orden}'


class ItemPresupuestoRepuestos(models.Model):
    """Ítems de repuestos y mano de obra de una orden."""

    TIPO_CHOICES = [
        ('REPUESTO', 'Repuesto'),
        ('MANO_OBRA', 'Mano de Obra'),
    ]

    orden = models.ForeignKey(
        OrdenFalla, on_delete=models.CASCADE, related_name='items_presupuesto', verbose_name='Orden'
    )
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES)
    descripcion = models.CharField('Descripción', max_length=200)
    cantidad = models.PositiveIntegerField('Cantidad', validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(
        'Precio Unitario',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    aprobado_cliente = models.BooleanField('Aprobado por Cliente', default=False)
    creado_en = models.DateTimeField('Creado En', auto_now_add=True)

    class Meta:
        verbose_name = 'Item de Presupuesto'
        verbose_name_plural = 'Items de Presupuesto'
        ordering = ['creado_en']

    def __str__(self):
        return f'{self.get_tipo_display()}: {self.descripcion} - ${self.precio_unitario}'

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario


class Etiqueta(models.Model):
    """Etiquetas para clasificar órdenes."""

    nombre = models.CharField('Nombre', max_length=50, unique=True)
    color = models.CharField('Color', max_length=7, default='#6C757D')

    class Meta:
        verbose_name = 'Etiqueta'
        verbose_name_plural = 'Etiquetas'

    def __str__(self):
        return self.nombre
