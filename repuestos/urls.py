from django.urls import path
from . import views

app_name = "repuestos"

urlpatterns = [
    path("", views.buscar_manual, name="inicio"),
    path("listar/", views.buscar_manual, name="listar"),
    path("buscar/", views.buscar_manual, name="buscar"),
    path("api/grupos/", views.api_grupos, name="api_grupos"),
    
    # Ver repuesto por ID
    path("id/<int:id_mate>/", views.repuesto_por_id, name="repuesto_por_id"),

    # Búsqueda manual avanzada
    path("buscar_manual/", views.buscar_manual, name="buscar_manual"),
]


