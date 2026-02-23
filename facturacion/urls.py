from django.urls import path
from . import views

app_name = "facturacion"

urlpatterns = [
    path("", views.listar_facturas, name="listar_facturas"),
    path("crear/", views.crear_factura, name="crear_factura"),
    path("<int:pk>/", views.detalle_factura, name="detalle_factura"),
    path("<int:pk>/editar/", views.editar_factura, name="editar_factura"),
    path("<int:pk>/pago/", views.registrar_pago, name="registrar_pago"),
    path("<int:pk>/emitir/", views.emitir_factura, name="emitir_factura"),
    path("<int:pk>/anular/", views.anular_factura, name="anular_factura"),
    path("<int:pk>/nota_credito/", views.crear_nota_credito, name="crear_nota_credito"),
    path("<int:pk>/pdf/", views.generar_pdf_factura, name="generar_pdf_factura"),
    path("<int:pk>/email/", views.enviar_factura_email, name="enviar_factura_email"),
    path("<int:pk>/aplicar_credito/", views.aplicar_credito, name="aplicar_credito"),
]
