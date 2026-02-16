from django.urls import path
from . import views

app_name = "usuarios"

urlpatterns = [
    path("listar/", views.listar_usuarios, name='listar'),
    path("nuevo/", views.nuevo_usuario, name='nuevo'),
    path("editar/<int:id>/", views.editar_usuario, name='editar'),
    path("eliminar/<int:id>/", views.eliminar_usuario, name='eliminar'),
]
