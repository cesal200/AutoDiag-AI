from django.db import models


class AnalisisSintoma(models.Model):
    """AI analysis of vehicle symptoms from multimodal inputs."""
    
    TIPO_RIESGO_CHOICES = [
        ('PUEDE_RODAR', 'Puede Rodar'),
        ('PRECAUCION', 'Precaución'),
        ('NO_MOVER_GRUA', 'No Mover Grúa'),
    ]
    
    orden = models.ForeignKey('workshop.OrdenFalla', on_delete=models.CASCADE, related_name='analisis_ia', verbose_name='Orden')
    sintomas_normalizados = models.JSONField('Síntomas Normalizados', default=list, help_text='Descripción estandarizada de los síntomas')
    causas_probables = models.JSONField('Causas Probables', default=list, help_text='Lista de causas con probabilidades')
    nivel_riesgo = models.CharField('Nivel de Riesgo', max_length=20, choices=TIPO_RIESGO_CHOICES)
    pruebas_taller_sugeridas = models.JSONField('Pruebas de Taller Sugeridas', default=list, help_text='Procedimientos y valores esperados')
    transcripcion_confianza = models.FloatField('Confianza de Transcripción', default=0.0)
    creado_en = models.DateTimeField('Creado Automáticamente', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Análisis de Síntoma IA'
        verbose_name_plural = 'Análisis de Síntoma IA'
    
    def __str__(self):
        return f'Análisis IA - {self.orden.codigo_orden}'


class EntradaMultimodal(models.Model):
    """Multimodal input entries for AI processing."""
    
    MODO_CHOICES = [
        ('VOZ', 'Voz/Transcripción'),
        ('IMAGEN', 'Imagen'),
        ('DATOS_VEHICULO', 'Datos del Vehículo'),
        ('NARRATIVA', 'Narrativa del Cliente'),
    ]
    
    orden = models.ForeignKey('workshop.OrdenFalla', on_delete=models.CASCADE, related_name='entradas_multimodales', verbose_name='Orden')
    modo = models.CharField('Modo de Entrada', max_length=20, choices=MODO_CHOICES)
    contenido = models.TextField('Contenido')
    archivo = models.FileField('Archivo', upload_to='multimodal/', null=True, blank=True)
    metadatos = models.JSONField('Metadatos', null=True, blank=True)
    creado_en = models.DateTimeField('Creado Automáticamente', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Entrada Multimodal'
        verbose_name_plural = 'Entradas Multimodales'
    
    def __str__(self):
        return f'{self.get_modo_display()} - {self.orden.codigo_orden}'


class PlantillaPDF(models.Model):
    """PDF templates for workshop reports."""
    
    nombre = models.CharField('Nombre', max_length=100)
    descripcion = models.TextField('Descripción', blank=True)
    html_template = models.TextField('Plantilla HTML')
    es_predeterminado = models.BooleanField('Predeterminado', default=False)
    creado_en = models.DateTimeField('Creado Automáticamente', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Plantilla PDF'
        verbose_name_plural = 'Plantillas PDF'
    
    def __str__(self):
        return self.nombre
