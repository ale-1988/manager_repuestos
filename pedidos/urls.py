from django.urls import path
from . import views
from . import api

app_name = "pedidos"

urlpatterns = [
    # Página principal
    path("", views.listar_pedidos, name="inicio"),
    path("listar/", views.listar_pedidos, name="listar"),

    # Crear nuevo pedido (selección de cliente)
    path("nuevo/", views.nuevo_pedido_cliente, name="nuevo_cliente"),
    
    # CRUD pedido
    path("editar/<int:id>/", views.editar_pedido, name="editar"),
    path("confirmar_division/<int:id>/", views.confirmar_division, name="confirmar_division"),
    path("cancelar/<int:id>/", views.cancelar_pedido, name="cancelar"),
    path("actualizar_estado/<int:id>/", views.actualizar_estado, name="actualizar_estado"),
    # Ítems del pedido
    path("<int:pedido_id>/items/", views.agregar_items, name="agregar_items"),
    path("buscar_equipo/", views.buscar_equipo, name="buscar_equipo"),


    # APIs AJAX — Modo NS, Equipo, Descripción
    path("api/consultar_ns/", api.api_consultar_ns, name="api_consultar_ns"),
    
    # API REAL — Buscar equipos (para modo B)
    path("api/buscar_equipos/", api.api_buscar_equipos, name="api_buscar_equipos"),
    
    # APIs de clientes
    path("api/buscar_clientes/", api.api_buscar_clientes, name="api_buscar_clientes"),
    path("api/lista_materiales/", api.api_lista_materiales_equipo, name="api_lista_materiales_equipo"),
    path("api/buscar_materiales/", api.api_buscar_materiales, name="api_buscar_materiales"),
    path("api/agregar_item/", api.api_agregar_item, name="api_agregar_item"),
    
    #Historiales
    path("historial/", views.historial_global, name="historial_global"),
    path("historial/pedido/<int:pedido_id>/", views.historial_global, name="historial_pedido"),
    
    path("<int:id>/facturar/", views.facturar_pedido, name="facturar_pedido"),
    path("<int:id>/comprobante_preliminar/",views.comprobante_preliminar,name="comprobante_preliminar"),
    path("<int:id>/pdf_preliminar/",views.generar_pdf_preliminar,name="pdf_preliminar"),
    path("detalle/<int:detalle_id>/modificar-cantidad/",views.modificar_cantidad,name="modificar_cantidad"),
    path("<int:id>/enviar_comprobante_email/",views.enviar_comprobante_email,name="enviar_comprobante_email"),

]
