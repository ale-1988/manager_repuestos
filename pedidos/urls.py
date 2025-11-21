from django.urls import path
from . import views

app_name = "pedidos"

urlpatterns = [

    # Crear pedido en estado BORRADOR
    path("nuevo/", views.nuevo_pedido, name="nuevo_pedido"),

    # Editar pedido por ID
    path("editar/<int:id_pedido>/", views.editar_pedido, name="editar_pedido"),

    # Asignar cliente directamente desde la lista
    path(
        "asignar-cliente/<int:id_pedido>/<int:id_cliente>/",
        views.asignar_cliente_directo,
        name="asignar_cliente_directo"
    ),
    #Listar pedidos
    path("listar/", views.listar_pedidos, name="listar_pedidos"),

    #Agregr item
    path("agregar-item/<int:pedido_id>/<int:id_mate>/",
     views.agregar_item,
     name="agregar_item"),

    path("agregar-items-desde-modal/", views.agregar_items_desde_modal, name="agregar_items_desde_modal"),

]