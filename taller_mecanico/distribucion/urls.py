from django.urls import path
from . import views

urlpatterns = [
    path('configurar/<int:orden_id>/', views.configurar_distribucion, name='configurar_distribucion'),
    path('configurar-remitente/', views.configurar_remitente, name='configurar_remitente'),
    path('enviar/<int:orden_id>/', views.enviar_reporte, name='enviar_reporte'),
    path('whatsapp/<int:orden_id>/', views.abrir_whatsapp, name='abrir_whatsapp'),
]
