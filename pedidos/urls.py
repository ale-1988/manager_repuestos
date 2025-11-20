from django.urls import path
from . import views

app_name = "pedidos"

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path("nuevo/", views.nuevo_pedido, name="nuevo_pedido"),
    path("editar/<int:id_pedido>/", views.editar_pedido, name="editar_pedido"),
    path("listar/", views.listar_pedidos, name="listar_pedidos"),  # si existe
]
