from django.urls import path
from . import views

app_name = "repuestos"

urlpatterns = [
    path("", views.buscar, name="inicio"),
    path("listar/", views.buscar, name="listar"),
    path("buscar/", views.buscar, name="buscar"),
    path("buscar-modal/", views.buscar_modal, name="buscar_modal"),
]


