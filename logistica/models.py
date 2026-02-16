from django.db import models
from pedidos.models import Pedido
from usuarios.models import Usuario
from repuestos.models import Material

class Logistica(models.Model):
    """Registro del flujo logístico de cada pedido."""

    cod_pedido = models.OneToOneField(
        Pedido,
        on_delete=models.CASCADE,
        related_name="logistica"
    )

    # Datos operativos
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text="Actualización automática del registro"
    )

    cod_operador = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="operaciones_logistica",
        help_text="Usuario interno que realizó la última acción"
    )

    # Transporte
    cod_transportista = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="envios_transportista",
        help_text="Transportista asignado al envío"
    )

    codigo_seguimiento = models.CharField(
        max_length=100,
        blank=True,
        help_text="Tracking provisto por la empresa de transporte"
    )

    # Fechas de entrega
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)

    # Observaciones y auditoría
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"Logística del pedido {self.cod_pedido.id}"

class OrdenPreparacion(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PREPARACION', 'En preparación'),
        ('COMPLETA', 'Completa'),
    ]

    pedido = models.OneToOneField(
        'pedidos.Pedido',
        on_delete=models.PROTECT,
        related_name='envios'
    )

    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE'
    )

    responsable = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='ordenes_preparacion'
    )

    def __str__(self):
        return f"Preparación Pedido {self.pedido.id}"

    
class PreparacionItem(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('ENCONTRADO', 'Encontrado'),
        ('FALTANTE', 'Faltante'),
    ]

    orden = models.ForeignKey(
        'logistica.OrdenPreparacion',
        on_delete=models.CASCADE,
        related_name='items'
    )
    repuesto_id = models.IntegerField()
    cantidad = models.PositiveIntegerField()

    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='PENDIENTE'
    )

    def __str__(self):
        return f"Repuesto {self.repuesto_id} x{self.cantidad}"

    @property
    def repuesto(self):
        from repuestos.models import Material
        return Material.objects.using("remota").get(pk=self.repuesto_id)


    
class Envio(models.Model):
    ESTADO_CHOICES = [
        ('PREPARADO', 'Preparado'),
        ('DESPACHADO', 'Despachado'),
        ('ENTREGADO', 'Entregado'),
    ]

    pedido = models.OneToOneField(
        'pedidos.Pedido',
        on_delete=models.PROTECT,
        related_name='envio'
    )

    transportista = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="envios_transportados"
    )


    fecha_despacho = models.DateTimeField(null=True, blank=True)

    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='PREPARADO'
    )

    tracking = models.CharField(
        max_length=100,
        blank=True
    )

    bultos = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Envío Pedido {self.pedido.id}"