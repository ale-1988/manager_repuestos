from django.db import models
from pedidos.models import Pedido
from usuarios.models import Usuario


class Transportista(Usuario):
    """Usuario especializado como transportista."""
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Transportista"
        verbose_name_plural = "Transportistas"

    def __str__(self):
        return f"{self.username} (Transportista)"


class Logistica(models.Model):
    """Registro del flujo logístico de cada pedido."""
    
    cod_pedido = models.OneToOneField("Pedido",on_delete=models.CASCADE,related_name="logistica")

    # Datos operativos
    fecha_actualizacion = models.DateTimeField(auto_now=True,help_text="Actualización automática del registro")
    cod_operador = models.ForeignKey(Usuario,on_delete=models.SET_NULL,null=True,blank=True,help_text="Usuario interno que realizó la última acción")
    

    # Transporte
    cod_transportista = models.ForeignKey(Transportista,on_delete=models.SET_NULL,null=True,blank=True)
    codigo_seguimiento = models.CharField(max_length=100,blank=True,help_text="Tracking provisto por la empresa de transporte")

    # Fechas de entrega
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)

    # Observaciones y auditoría
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"Logística del pedido {self.pedido.id}"
