from django.contrib import admin
from .models import ConfiguracionDistribucion, EnvioReportes, PlantillaEmail


@admin.register(ConfiguracionDistribucion)
class ConfiguracionDistribucionAdmin(admin.ModelAdmin):
    list_display = ('orden', 'metodo')
    search_fields = ('orden__codigo_orden',)


@admin.register(EnvioReportes)
class EnvioReportesAdmin(admin.ModelAdmin):
    list_display = ('orden', 'metodo', 'estado')
    search_fields = ('orden__codigo_orden',)


@admin.register(PlantillaEmail)
class PlantillaEmailAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)