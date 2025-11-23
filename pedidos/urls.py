from django.urls import path
from . import views

app_name = "pedidos"

urlpatterns = [
    path("", views.buscar_pedido, name="inicio"),
    path("listar/", views.buscar_pedido, name="listar"),
    # path("buscar/", views.buscar_pedido, name="buscar"),

    # Nuevo flujo correcto
    path("nuevo/", views.nuevo_pedido_cliente, name="nuevo_cliente"),
    # API AJAX para clientes
    path("api/buscar_clientes/", views.api_buscar_clientes, name="api_buscar_clientes"),

    path("editar/<int:id>/", views.editar_pedido, name="editar"),
    path("detalle/<int:id>/", views.detalle_pedido, name="detalle"),
    path("cancelar/<int:id>/", views.cancelar_pedido, name="cancelar"),
    
    path("actualizar_estado/<int:id>/", views.actualizar_estado, name="actualizar_estado"),
    
    # =========================================================
    #   AGREGAR ITEMS AL PEDIDO
    # =========================================================
    path("<int:pedido_id>/items/", views.agregar_items, name="agregar_items"),
    # Búsqueda por equipo (lista de equipos)
    path("buscar_equipo/", views.buscar_equipo, name="buscar_equipo"),
     # Materiales del equipo seleccionado
    path("equipo/<int:id_mate>/", views.equipo_materiales, name="equipo_materiales"),
    
    # APIs AJAX para los 3 modos
    path("api/consultar_ns/", views.api_consultar_ns, name="api_consultar_ns"),
    # path("api/buscar_equipos/", views.api_buscar_equipos, name="api_buscar_equipos"),
    path("api/lista_materiales/", views.api_lista_materiales_equipo, name="api_lista_materiales_equipo"),
    path("api/buscar_materiales/", views.api_buscar_materiales, name="api_buscar_materiales"),
    path("api/agregar_item/", views.api_agregar_item, name="api_agregar_item"),
]
