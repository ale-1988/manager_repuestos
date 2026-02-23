from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from facturacion.models import Factura, Pago
from logistica.models import OrdenPreparacion, PreparacionItem, Envio

from usuarios.services import get_usuario_sistema


# ==========================================================
# FACTURADO
# ==========================================================
@receiver(post_save, sender=Factura)
def pedido_facturado(sender, instance, created, **kwargs):

    # Solo actuar al crear
    if not created:
        return

    # Solo facturas reales (no notas de crédito)
    if instance.tipo != "FACTURA":
        return

    # Debe tener pedido asociado
    if not instance.pedido:
        return

    pedido = instance.pedido

    if pedido.estado != "CERRADO":
        raise ValueError(
            f"No se puede facturar un pedido en estado {pedido.estado}"
        )

    pedido.cambiar_estado(
        "FACTURADO",
        usuario=get_usuario_sistema(),
        observacion="Cambio automático por generación de factura"
    )


# ==========================================================
# PAGADO
# ==========================================================
@receiver(post_save, sender=Pago)
def pedido_pagado(sender, instance, created, **kwargs):
    if not created:
        return

    factura = instance.factura
    pedido = factura.pedido

    total_pagado = sum(p.monto for p in factura.pagos.all())

    if total_pagado >= factura.importe_total:
        if pedido.estado != 'PAGADO':
            pedido.cambiar_estado(
                "PAGADO",
                usuario=get_usuario_sistema(),
                observacion="Cambio automático por pago completo"
            )

        factura.estado = 'PAGADA'
        factura.save(update_fields=['estado'])


# ==========================================================
# PREPARANDO
# ==========================================================
@receiver(post_save, sender=OrdenPreparacion)
def pedido_preparando(sender, instance, created, **kwargs):
    if not created:
        return

    pedido = instance.pedido

    if pedido.estado != 'PAGADO':
        raise ValueError("Solo se pueden preparar pedidos PAGADOS")

    pedido.cambiar_estado(
        "PREPARANDO",
        usuario=get_usuario_sistema(),
        observacion="Cambio automático por creación de orden de preparación"
    )


# ==========================================================
# CONSOLIDADO
# ==========================================================
@receiver(post_save, sender=PreparacionItem)
def pedido_consolidado(sender, instance, **kwargs):
    orden = instance.orden
    pedido = orden.pedido

    estados = orden.items.values_list('estado', flat=True)

    if estados and all(e == 'ENCONTRADO' for e in estados):
        if pedido.estado == 'PREPARANDO':
            pedido.cambiar_estado(
                "CONSOLIDADO",
                usuario=get_usuario_sistema(),
                observacion="Cambio automático por consolidación completa"
            )


# ==========================================================
# ENVIADO
# ==========================================================
@receiver(post_save, sender=Envio)
def pedido_enviado(sender, instance, created, **kwargs):
    if not created:
        return

    pedido = instance.pedido

    if pedido.estado != 'CONSOLIDADO':
        raise ValueError("No se puede enviar un pedido no consolidado")

    pedido.cambiar_estado(
        "ENVIADO",
        usuario=get_usuario_sistema(),
        observacion="Cambio automático por generación de envío"
    )


# ==========================================================
# ENTREGADO
# ==========================================================
@receiver(post_save, sender=Envio)
def pedido_entregado(sender, instance, **kwargs):
    pedido = instance.pedido

    if instance.estado == 'ENTREGADO' and pedido.estado != 'ENTREGADO':
        pedido.cambiar_estado(
            "ENTREGADO",
            usuario=get_usuario_sistema(),
            observacion="Cambio automático por confirmación de entrega"
        )
