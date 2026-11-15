from django.contrib import admin

from .models import (
    Etiqueta,
    EvidenciaSintoma,
    ItemPresupuestoRepuestos,
    OrdenFalla,
    Taller,
    Vehiculo,
)


@admin.register(Taller)
class TallerAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'telefono', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'direccion')


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('placa', 'marca', 'modelo', 'anio', 'motor', 'cliente')
    list_filter = ('marca', 'anio')
    search_fields = ('placa', 'marca', 'modelo', 'motor', 'cliente__username')


@admin.register(OrdenFalla)
class OrdenFallaAdmin(admin.ModelAdmin):
    list_display = (
        'ticket',
        'codigo_orden',
        'cliente_efectivo',
        'vehiculo',
        'estado',
        'mecanico_asignado',
        'kilometraje_ingreso',
        'creado_en',
    )
    list_filter = ('estado', 'mecanico_asignado', 'taller')
    search_fields = (
        'ticket',
        'codigo_orden',
        'vehiculo__placa',
        'vehiculo__marca',
        'vehiculo__modelo',
        'cliente__username',
        'cliente__email',
        'nombre_cliente_walkin',
        'telefono_cliente_walkin',
        'mecanico_asignado__username',
    )
    readonly_fields = ('ticket', 'codigo_orden', 'token_publico', 'token_expira_en', 'creado_en', 'actualizado_en')
    filter_horizontal = ('etiquetas',)


@admin.register(EvidenciaSintoma)
class EvidenciaSintomaAdmin(admin.ModelAdmin):
    list_display = ('orden', 'nivel_riesgo', 'creado_en')
    list_filter = ('nivel_riesgo',)
    search_fields = ('orden__codigo_orden',)


@admin.register(ItemPresupuestoRepuestos)
class ItemPresupuestoRepuestosAdmin(admin.ModelAdmin):
    list_display = ('orden', 'tipo', 'descripcion', 'cantidad', 'precio_unitario', 'aprobado_cliente')
    list_filter = ('tipo', 'aprobado_cliente')
    search_fields = ('orden__codigo_orden', 'descripcion')


@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'color')
    search_fields = ('nombre',)
