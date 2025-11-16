from django.db import models
from usuarios.models import Usuario
from repuestos.models import Material

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
    id = models.BigAutoField(primary_key=True)
    cod_cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE,related_name="pedidos_cliente")
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='CREADO')
    cod_transportista = models.ForeignKey(Usuario, on_delete=models.PROTECT,related_name="pedidos_transportista",null=True,blank=True)
    observaciones = models.TextField(blank=True)
    
    def __str__(self):
        return f"Pedido {self.id} - {self.cod_cliente.username}"
    

class DetallePedido(models.Model):
    cod_pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="detalles")
    cod_repuesto = models.IntegerField() #id_mate
    cantidad = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.cod_repuesto.valor} x {self.cantidad}"
    
    @property
    def material(self):
        from repuestos.models import Material
        return Material.objects.using("remota").get(pk=self.cod_repuesto)