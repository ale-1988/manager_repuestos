from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

def home_redirect(request):
    if not request.user.is_authenticated:
        return redirect("sesiones:login")
    return redirect("pedidos:listar")

urlpatterns = [
    path("admin/", admin.site.urls),

    path("sesiones/", include(("sesiones.urls", "sesiones"), namespace="sesiones")),
    path("usuarios/", include(("usuarios.urls", "usuarios"), namespace="usuarios")),
    path("clientes/", include(("clientes.urls", "clientes"), namespace="clientes")),
    path("repuestos/", include(("repuestos.urls", "repuestos"), namespace="repuestos")),
    path("pedidos/", include(("pedidos.urls", "pedidos"), namespace="pedidos")),
    path("facturacion/", include(("facturacion.urls", "facturacion"), namespace="facturacion")),

    path("", home_redirect, name="inicio"),
]
handler404 = "manager_repuestos.views.custom_404"