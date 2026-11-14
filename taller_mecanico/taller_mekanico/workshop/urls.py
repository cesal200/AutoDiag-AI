from django.urls import path
from . import views

urlpatterns = [
    path('orden/nueva/', views.orden_nueva, name='orden_nueva'),
    path('orden/lista/', views.orden_lista, name='orden_lista'),
    path('orden/<int:orden_id>/', views.orden_detalle, name='orden_detalle'),
    path('pdf/<int:orden_id>/', views.generar_pdf, name='generar_pdf'),
]