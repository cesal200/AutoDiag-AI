from django.contrib import admin
from .models import AnalisisSintoma, EntradaMultimodal, PlantillaPDF


@admin.register(AnalisisSintoma)
class AnalisisSintomaAdmin(admin.ModelAdmin):
    list_display = ('orden', 'nivel_riesgo')
    search_fields = ('orden__codigo_orden',)


@admin.register(EntradaMultimodal)
class EntradaMultimodalAdmin(admin.ModelAdmin):
    list_display = ('orden', 'modo')
    search_fields = ('orden__codigo_orden',)


@admin.register(PlantillaPDF)
class PlantillaPDFAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)