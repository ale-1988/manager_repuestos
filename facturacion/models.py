from django.db import models
#from django.contrib.auth.models import User
from usuarios.models import Usuario

class Factura(models.Model):
    ESTADO_CHOICES = [
        ('EMITIDA', 'Emitida'),
        ('PAGADA', 'Pagada'),
        ('ANULADA', 'Anulada'),
    ]

    pedido = models.OneToOneField(
        'pedidos.Pedido',
        on_delete=models.PROTECT,
        related_name='factura'
    )

    fecha_emision = models.DateTimeField(auto_now_add=True)
    cliente = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='facturas'
    )

    importe_total = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='EMITIDA'
    )

    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha_emision']

    def __str__(self):
        return f"Factura #{self.id} - Pedido {self.pedido.id}"

class Pago(models.Model):
    MEDIO_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('CUENTA_CORRIENTE', 'Cuenta Corriente'),
        ('OTRO', 'Otro'),
    ]

    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name='pagos'
    )

    fecha = models.DateTimeField(auto_now_add=True)

    medio_pago = models.CharField(
        max_length=20,
        choices=MEDIO_PAGO_CHOICES
    )

    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    referencia = models.CharField(
        max_length=100,
        blank=True
    )

    def __str__(self):
        return f"Pago {self.monto} - Factura {self.factura.id}"