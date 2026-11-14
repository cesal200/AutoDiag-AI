from django.urls import path
from . import views

urlpatterns = [
    path('configurar/<int:orden_id>/', views.configurar_distribucion, name='configurar_distribucion'),
    path('enviar/<int:orden_id>/', views.enviar_reporte, name='enviar_reporte'),
]
