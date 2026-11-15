from django.urls import path
from . import views

urlpatterns = [
    path('analizar/<int:orden_id>/', views.analizar_sintoma, name='analizar_sintoma'),
    path('resultado/<int:analisis_id>/', views.resultado_analisis, name='resultado_analisis'),
    path('resultado/<int:analisis_id>/descartar/', views.descartar_analisis, name='descartar_analisis'),
]
