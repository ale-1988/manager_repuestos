from django.db import models
from usuarios.models import Usuario
from repuestos.models import Material
from clientes.models import Clientes


class Pedido(models.Model):
    ESTADOS = [
        ('BORRADOR', 'Borrador'),
        ('CREADO', 'Creado'),
        ('CONFIRMADO', 'Confirmado'),
        ('CERRADO', 'Cerrado'),
        ('FACTURADO', 'Facturado'),
        ('PAGADO', 'Pagado'),
        ('PREPARANDO', 'Preparando'),
        ('CONSOLIDADO', 'Consolidado'),
        ('ENVIADO', 'Enviado'),
        ('ENTREGADO', 'Entregado'),
        ('CANCELADO', 'Cancelado'),
    ]
    id = models.BigAutoField(primary_key=True)
    cod_cliente = models.IntegerField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='BORRADOR')
    cod_transportista = models.ForeignKey(Usuario, on_delete=models.PROTECT,related_name="pedidos_transportista",null=True,blank=True)
    observaciones = models.TextField(blank=True)
 
     
    @property
    def cliente(self):
        return Clientes.objects.using("cliente").get(pk=self.cod_cliente) if self.cod_cliente else None
    
    def __str__(self):
        cli = self.cliente.nombre if self.cliente else "Sin cliente"
        return f"Pedido {self.id} - {cli}"


class DetallePedido(models.Model):
    cod_pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="detalles")
    cod_repuesto = models.IntegerField() #id_mate
    cantidad = models.DecimalField(max_digits=10, decimal_places=3,default=1)
    numero_serie = models.CharField(max_length=20, null=True, blank=True)
    
    def __str__(self):
        return f"{self.cod_repuesto.valor} x {self.cantidad}"
    
    @property
    def material(self):
        from repuestos.models import Material
        return Material.objects.using("remota").get(pk=self.cod_repuesto)
    
    @property
    def equipo_nombre(self):
        #Evita import circulares
        from repuestos.models import Seguimiento, Material
        if not self.numero_serie:
            return None

        # 1 — Buscar en Seguimiento
        seg = (
            Seguimiento.objects.using("rpg2")
            .filter(seg_numero_serie=self.numero_serie)
            .order_by("-seg_fecha_liberacion")
            .first()
        )
        if not seg or not seg.equi_codigo:
            return None

        try:
            mat = Material.objects.using("remota").get(pk=seg.equi_codigo)
            return mat.valor
        except Material.DoesNotExist:
            return None