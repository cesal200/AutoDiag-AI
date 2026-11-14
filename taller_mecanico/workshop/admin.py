from django.contrib import admin
from .models import OrdenFalla, EvidenciaSintoma, ItemPresupuestoRepuestos, Etiqueta


@admin.register(OrdenFalla)
class OrdenFallaAdmin(admin.ModelAdmin):
    list_display = ('codigo_orden', 'vehiculo', 'estado', 'kilometraje_ingreso')
    search_fields = ('codigo_orden', 'vehiculo', 'mecanico_asignado__username')


@admin.register(EvidenciaSintoma)
class EvidenciaSintomaAdmin(admin.ModelAdmin):
    list_display = ('orden', 'nivel_riesgo')
    search_fields = ('orden__codigo_orden',)


@admin.register(ItemPresupuestoRepuestos)
class ItemPresupuestoRepuestosAdmin(admin.ModelAdmin):
    list_display = ('orden', 'tipo', 'descripcion', 'cantidad', 'precio_unitario')
    search_fields = ('orden__codigo_orden', 'descripcion')


@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)