from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone


def generar_codigo_orden():
    return f'ORD-{timezone.localdate().year}-{uuid4().hex[:8].upper()}'


class OrdenFalla(models.Model):
    """Repair order lifecycle with AI pre-diagnosis."""
    
    ESTADO_CHOICES = [
        ('PRE_DIAGNOSTICO', 'Pre-Diagnóstico'),
        ('EN_TALLER', 'En Taller'),
        ('ESPERA_REPUESTO', 'Espera Repuesto'),
        ('LISTO', 'Listo'),
        ('ENTREGADO', 'Entregado'),
    ]
    
    codigo_orden = models.CharField('Código de Orden', max_length=20, unique=True, default=generar_codigo_orden)
    taller = models.CharField('Taller', max_length=100)
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='ordenes_taller', verbose_name='Cliente')
    vehiculo = models.CharField('Vehículo', max_length=100)
    placa = models.CharField('Placa', max_length=15, blank=True, default='')
    mecanico_asignado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='Mecánico Asignado')
    kilometraje_ingreso = models.IntegerField('Kilometraje Ingreso')
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='PRE_DIAGNOSTICO')
    etiquetas = models.ManyToManyField('Etiqueta', blank=True, verbose_name='Etiquetas')
    token_publico = models.UUIDField('Token Público', unique=True, null=True, blank=True)
    token_expira_en = models.DateTimeField('Token Expira En', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Orden de Fallo'
        verbose_name_plural = 'Órdenes de Fallo'
    
    def __str__(self):
        return f'{self.codigo_orden} - {self.vehiculo}'


class EvidenciaSintoma(models.Model):
    """Evidence and symptoms for a repair order."""
    
    ORDEN_ESTADO_CHOICES = [
        ('PRE_DIAGNOSTICO', 'Pre-Diagnóstico'),
        ('EN_TALLER', 'En Taller'),
        ('ESPERA_REPUESTO', 'Espera Repuesto'),
        ('LISTO', 'Listo'),
        ('ENTREGADO', 'Entregado'),
    ]
    
    orden = models.ForeignKey(OrdenFalla, on_delete=models.CASCADE, related_name='evidencias', verbose_name='Orden')
    archivo_audio = models.FileField('Archivo de Audio', upload_to='audios/', null=True, blank=True)
    imagen = models.ImageField('Imagen', upload_to='fotos/', null=True, blank=True)
    narrativa_cliente = models.TextField('Narrativa del Cliente', null=True, blank=True)
    diagnostico_ia_json = models.JSONField('Diagnóstico IA JSON', null=True, blank=True)
    nivel_riesgo = models.CharField('Nivel de Riesgo', max_length=20, choices=ORDEN_ESTADO_CHOICES, default='PRECAUCION')
    
    class Meta:
        verbose_name = 'Evidencia de Síntoma'
        verbose_name_plural = 'Evidencias de Síntoma'
    
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
    """Budget items for parts and labor."""
    
    TIPO_CHOICES = [
        ('REPUESTO', 'Repuesto'),
        ('MANO_OBRA', 'Mano de Obra'),
    ]
    
    orden = models.ForeignKey(OrdenFalla, on_delete=models.CASCADE, related_name='items_presupuesto', verbose_name='Orden')
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES)
    descripcion = models.CharField('Descripción', max_length=200)
    cantidad = models.IntegerField('Cantidad')
    precio_unitario = models.DecimalField('Precio Unitario', max_digits=10, decimal_places=2)
    aprobado_cliente = models.BooleanField('Aprobado por Cliente', default=False)
    
    class Meta:
        verbose_name = 'Item de Presupuesto'
        verbose_name_plural = 'Items de Presupuesto'
    
    def __str__(self):
        return f'{self.get_tipo_display()}: {self.descripcion} - ${self.precio_unitario}'


class Etiqueta(models.Model):
    """Tags for classifying orders."""
    
    nombre = models.CharField('Nombre', max_length=50, unique=True)
    color = models.CharField('Color', max_length=7, default='#6C757D')
    
    class Meta:
        verbose_name = 'Etiqueta'
        verbose_name_plural = 'Etiquetas'
    
    def __str__(self):
        return self.nombre
