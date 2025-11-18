from django.urls import path
from . import views

urlpatterns = [
    path('listar/', views.listar_usuarios, name='usuarios_listar'),
    path('nuevo/', views.nuevo_usuario, name='usuarios_nuevo'),
    path('editar/<int:id>/', views.editar_usuario, name='usuarios_editar'),
    path('eliminar/<int:id>/', views.eliminar_usuario, name='usuarios_eliminar'),
]
