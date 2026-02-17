from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Factura
from .forms import FacturaForm, PagoForm
from django.core.exceptions import ValidationError

from django.http import HttpResponse

from django.core.mail import EmailMessage
from .utils import build_pdf_factura

# ==============================
# LISTAR FACTURAS
# ==============================
@login_required
def listar_facturas(request):

    estado = request.GET.get("estado")
    tipo = request.GET.get("tipo")
    cliente = request.GET.get("cliente")
    solo_saldo = request.GET.get("solo_saldo")

    facturas = Factura.objects.all()

    if estado:
        facturas = facturas.filter(estado=estado)

    if tipo:
        facturas = facturas.filter(tipo=tipo)

    if cliente:
        facturas = facturas.filter(cliente__username__icontains=cliente)

    if solo_saldo:
        facturas = [f for f in facturas if f.saldo_actual() > 0]

    return render(request, "facturacion/listar_facturas.html", {
        "facturas": facturas,
    })



# ==============================
# CREAR FACTURA
# ==============================
@login_required
def crear_factura(request):

    form = FacturaForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            factura = form.save()
            messages.success(request, "Factura creada correctamente.")
            return redirect("facturacion:detalle_factura", pk=factura.pk)

    return render(request, "facturacion/editar_factura.html", {
        "form": form
    })


# ==============================
# EDITAR FACTURA
# ==============================
@login_required
def editar_factura(request, pk):

    factura = get_object_or_404(Factura, pk=pk)

    form = FacturaForm(request.POST or None, instance=factura)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Factura actualizada.")
            return redirect("facturacion:detalle_factura", pk=pk)

    return render(request, "facturacion/editar_factura.html", {
        "form": form,
        "factura": factura
    })


# ==============================
# DETALLE FACTURA
# ==============================
@login_required
def detalle_factura(request, pk):

    factura = get_object_or_404(Factura, pk=pk)

    pago_form = PagoForm()

    return render(request, "facturacion/detalle_factura.html", {
        "factura": factura,
        "pago_form": pago_form
    })


# ==============================
# REGISTRAR PAGO
# ==============================
@login_required
def registrar_pago(request, pk):

    factura = get_object_or_404(Factura, pk=pk)

    if request.method == "POST":
        form = PagoForm(request.POST)

        if form.is_valid():
            pago = form.save(commit=False)
            pago.factura = factura
            pago.save()

            messages.success(request, "Pago registrado.")
        else:
            messages.error(request, form.errors)

    return redirect("facturacion:detalle_factura", pk=pk)

# ==============================
# EMITIR FACTURA
# ==============================
@login_required
def emitir_factura(request, pk):

    factura = get_object_or_404(Factura, pk=pk)

    try:
        factura.cambiar_estado("EMITIDA", request.user)
        messages.success(request, "Factura emitida correctamente.")

    except ValidationError as e:
        messages.error(request, e.message)

    return redirect("facturacion:detalle_factura", pk=pk)

# ==============================
# ANULAR FACTURA
# ==============================
@login_required
def anular_factura(request, pk):

    factura = get_object_or_404(Factura, pk=pk)

    try:
        factura.cambiar_estado("ANULADA", request.user)
        messages.success(request, "Factura anulada correctamente.")
    except ValidationError as e:
        messages.error(request, e.message)

    return redirect("facturacion:detalle_factura", pk=pk)

# ==============================
# CREAR NOTA DE CREDITO DESDE FACTURA
# ==============================
@login_required
def crear_nota_credito(request, pk):

    factura = get_object_or_404(Factura, pk=pk)

    if factura.estado == "ANULADA":
        messages.error(request, "No se puede generar nota sobre factura anulada.")
        return redirect("facturacion:detalle_factura", pk=pk)

    nc = Factura.objects.create(
        tipo="NOTA_CREDITO",
        factura_referencia=factura,
        cliente=factura.cod_cliente,
        importe_total=factura.saldo_actual(),
        estado="BORRADOR"
    )

    messages.success(request, "Nota de crédito creada en BORRADOR.")
    return redirect("facturacion:editar_factura", pk=nc.pk)

# ==============================
# GENERAR PDF FACTURA
# ==============================
@login_required
def generar_pdf_factura(request, pk):

    factura = get_object_or_404(Factura, pk=pk)

    pdf_bytes = build_pdf_factura(factura)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="factura_{factura.numero}.pdf"'
    )

    return response

# ==============================
# ENVIAR PDF FACTURA X EMAIL
# ==============================
@login_required
def enviar_factura_email(request, pk):

    factura = get_object_or_404(Factura, pk=pk)

    pdf_bytes = build_pdf_factura(factura)

    email = EmailMessage(
        subject=f"{factura.tipo} Nº {factura.numero}",
        body="Adjuntamos su comprobante.",
        to=[factura.cliente.email],
    )

    email.attach(
        f"factura_{factura.numero}.pdf",
        pdf_bytes,
        "application/pdf",
    )

    email.send()

    messages.success(request, "Factura enviada por email.")
    return redirect("facturacion:detalle_factura", pk=pk)
