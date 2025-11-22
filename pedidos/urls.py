from django.urls import path
from . import views

app_name = "pedidos"

urlpatterns = [
    path("", views.buscar_pedido, name="inicio"),
    path("listar/", views.buscar_pedido, name="listar"),
    path("buscar/", views.buscar_pedido, name="buscar"),

    # Nuevo flujo correcto
    path("nuevo/", views.nuevo_pedido_cliente, name="nuevo_cliente"),

    # API AJAX para clientes
    path("api/buscar_clientes/", views.api_buscar_clientes, name="api_buscar_clientes"),

    path("editar/<int:id>/", views.editar_pedido, name="editar"),
    path("cancelar/<int:id>/", views.cancelar_pedido, name="cancelar"),
    path("actualizar_estado/<int:id>/", views.actualizar_estado, name="actualizar_estado"),
    
    path("detalle/<int:id>/", views.detalle_pedido, name="detalle"),

    path("agregar_items_desde_modal/", views.agregar_items_desde_modal, name="agregar_items_desde_modal"),
]
