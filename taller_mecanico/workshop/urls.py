from django.urls import path
from . import views

urlpatterns = [
    path('cliente/orden/nueva/', views.orden_cliente_nueva, name='cliente_orden_nueva'),
    path('cliente/ordenes/', views.orden_cliente_lista, name='cliente_orden_lista'),
    path('cliente/ordenes/<int:orden_id>/', views.orden_cliente_detalle, name='cliente_orden_detalle'),
    path('orden/<int:orden_id>/mensajes/', views.mensajes_orden, name='mensajes_orden'),
    path('orden/<int:orden_id>/enviar-mensaje/', views.enviar_mensaje_orden, name='enviar_mensaje_orden'),
    path('orden/nueva/', views.orden_nueva, name='orden_nueva'),
    path('orden/lista/', views.orden_lista, name='orden_lista'),
    path('orden/<int:orden_id>/', views.orden_detalle, name='orden_detalle'),
    path('pdf/<int:orden_id>/', views.generar_pdf, name='generar_pdf'),
]
