from django.db import models


METODO_DISTRIBUCION_CHOICES = [
    ('TELEGRAM', 'Telegram'),
    ('EMAIL', 'Email'),
    ('AMBOS', 'Ambos'),
    ('NINGUNO', 'Ninguno'),
]


class ConfiguracionDistribucion(models.Model):
    """Configuration for report distribution methods."""
    
    METODO_CHOICES = METODO_DISTRIBUCION_CHOICES
    
    orden = models.OneToOneField('workshop.OrdenFalla', on_delete=models.CASCADE, related_name='config_distribucion', verbose_name='Orden')
    metodo = models.CharField('Método de Distribución', max_length=10, choices=METODO_CHOICES, default='TELEGRAM')
    chat_telegram_id = models.CharField('ID Chat Telegram', max_length=50, null=True, blank=True)
    email_destino = models.EmailField('Email Destino', max_length=254, null=True, blank=True)
    creado_en = models.DateTimeField('Creado Automáticamente', auto_now_add=True)
    actualizado_en = models.DateTimeField('Actualizado Automáticamente', auto_now=True)
    
    class Meta:
        verbose_name = 'Configuración de Distribución'
        verbose_name_plural = 'Configuraciones de Distribución'
    
    def __str__(self):
        return f'Distribución {self.orden.codigo_orden} - {self.get_metodo_display()}'


class EnvioReportes(models.Model):
    """Log of report distribution attempts."""
    
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('ENVIADO', 'Enviado'),
        ('Fallido', 'Fallido'),
    ]
    
    METODO_CHOICES = METODO_DISTRIBUCION_CHOICES
    
    orden = models.ForeignKey('workshop.OrdenFalla', on_delete=models.CASCADE, related_name='logs_envios', verbose_name='Orden')
    metodo = models.CharField('Método', max_length=10, choices=METODO_CHOICES, default='TELEGRAM')
    estado = models.CharField('Estado', max_length=10, choices=ESTADO_CHOICES, default='PENDIENTE')
    mensaje_error = models.TextField('Mensaje de Error', null=True, blank=True)
    creado_en = models.DateTimeField('Creado Automáticamente', auto_now=True)
    
    class Meta:
        verbose_name = 'Envío de Reporte'
        verbose_name_plural = 'Log de Envios de Reportes'
    
    def __str__(self):
        return f'Envio {self.id} - {self.orden.codigo_orden} ({self.get_estado_display()})'


class PlantillaEmail(models.Model):
    """Email templates for report distribution."""
    
    nombre = models.CharField('Nombre', max_length=100)
    asunto = models.CharField('Asunto', max_length=200)
    cuerpo_html = models.TextField('Cuerpo HTML')
    es_predeterminado = models.BooleanField('Predeterminado', default=False)
    creado_en = models.DateTimeField('Creado Automáticamente', auto_now=True)
    
    class Meta:
        verbose_name = 'Plantilla de Email'
        verbose_name_plural = 'Plantillas de Email'
    
    def __str__(self):
        return self.nombre
