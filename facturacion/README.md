Módulo Facturación

Este módulo implementa el circuito de facturación y pagos del sistema, actuando como puente entre los pedidos confirmados y la logística.

Responsabilidades

Emisión de facturas a partir de pedidos

Registro de pagos parciales o totales

Control del estado financiero del pedido

Modelos principales

Factura

Pago

Flujo típico

Pedido confirmado

Emisión de factura

Registro de pagos

Pedido pasa a estado PAGADO

Decisiones de diseño

No se permite facturar pedidos no confirmados

Los cambios de estado del pedido se disparan mediante señales