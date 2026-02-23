Módulo Logística

Este módulo representa el proceso físico de preparación y envío de pedidos ya pagados.

Responsabilidades

Generar órdenes de preparación

Registrar ítems preparados

Gestionar envíos y entregas

Modelos principales

OrdenPreparacion

PreparacionItem

Envio

Flujo de estados

PAGADO → PREPARANDO → CONSOLIDADO → ENVIADO → ENTREGADO

Restricciones técnicas relevantes

No se usan claves foráneas a bases externas

Los repuestos se referencian por identificador lógico