Módulo Pedidos

Este es el núcleo funcional del sistema. Modela el ciclo de vida completo de un pedido comercial.

Responsabilidades

Creación y edición de pedidos

Gestión de ítems del pedido

Control de estados del pedido

Coordinación con facturación y logística

Modelos principales

Pedido

DetallePedido

Cadena de estados

BORRADOR → CREADO → CONFIRMADO → CERRADO → FACTURADO → PAGADO → PREPARANDO → CONSOLIDADO → ENVIADO → ENTREGADO

Decisiones clave

La edición de ítems solo está permitida en estado CREADO

Los cambios de estado críticos se realizan mediante señales

El pedido es la entidad orquestadora del sistema