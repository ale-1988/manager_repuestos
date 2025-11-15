from django.db import models
from usuarios.models import Usuario,Transportista
from repuestos.models import Repuesto

class Pedido(models.Model):
    ESTADOS = [
        ('CREADO', 'Creado'),
        ('CONFIRMADO', 'Confirmado'),
        ('FACTURADO', 'Facturado'),
        ('PAGADO', 'Pagado'),
        ('PREPARANDO', 'Preparando'),
        ('CONSOLIDADO', 'Consolidado'),
        ('ENVIADO', 'Enviado'),
        ('ENTREGADO', 'Entregado'),
        ('CANCELADO', 'Cancelado'),
    ]

    cod_cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE,related_name="pedidos")
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='CREADO')
    cod_transportista = models.ForeignKey(Transportista, on_delete=models.PROTECT,related_name="pedidos")
    observaciones = models.TextField(blank=True)
    
    def __str__(self):
        return f"Pedido {self.id} - {self.cliente.username}"
    

class DetallePedido(models.Model):
    cod_pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="detalles")
    cod_repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.repuesto} x {self.cantidad}"
