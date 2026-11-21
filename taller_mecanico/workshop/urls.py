from django.urls import path

from . import views

urlpatterns = [
    path('vehiculo/nuevo/', views.vehiculo_nueva, name='vehiculo_nueva'),
    path('orden/nueva/', views.orden_nueva, name='orden_nueva'),
    path('orden/<int:orden_id>/editar/', views.editar_orden, name='editar_orden'),
    path('orden/lista/', views.orden_lista, name='orden_lista'),
    path('orden/<int:orden_id>/', views.orden_detalle, name='orden_detalle'),
    path('orden/<int:orden_id>/estado/', views.cambiar_estado, name='cambiar_estado'),
    path('orden/<int:orden_id>/mecanico/', views.asignar_mecanico, name='asignar_mecanico'),
    path('orden/<int:orden_id>/item/', views.agregar_item, name='agregar_item'),
    path(
        'orden/<int:orden_id>/item/<int:item_id>/eliminar/',
        views.eliminar_item,
        name='eliminar_item',
    ),
    path(
        'orden/<int:orden_id>/item/<int:item_id>/aprobar/',
        views.aprobar_item,
        name='aprobar_item',
    ),
    path('orden/<int:orden_id>/evidencia/', views.agregar_evidencia, name='agregar_evidencia'),
    path('orden/<int:orden_id>/mensajes/', views.mensajes_orden, name='mensajes_orden'),
    path('orden/<int:orden_id>/mensajes/enviar/', views.enviar_mensaje_orden, name='enviar_mensaje_orden'),
    path('orden/<int:orden_id>/token/', views.regenerar_token, name='regenerar_token'),
    path('pdf/<int:orden_id>/', views.generar_pdf, name='generar_pdf'),
    path('pdf/<int:orden_id>/descargar/', views.descargar_pdf, name='descargar_pdf'),
]
