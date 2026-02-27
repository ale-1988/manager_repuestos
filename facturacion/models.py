from django.db import models, transaction
from django.db.models import Max, Sum
from django.core.exceptions import ValidationError
from usuarios.models import Usuario


class Factura(models.Model):

    # =========================
    # TIPOS
    # =========================
    TIPO_CHOICES = [
        ("FACTURA", "Factura"),
        ("NOTA_CREDITO", "Nota de Crédito"),
    ]

    # =========================
    # ESTADOS
    # =========================
    ESTADO_CHOICES = [
        ("BORRADOR", "Borrador"),
        ("EMITIDA", "Emitida"),
        ("PAGADA", "Pagada"),
        ("CONSUMIDA", "Consumida"),  # Solo para NC
        ("ANULADA", "Anulada"),
    ]

    TRANSICIONES_VALIDAS = {
        "BORRADOR": ["EMITIDA", "ANULADA"],
        "EMITIDA": ["PAGADA", "ANULADA"],
        "PAGADA": [],
        "CONSUMIDA": [],
        "ANULADA": [],
    }

    # =========================
    # RELACIONES
    # =========================
    pedido = models.OneToOneField(
        "pedidos.Pedido",
        on_delete=models.PROTECT,
        related_name="factura",
        null=True,
        blank=True,
    )

    # Para NC generadas por sobrepago
    factura_referencia = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="notas_generadas",
    )

    cod_cliente = models.IntegerField()

    # =========================
    # DATOS PRINCIPALES
    # =========================
    numero = models.PositiveIntegerField(unique=True, editable=False, null=True)

    tipo = models.CharField(
        max_length=15,
        choices=TIPO_CHOICES,
        default="FACTURA",
    )

    fecha_emision = models.DateTimeField(auto_now_add=True)

    importe_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default="BORRADOR",
    )

    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ["-numero"]

    # ======================================
    # CLIENTE
    # ======================================
    @property
    def cliente(self):
        from clientes.models import Clientes
        return Clientes.objects.using("cliente").get(pk=self.cod_cliente)

    # ======================================
    # VALIDACIONES
    # ======================================
    def clean(self):

        try:
            self.cliente
        except Exception:
            raise ValidationError("Cliente inválido.")

        if self.importe_total is None or self.importe_total < 0:
            raise ValidationError("El importe no puede ser negativo.")

        # =========================
        # FACTURA
        # =========================
        if self.tipo == "FACTURA":
            if not self.pedido:
                raise ValidationError("Una factura debe estar asociada a un pedido.")

        # =========================
        # NOTA DE CRÉDITO
        # =========================
        if self.tipo == "NOTA_CREDITO":

            # No puede estar en BORRADOR
            if self.estado == "BORRADOR":
                raise ValidationError(
                    "Una Nota de Crédito no puede estar en estado BORRADOR."
                )

            if not self.factura_referencia:
                raise ValidationError(
                    "Las notas de crédito deben tener factura de referencia."
                )

    # ======================================
    # NUMERACIÓN AUTOMÁTICA
    # ======================================
    def save(self, *args, **kwargs):

        self.full_clean()

        if not self.numero:
            with transaction.atomic():
                ultimo = (
                    Factura.objects.select_for_update()
                    .aggregate(Max("numero"))["numero__max"]
                )
                self.numero = (ultimo or 0) + 1

        super().save(*args, **kwargs)

    # ======================================
    # CAMBIO DE ESTADO
    # ======================================
    def cambiar_estado(self, nuevo_estado, usuario):

        with transaction.atomic():

            if nuevo_estado not in dict(self.ESTADO_CHOICES):
                raise ValidationError("Estado inválido.")

            if nuevo_estado not in self.TRANSICIONES_VALIDAS[self.estado]:
                raise ValidationError(
                    f"No se puede pasar de {self.estado} a {nuevo_estado}"
                )
            # =========================
            # RESTRICCIONES PARA NC
            # =========================
            if self.tipo == "NOTA_CREDITO":

                if nuevo_estado == "BORRADOR":
                    raise ValidationError(
                        "Una Nota de Crédito no puede volver a BORRADOR."
                    )

                if nuevo_estado == "PAGADA":
                    raise ValidationError(
                        "Una Nota de Crédito no puede pasar a estado PAGADA."
                    )
            # ======================================
            # EMISIÓN DE FACTURA
            # ======================================
            if self.tipo == "FACTURA" and nuevo_estado == "EMITIDA":

                creditos = Factura.objects.select_for_update().filter(
                    tipo="NOTA_CREDITO",
                    cod_cliente=self.cod_cliente,
                    estado="EMITIDA",
                )

                total_credito = (
                    creditos.aggregate(Sum("importe_total"))["importe_total__sum"]
                    or 0
                )

                if total_credito > 0:

                    importe_original = self.importe_total

                    descuento = min(total_credito, importe_original)
                    restante_credito = total_credito - descuento

                    # Aplicar descuento a la factura
                    self.importe_total = importe_original - descuento

                    # Consumir todas las NC existentes
                    for nc in creditos:
                        nc.estado = "CONSUMIDA"
                        nc.save()

                    # Si sobró crédito → generar nueva NC
                    if restante_credito > 0:
                        Factura.objects.create(
                            tipo="NOTA_CREDITO",
                            factura_referencia=self,
                            cod_cliente=self.cod_cliente,
                            importe_total=restante_credito,
                            estado="EMITIDA",
                            observaciones="Crédito remanente por aplicación automática.",
                        )
                        
            # ======================================
            # ANULACIÓN DE FACTURA
            # ======================================
            if self.tipo == "FACTURA" and nuevo_estado == "ANULADA":
                
                # Pago real
                total_pagado = self.total_pagado()
                
                # Generar NC por el importe pagado de la factura
                if total_pagado > 0:
                    Factura.objects.create(
                        tipo="NOTA_CREDITO",
                        factura_referencia=self,
                        cod_cliente=self.cod_cliente,
                        importe_total=total_pagado,
                        estado="EMITIDA",
                        observaciones="Nota de crédito generada por anulación de factura.",
                    )

            # ======================================
            # CAMBIO DE ESTADO
            # ======================================
            self.estado = nuevo_estado
            self.save()

            # Historial
            HistorialEstadoFactura.objects.create(
                factura=self,
                estado=nuevo_estado,
                usuario=usuario,
            )
    # ======================================
    # TOTALES
    # ======================================
    def total_pagado(self):
        return self.pagos.aggregate(Sum("monto"))["monto__sum"] or 0

    def saldo_actual(self):
        return self.importe_total - self.total_pagado()

    @classmethod
    def credito_disponible_cliente(cls, cod_cliente):
        return (
            cls.objects.filter(
                tipo="NOTA_CREDITO",
                cod_cliente=cod_cliente,
                estado="EMITIDA",
            ).aggregate(Sum("importe_total"))["importe_total__sum"]
            or 0
        )

    def verificar_estado_por_saldo(self, usuario=None):

        from usuarios.services import get_usuario_sistema

        if not usuario:
            usuario = get_usuario_sistema()

        saldo = self.saldo_actual()

        if saldo == 0 and self.estado == "EMITIDA":
            self.cambiar_estado("PAGADA", usuario)

    def __str__(self):
        return f"{self.tipo} Nº {self.numero}"


# =====================================================
# HISTORIAL
# =====================================================
class HistorialEstadoFactura(models.Model):

    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name="historial_estados",
    )

    estado = models.CharField(max_length=15)

    fecha = models.DateTimeField(auto_now_add=True)

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
    )

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.factura} → {self.estado}"


# =====================================================
# PAGOS
# =====================================================
class Pago(models.Model):

    MEDIO_PAGO_CHOICES = [
        ("EFECTIVO", "Efectivo"),
        ("TRANSFERENCIA", "Transferencia"),
        ("CUENTA_CORRIENTE", "Cuenta Corriente"),
        ("OTRO", "Otro"),
    ]

    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name="pagos",
    )

    fecha = models.DateTimeField(auto_now_add=True)

    medio_pago = models.CharField(
        max_length=20,
        choices=MEDIO_PAGO_CHOICES,
    )

    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    referencia = models.CharField(
        max_length=100,
        blank=True,
    )

    def clean(self):
        if not self.factura_id:
            return
        
        # No permitir pagos sobre NC
        if self.factura.tipo != "FACTURA":
            raise ValidationError(
                "No se pueden registrar pagos en una Nota de Crédito."
            )
        
        if self.factura.estado not in ["EMITIDA", "PAGADA"]:
            raise ValidationError(
                "No se pueden registrar pagos en esta factura."
            )

    def save(self, *args, **kwargs):

        with transaction.atomic():

            self.full_clean()

            if not self.factura_id:
                raise ValidationError("El pago debe tener factura asociada.")
            
            factura = self.factura

            saldo_pendiente = factura.saldo_actual()

            # Sobrepago → generar NC
            if self.monto > saldo_pendiente:

                excedente = self.monto - saldo_pendiente

                self.monto = saldo_pendiente
                super().save(*args, **kwargs)

                Factura.objects.create(
                    tipo="NOTA_CREDITO",
                    factura_referencia=factura,
                    cod_cliente=factura.cod_cliente,
                    importe_total=excedente,
                    estado="EMITIDA",
                )

            else:
                super().save(*args, **kwargs)

            factura.verificar_estado_por_saldo()

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "No se pueden eliminar pagos. Debe registrarse un movimiento compensatorio."
        )

    def __str__(self):
        return f"Pago {self.monto} - Factura {self.factura.numero}"