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
        ("ANULADA", "Anulada"),
    ]

    TRANSICIONES_VALIDAS = {
        "BORRADOR": ["EMITIDA", "ANULADA"],
        "EMITIDA": ["PAGADA", "ANULADA"],
        "PAGADA": ["EMITIDA"],
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

    factura_referencia = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="notas_credito",
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

        if self.importe_total is None or self.importe_total <= 0:
            raise ValidationError("El importe debe ser mayor a cero.")

        if self.tipo == "FACTURA":
            if not self.pedido:
                raise ValidationError("Una factura debe estar asociada a un pedido.")

        if self.tipo == "NOTA_CREDITO":

            # Si tiene factura_referencia, validar coherencia
            if self.factura_referencia:

                if self.cod_cliente != self.factura_referencia.cod_cliente:
                    raise ValidationError(
                        "La NC debe tener el mismo cliente que la factura."
                    )

                if self.factura_referencia.tipo != "FACTURA":
                    raise ValidationError(
                        "Solo se puede generar nota de crédito sobre una factura."
                    )

            # Si NO tiene factura_referencia,
            # es crédito a cuenta (por sobrepago) y está permitido

    # ======================================
    # NUMERACIÓN AUTOMÁTICA SEGURA
    # ======================================
    def save(self, *args, **kwargs):

        if self.pk:
            original = Factura.objects.get(pk=self.pk)

            if original.estado != "BORRADOR":

                # Permitir solo cambio de estado
                campos_editables = [
                    "pedido",
                    "factura_referencia",
                    "cod_cliente",
                    "importe_total",
                    "tipo",
                    "observaciones",
                ]

                for campo in campos_editables:
                    if getattr(original, campo) != getattr(self, campo):
                        raise ValidationError(
                            "Solo se puede editar una factura en estado BORRADOR."
                        )

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
    # CAMBIO DE ESTADO CONTROLADO
    # ======================================
    def cambiar_estado(self, nuevo_estado, usuario):
        with transaction.atomic():
            if nuevo_estado not in dict(self.ESTADO_CHOICES):
                raise ValidationError("Estado inválido.")

            if nuevo_estado not in self.TRANSICIONES_VALIDAS[self.estado]:
                raise ValidationError(
                    f"No se puede pasar de {self.estado} a {nuevo_estado}"
                )

            # Validaciones previas específicas
            if nuevo_estado == "ANULADA" and self.pagos.exists():
                raise ValidationError("No se puede anular una factura con pagos.")

            if self.tipo == "NOTA_CREDITO" and nuevo_estado == "EMITIDA":
                factura = self.factura_referencia
                saldo = factura.saldo_actual()

                if self.importe_total > saldo:
                    raise ValidationError(
                        "La nota de crédito excede el saldo disponible de la factura."
                    )

            # Cambiar estado
            self.estado = nuevo_estado
            self.save()

            # Efectos colaterales
            if nuevo_estado == "PAGADA" and self.pedido:
                self.pedido.cambiar_estado("PAGADO", usuario)

            if nuevo_estado == "ANULADA" and self.pedido:
                self.pedido.cambiar_estado("CERRADO", usuario)

            if self.tipo == "NOTA_CREDITO" and self.factura_referencia:
                self.factura_referencia.verificar_estado_por_saldo(usuario)

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

    def total_notas_credito(self):
        return (
            self.notas_credito.filter(estado="EMITIDA")
            .aggregate(Sum("importe_total"))["importe_total__sum"]
            or 0
        )

    def total_creditos_aplicados(self):
        return (
            self.aplicaciones_credito.aggregate(Sum("monto"))["monto__sum"]
            or 0
        )

    def saldo_actual(self):
        return (
            self.importe_total
            - self.total_pagado()
            - self.total_creditos_aplicados()
        )

    # ======================================
    # VERIFICAR ESTADO POR SALDO
    # ======================================
    def verificar_estado_por_saldo(self, usuario=None):
        from usuarios.services import get_usuario_sistema
                
        if not usuario:
            usuario = get_usuario_sistema()

        saldo = self.saldo_actual()

        if saldo == 0 and self.estado == "EMITIDA":
            self.cambiar_estado("PAGADA", usuario)

        elif saldo > 0 and self.estado == "PAGADA":
            self.cambiar_estado("EMITIDA",usuario)


    def tiene_credito_disponible(self):
        from .models import AplicacionCredito

        creditos = Factura.objects.filter(
            tipo="NOTA_CREDITO",
            cod_cliente=self.cod_cliente,
            estado="EMITIDA"
        )

        for nc in creditos:

            # Ya aplicado a esta factura
            if AplicacionCredito.objects.filter(
                factura=self,
                nota_credito=nc
            ).exists():
                continue

            monto_disponible = nc.importe_total - nc.total_credito_aplicado()

            if monto_disponible > 0:
                return True

        return False

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

        if self.factura.estado not in ["EMITIDA", "PAGADA"]:
            raise ValidationError(
                "No se pueden registrar movimientos en esta factura."
            )

        total_actual = self.factura.total_pagado()

        if self.pk:
            pago_original = Pago.objects.get(pk=self.pk)
            total_actual -= pago_original.monto

        nuevo_total = total_actual + self.monto

        if nuevo_total < 0:
            raise ValidationError("El total pagado no puede quedar negativo.")

        limite = (
            self.factura.importe_total
            - self.factura.total_notas_credito()
        )

        if self.monto < 0 and not self.referencia.strip():
            raise ValidationError(
                "Debe indicar el motivo del reverso."
            )

    def save(self, *args, **kwargs):
        from django.db import transaction
        from .models import Factura

        with transaction.atomic():

            self.full_clean()

            factura = self.factura

            # Calcular saldo actual ANTES de guardar
            saldo_pendiente = factura.saldo_actual()

            # Si el pago supera el saldo → hay sobrepago
            if self.monto > saldo_pendiente:

                excedente = self.monto - saldo_pendiente

                # Ajustar el pago al saldo real
                self.monto = saldo_pendiente
                super().save(*args, **kwargs)

                # Crear Nota de Crédito automática
                nc = Factura.objects.create(
                    tipo="NOTA_CREDITO",
                    factura_referencia=None,
                    cod_cliente=factura.cod_cliente,
                    importe_total=excedente,
                    estado="EMITIDA",
                    observaciones="Crédito generado por sobrepago."
                )

                # Marcar factura como pagada
                factura.verificar_estado_por_saldo()

                # Guardar referencia para mostrar mensaje en vista
                self._nc_generada = nc
            else:
                super().save(*args, **kwargs)
                factura.verificar_estado_por_saldo()


    def delete(self, *args, **kwargs):
        raise ValidationError(
            "No se pueden eliminar pagos. Debe registrarse un movimiento compensatorio."
        )

    def __str__(self):
        return f"Pago {self.monto} - Factura {self.factura.numero}"

    
class AplicacionCredito(models.Model):

    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name="aplicaciones_credito",
    )

    nota_credito = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name="aplicaciones_realizadas",
        limit_choices_to={"tipo": "NOTA_CREDITO"},
    )

    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("factura", "nota_credito")

    def clean(self):

        if self.monto <= 0:
            raise ValidationError("El monto debe ser mayor a cero.")

        saldo_factura = self.factura.saldo_actual()
        if self.monto > saldo_factura:
            raise ValidationError("El monto excede el saldo de la factura.")

        saldo_nc = self.nota_credito.saldo_actual()
        if self.monto > saldo_nc:
            raise ValidationError("El monto excede el saldo disponible del crédito.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        # Verificar estado posterior
        self.factura.verificar_estado_por_saldo()

    def __str__(self):
        return f"Aplicación {self.monto}"
