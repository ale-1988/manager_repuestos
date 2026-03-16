from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from pedidos.models import Pedido, DetallePedido
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.http import JsonResponse
from repuestos.models import Repuesto

# Create your views here.

def listar_preparacion(request):

    pedidos = Pedido.objects.filter(
        estado__in=["PAGADO","PREPARANDO"]
    ).order_by("fecha", "id")

    for pedido in pedidos:

        total = 0
        preparado = 0
        items = 0

        for item in pedido.detalles.all():
            items +=1
            total += item.cantidad
            preparado += item.cantidad_preparada

        pedido.total_items = items
        pedido.total_cantidad = total
        pedido.total_preparado = preparado

        if total > 0:
            pedido.progreso_preparacion = int((preparado / total) * 100)
        else:
            pedido.progreso_preparacion = 0    
    
    
    return render(
        request,
        "logistica/listar_preparacion.html",
        {"pedidos": pedidos}
    )

def detalle_preparacion(request, id):

    pedido = get_object_or_404(Pedido, pk=id)

    detalles = list(pedido.detalles.all())

    # obtener todos los ids de repuestos
    ids_repuestos = [d.cod_repuesto for d in detalles]

    # traer todos los repuestos en una sola consulta
    repuestos = Repuesto.objects.using("remota").filter(id_mate__in=ids_repuestos)

    # crear diccionario id → repuesto
    repuestos_dict = {r.id_mate: r for r in repuestos}

    # asociar nombre al detalle
    for d in detalles:
        d.repuesto = repuestos_dict.get(d.cod_repuesto)

    pedido_completo = all(
    d.cantidad_preparada >= d.cantidad for d in detalles
)
    return render(
        request,
        "logistica/detalle_preparacion.html",
        {
            "pedido": pedido,
            "detalles": detalles,
            "pedido_completo": pedido_completo
        }
    )
    
def listar_entregas(request):

    pedidos = Pedido.objects.filter(
        estado__in=["CONSOLIDADO", "ENVIADO"]
    ).order_by("fecha")

    return render(
        request,
        "logistica/listar_entregas.html",
        {"pedidos": pedidos}
    )
    
def detalle_entregas(request, id):

    pedido = get_object_or_404(Pedido, pk=id)

    return render(
        request,
        "logistica/detalle_entregas.html",
        {"pedido": pedido}
    )          

def comenzar_preparacion(request, id):

    pedido = get_object_or_404(Pedido, pk=id)

    try:
        pedido.cambiar_estado(
            Pedido.PREPARANDO,
            usuario=request.user,
            observacion="Inicio de preparación"
        )

        messages.success(request, "El pedido pasó a estado PREPARANDO.")

    except ValidationError as e:
        messages.error(request, str(e))

    return redirect("logistica:detalle_preparacion", id=pedido.id)

def consolidar_pedido(request, id):

    pedido = get_object_or_404(Pedido, pk=id)

    try:
        pedido.cambiar_estado(
            Pedido.ESTADO_CONSOLIDADO,
            usuario=request.user,
            observacion="Pedido consolidado"
        )

        messages.success(request, "El pedido fue CONSOLIDADO.")

    except ValidationError as e:
        messages.error(request, str(e))

    return redirect("logistica:detalle_preparacion", id=pedido.id)

def enviar_pedido(request, id):

    pedido = get_object_or_404(Pedido, pk=id)

    try:
        pedido.cambiar_estado(
            Pedido.ESTADO_ENVIADO,
            usuario=request.user,
            observacion="Pedido enviado"
        )

        messages.success(request, "El pedido fue ENVIADO.")

    except ValidationError as e:
        messages.error(request, str(e))

    return redirect("logistica:detalle_entregas", id=pedido.id)

def confirmar_entrega(request, id):

    pedido = get_object_or_404(Pedido, pk=id)

    try:
        pedido.cambiar_estado(
            Pedido.ESTADO_ENTREGADO,
            usuario=request.user,
            observacion="Entrega confirmada"
        )

        messages.success(request, "El pedido fue ENTREGADO.")

    except ValidationError as e:
        messages.error(request, str(e))

    return redirect("logistica:detalle_entregas", id=pedido.id)


def guardar_preparacion(request, id):

    pedido = get_object_or_404(Pedido, pk=id)

    if request.method == "POST":

        for item in pedido.detalles.all():

            campo = f"prep_{item.id}"

            if campo in request.POST:
                valor = request.POST[campo]

                if valor:
                    item.cantidad_preparada = Decimal(valor)
                    item.save(update_fields=["cantidad_preparada"])

    return redirect("logistica:detalle_preparacion", id=pedido.id)

def actualizar_preparado(request, id):

    item = get_object_or_404(DetallePedido, pk=id)

    if request.method == "POST":

        valor = request.POST.get("cantidad_preparada")

        if valor:
            item.cantidad_preparada = Decimal(valor)
            item.save(update_fields=["cantidad_preparada"])

    return redirect("logistica:detalle_preparacion", id=item.cod_pedido.id)

