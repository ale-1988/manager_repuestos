from django.urls import path
from . import views

app_name = "logistica"

urlpatterns = [

    path("preparacion/", views.listar_preparacion, name="listar_preparacion"),
    path("preparacion/<int:id>/", views.detalle_preparacion, name="detalle_preparacion"),

    path("entregas/", views.listar_entregas, name="listar_entregas"),
    path("entregas/<int:id>/", views.detalle_entregas, name="detalle_entregas"),

    path("preparacion/<int:id>/comenzar/",views.comenzar_preparacion,name="comenzar_preparacion"),
    path("preparacion/<int:id>/consolidar/",views.consolidar_pedido,name="consolidar_pedido"),
    path("preparacion/<int:id>/guardar/",views.guardar_preparacion,name="guardar_preparacion"),
    path("item/<int:id>/actualizar/",views.actualizar_preparado,name="actualizar_preparado"),
    path("entregas/<int:id>/enviar/",views.enviar_pedido,name="enviar_pedido"),
    path("entregas/<int:id>/entregar/",views.confirmar_entrega,name="confirmar_entrega"),
]