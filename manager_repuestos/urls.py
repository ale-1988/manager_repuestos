"""
URL configuration for manager_repuestos project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from sesiones.views import inicio

urlpatterns = [
    path("admin/", admin.site.urls),

    # Inicio del sistema (barra superior)
    path("", inicio, name="inicio"),

    # Login 
    path("", include("sesiones.urls")),

    # ABM usuarios
    path("usuarios/", include("usuarios.urls")),

    # Modulo repuestos
    path('repuestos/', include('repuestos.urls')),

    # Módulo pedidos
    path("pedidos/", include(("pedidos.urls", 'pedidos'), namespace='pedidos')),
    
    #Modulo clientes
    path("clientes/", include("clientes.urls")),

]
