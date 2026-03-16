from django.db import models
from usuarios.models import Usuario
from repuestos.models import Material
from clientes.models import Clientes
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from facturacion.models import Factura
from django.db import transaction


class Pedido(models.Model):
    BORRADOR = "BORRADOR"
    CREADO = "CREADO"
    CONFIRMADO = "CONFIRMADO"
    CERRADO = "CERRADO"
    FACTURADO = "FACTURADO"
    PAGADO = "PAGADO"
    PREPARANDO = "PREPARANDO"
    CONSOLIDADO = "CONSOLIDADO"
    ENVIADO = "ENVIADO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"
    
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
    TRANSICIONES_VALIDAS = {
        "BORRADOR": ["CREADO", "CANCELADO"],
        "CREADO": ["CONFIRMADO", "CANCELADO"],
        "CONFIRMADO": ["CREADO", "CERRADO", "CANCELADO"],
        "CERRADO": ["FACTURADO"],
        "FACTURADO": ["PAGADO"],
        "PAGADO": ["PREPARANDO"],
        "PREPARANDO": ["CONSOLIDADO"],
        "CONSOLIDADO": ["ENVIADO"],
        "ENVIADO": ["ENTREGADO"],
        "ENTREGADO": [],
        "CANCELADO": [],
    }

    id = models.BigAutoField(primary_key=True)
    cod_cliente = models.IntegerField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='BORRADOR')
    cod_transportista = models.ForeignKey(Usuario, on_delete=models.PROTECT,related_name="pedidos_transportista",null=True,blank=True)
    observaciones = models.TextField(blank=True)


    def estados_disponibles(self):
        """
        Devuelve lista de estados a los que puede transicionar
        desde el estado actual.
        """
        return self.TRANSICIONES_VALIDAS.get(self.estado, [])


    def puede_ir_a(self, estado):
        return estado in self.estados_disponibles()
    
    
    def cambiar_estado(self, nuevo_estado,usuario, observacion=None):

        if not usuario:
            raise ValidationError("El usuario es obligatorio para cambiar el estado.")
        
        estado_actual = self.estado

        if nuevo_estado == estado_actual:
            return False

        transiciones_permitidas = self.TRANSICIONES_VALIDAS.get(estado_actual, [])

        if nuevo_estado not in transiciones_permitidas:
            raise ValidationError(
                f"No se puede cambiar de {estado_actual} a {nuevo_estado}"
            )

        with transaction.atomic():
            self.estado = nuevo_estado
            super().save(update_fields=["estado"])
            
            # Registrar historial
            HistorialEstadoPedido.objects.create(
                pedido=self,
                estado_anterior=estado_actual,
                estado_nuevo=nuevo_estado,
                usuario=usuario,
                observacion=observacion,
            )
        return True

    
    @property
    def cliente(self):
        return Clientes.objects.using("cliente").get(pk=self.cod_cliente) if self.cod_cliente else None
    
    def __str__(self):
        cli = self.cliente.nombre if self.cliente else "Sin cliente"
        return f"Pedido {self.id} - {cli}"
    
    def puede_facturarse(self):
        return self.estado == 'CERRADO'

    def puede_prepararse(self):
        return self.estado == 'PAGADO'

    def puede_enviarse(self):
        return self.estado == 'CONSOLIDADO'
    
    def cancelar(self, motivo=None):
        """
        Cancela el pedido si todavía no ingresó
        al circuito de facturación o logística.
        """
        estados_validos = ['BORRADOR', 'CREADO', 'CONFIRMADO']

        if self.estado not in estados_validos:
            raise ValidationError(
                f"No se puede cancelar un pedido en estado {self.estado}"
            )

        self.estado = 'CANCELADO'

        if motivo:
            self.observaciones = motivo

        self.save(update_fields=['estado'])

    def cerrar(self):
        """
        Cierra el pedido para edición.
        No permite modificar cantidades ni ítems,
        pero aún no factura.
        """
        if self.estado != 'CONFIRMADO':
            raise ValidationError(
                "Solo se pueden cerrar pedidos CONFIRMADOS"
            )

        self.estado = 'CERRADO'
        self.save(update_fields=['estado'])
        
    def save(self, *args, **kwargs):
        if self.pk:
            estado_anterior = Pedido.objects.get(pk=self.pk).estado
            if estado_anterior != self.estado:
                raise ValidationError(
                    "El estado no puede modificarse directamente. "
                    "Use cambiar_estado() para modificar el estado del pedido."
                )

        super().save(*args, **kwargs)

        

    def crear_factura_desde_pedido(self, usuario):

        if self.estado != "CERRADO":
            raise ValidationError(
                "Solo se pueden facturar pedidos en estado CERRADO."
            )

        if not self.detalles.exists():
            raise ValidationError(
                "No se puede facturar un pedido sin ítems."
            )

        with transaction.atomic():

            # Bloqueo del pedido para evitar doble facturación
            pedido = type(self).objects.select_for_update().get(pk=self.pk)

            if Factura.objects.filter(pedido=pedido).exists():
                raise ValidationError(
                    "Este pedido ya tiene una factura asociada."
                )

            total = Decimal("0.00")

            for d in pedido.detalles.all():
                subtotal = Decimal(d.cantidad) * Decimal(d.material.precio)
                total += subtotal

            total = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            
            if total <= Decimal("0"):
                raise ValidationError(
                    "El total del pedido debe ser mayor a cero."
                )
            print("COD_CLIENTE:", pedido.cod_cliente)
            factura = Factura.objects.create(
                pedido=pedido,
                cod_cliente=pedido.cod_cliente,
                tipo="FACTURA",
                importe_total=total,
                estado="BORRADOR",
            )

        return factura



class HistorialEstadoPedido(models.Model):
    pedido = models.ForeignKey(
        "Pedido",
        on_delete=models.CASCADE,
        related_name="historial_estados"
    )

    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )

    fecha = models.DateTimeField(auto_now_add=True)

    observacion = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-fecha"]


class DetallePedido(models.Model):
    cod_pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="detalles")
    cod_repuesto = models.IntegerField() #id_mate
    cantidad = models.DecimalField(max_digits=10, decimal_places=3,default=1,validators=[MinValueValidator(Decimal(0.001))])
    numero_serie = models.CharField(max_length=20, null=True, blank=True)
    cantidad_preparada = models.DecimalField(max_digits=10,decimal_places=3,default=0)
    
    def __str__(self):
        return f"Repuesto {self.cod_repuesto} x {self.cantidad}"
    
    @property
    def material(self):
        from repuestos.models import Material
        return Material.objects.using("remota").get(pk=self.cod_repuesto)

    @property
    def info_equipo(self):
        """
        Devuelve un dict con:
        - equipo_nombre
        - numero_serie
        - fecha_liberacion
        - fin_garantia
        - garantia_ok (bool)
        
        Si no hay NS o seguimiento, devuelve None.
        """
        if not self.numero_serie:
            return None

        from repuestos.models import Seguimiento, Material
        from dateutil.relativedelta import relativedelta
        from django.conf import settings
        from django.utils import timezone

        seg = (
            Seguimiento.objects.using("rpg2")
            .filter(seg_numero_serie=self.numero_serie)
            .order_by("-seg_fecha_liberacion")
            .first()
        )
        if not seg:
            return None

        # Equipo asociado a ese número de serie
        try:
            mat = Material.objects.using("remota").get(pk=seg.equi_codigo)
            equipo_nombre = mat.valor
        except Material.DoesNotExist:
            equipo_nombre = None

        meses = getattr(settings, "GARANTIA_MESES", 36)
        fecha_liberacion = seg.seg_fecha_liberacion
        fin_garantia = fecha_liberacion + relativedelta(months=meses)
        
        if timezone.now() <= fin_garantia:
            color_garantia="#6fcf85"
        else:
            color_garantia="#e46772"   

        return {
            "numero_serie": self.numero_serie,
            "equipo_nombre": equipo_nombre,
            "fecha_liberacion": fecha_liberacion,
            "fin_garantia": fin_garantia,
            "color_garantia": color_garantia,
        }

    def save(self, *args, **kwargs):
        if self.cod_pedido.estado != "CREADO":
            campos_editables_logistica = ["cantidad_preparada"]

            if self.pk:
                original = DetallePedido.objects.get(pk=self.pk)

                for campo in ["cod_repuesto", "cantidad", "numero_serie"]:
                    if getattr(self, campo) != getattr(original, campo):
                        raise ValidationError(f"Solo se pueden editar ítems cuando el pedido está en estado CREADO (estado actual: {self.cod_pedido.estado})")

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.cod_pedido.estado != 'CREADO':
            raise ValidationError(
                f"Solo se pueden eliminar ítems cuando el pedido está en estado CREADO "
                f"(estado actual: {self.cod_pedido.estado})"
            )

        super().delete(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cod_pedido", "cod_repuesto"],
                name="unique_repuesto_por_pedido"
            )
        ]
