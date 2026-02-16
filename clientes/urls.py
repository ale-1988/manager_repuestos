from django.urls import path
from . import views

app_name = "clientes"

urlpatterns = [
    path("buscar-ajax/", views.buscar_clientes_ajax, name="buscar_ajax"),
]
