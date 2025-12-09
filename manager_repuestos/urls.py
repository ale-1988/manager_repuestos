from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect

def home_redirect(request):
    return redirect("pedidos:listar")



urlpatterns = [
    # Página de inicio y login/logout bajo "sesiones"
    path("", include(("sesiones.urls", "sesiones"), namespace="sesiones")),

    path("admin/", admin.site.urls),

    # Usuarios
    path("usuarios/",include(("usuarios.urls", "usuarios"), namespace="usuarios")),

    # Clientes
    path("clientes/",include(("clientes.urls", "clientes"), namespace="clientes")),

    # Repuestos
    path("repuestos/",include(("repuestos.urls", "repuestos"), namespace="repuestos")),

    # Pedidos
    path("pedidos/",include(("pedidos.urls", "pedidos"), namespace="pedidos")),

    path("", home_redirect, name="inicio"),





]
