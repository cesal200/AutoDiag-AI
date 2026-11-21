"""
URL configuration for taller_mecanico project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns: path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns: path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns: path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from accounts import views as accounts_views
from workshop import views as workshop_views

from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('registro/', views.register, name='register'),
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('registro/', accounts_views.registro, name='registro'),
    path('panel/', workshop_views.dashboard, name='dashboard'),
    path('panel/admin/', workshop_views.dashboard_admin, name='dashboard_admin'),
    path('panel/cliente/', workshop_views.dashboard_cliente, name='dashboard_cliente'),
    path('panel/tecnico/', workshop_views.dashboard_tecnico, name='dashboard_tecnico'),
    path('panel/clientes/nuevo/', workshop_views.cliente_rapido, name='cliente_rapido'),
    path(
        'seguimiento/<uuid:token>/',
        workshop_views.seguimiento_publico,
        name='seguimiento_publico',
    ),
    path('api/', include('workshop.urls')),
    path('api/diagnostico/', include('diagnostico_ia.urls')),
    path('api/distribucion/', include('distribucion.urls')),
    path('workshop/', include('workshop.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
