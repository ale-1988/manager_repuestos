from django import forms
from .models import Factura, Pago


class FacturaForm(forms.ModelForm):

    class Meta:
        model = Factura
        fields = [
            "pedido",
            "factura_referencia",
            "cod_cliente",
            "tipo",
            "importe_total",
            "observaciones",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.tipo == "NOTA_CREDITO":
            self.fields["pedido"].disabled = True
        # Bloquear edición si no está en BORRADOR
        if self.instance.pk and self.instance.estado != "BORRADOR":
            for field in self.fields:
                self.fields[field].disabled = True


class PagoForm(forms.ModelForm):

    class Meta:
        model = Pago
        fields = ["medio_pago", "monto", "referencia"]


    def __init__(self, *args, factura=None, **kwargs):
        self.factura = factura
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        if self.factura and self.factura.estado not in ["EMITIDA", "PAGADA"]:
            raise forms.ValidationError(
                "No se pueden registrar pagos en esta factura."
            )

        return cleaned_data