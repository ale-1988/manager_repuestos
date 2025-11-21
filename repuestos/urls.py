from django.urls import path
from . import views

app_name = "repuestos"

urlpatterns = [

    # Entrada principal del módulo
    path("buscar/", views.buscar, name="buscar"),

    # Si el número ingresado era un ID de material
    path("repuesto/<int:id_mate>/", views.repuesto_por_id, name="repuesto_por_id"),

    # Con un id_mate de equipo accedo a su lista de materiales
    #path("equipo-desde-mate/<int:id_mate>/", views.lista_materiales_equipo, name="lista_materiales_equipo"),

    path("equipo/<int:id_mate>/lista/", views.lista_materiales_equipo, name="lista_materiales_equipo"),

    # Si el número ingresado era un NS → elegir equipo
    #path("equipo/<int:id_mate>/lista/", views.lista_materiales_equipo, name="lista_materiales"),

    # Selección manual cuando el NS no existe
    path("seleccionar-equipo/", views.seleccionar_equipo, name="seleccionar_equipo"),

    # Búsqueda manual por filtros (texto / grupos)
    path("buscar-manual/", views.buscar_manual, name="buscar_manual"),
    
    # Super busqueda modal
    path("buscar-modal/", views.buscar_modal, name="buscar_modal"),

]
