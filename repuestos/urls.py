from django.urls import path
from . import views

app_name = "repuestos"

urlpatterns = [
    path("", views.buscar, name="inicio"),
    path("listar/", views.buscar, name="listar"),
    path("buscar/", views.buscar, name="buscar"),
    path("api/grupos/", views.api_grupos, name="api_grupos"),
    
    # Ver repuesto por ID
    path("id/<int:id_mate>/", views.repuesto_por_id, name="repuesto_por_id"),

    # Búsqueda manual avanzada
    path("buscar_manual/", views.buscar_manual, name="buscar_manual"),

    # Lista de materiales por equipo (legacy)
    path("lista_materiales/<int:id_mate>/",
         views.lista_materiales_equipo,
         name="lista_materiales"),
]


