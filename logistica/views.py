from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import OuterRef, Subquery

from decimal import Decimal
from pedidos.models import Pedido, DetallePedido, HistorialEstadoPedido
from repuestos.models import Repuesto
from usuarios.models import Usuario

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
            Pedido.CONSOLIDADO,
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

def listar_entregas(request):

    pedidos = Pedido.objects.filter(
        estado__in=[Pedido.CONSOLIDADO, Pedido.ENVIADO, Pedido.ENTREGADO]
    ).order_by("fecha", "id")

    return render(
        request,
        "logistica/listar_entregas.html",
        {"pedidos": pedidos}
    )
    



def detalle_entregas(request, id):

    pedido = get_object_or_404(Pedido, pk=id)
    fechas = pedido.fechas_logisticas()

    transportistas = Usuario.objects.filter(
        rol="transportista"
    ).order_by("username")
    
    if request.method == "POST" and pedido.estado == Pedido.CONSOLIDADO:
        transportista_id = request.POST.get("transportista")

        if transportista_id:
            pedido.cod_transportista_id = transportista_id
            pedido.save(update_fields=["cod_transportista"])

        return redirect("logistica:detalle_entregas", id=pedido.id)
    
    return render(
        request,
        "logistica/detalle_entregas.html",
        {
            "pedido": pedido,
            "transportistas": transportistas,
            "fechas": fechas
        }
    )
    



def enviar_pedido(request, id):
    pedido = get_object_or_404(Pedido, pk=id)
    if not pedido.cod_transportista:
        messages.error(
            request,
            "Debe asignarse un transportista antes de enviar el pedido."
        )
        return redirect("logistica:detalle_entregas", id=pedido.id)
    pedido.fecha_envio = timezone.now()
    pedido.cambiar_estado(
        Pedido.ENVIADO,
        usuario=request.user,
        observacion="Pedido despachado"
    )
    pedido.save(update_fields=["fecha_envio"])
    return redirect("logistica:listar_entregas")

def confirmar_entrega(request, id):

    pedido = get_object_or_404(Pedido, pk=id)

    pedido.cambiar_estado(
        "ENTREGADO",
        usuario=request.user,
        observacion="Entrega confirmada"
    )

    return redirect("logistica:listar_entregas")



def listar_entregas(request):
    historial = HistorialEstadoPedido.objects.filter(pedido=OuterRef("pk"))

    pedidos = (
        Pedido.objects
        .filter(estado__in=[Pedido.CONSOLIDADO, Pedido.ENVIADO, Pedido.ENTREGADO])
        .annotate(
            fecha_logistica=Subquery(
                historial.filter(
                    estado_nuevo=Pedido.PAGADO
                ).values("fecha")[:1]
            ),
            fecha_consolidado=Subquery(
                historial.filter(
                    estado_nuevo=Pedido.CONSOLIDADO
                ).values("fecha")[:1]
            ),
            fecha_enviado=Subquery(
                historial.filter(
                    estado_nuevo=Pedido.ENVIADO
                ).values("fecha")[:1]
            ),
            fecha_entregado=Subquery(
                historial.filter(
                    estado_nuevo=Pedido.ENTREGADO
                ).values("fecha")[:1]
            ),
            
        )
        .order_by("-fecha_entregado", "-fecha_enviado", "-fecha_consolidado")
    )


    return render(
        request,
        "logistica/listar_entregas.html",
        {"pedidos": pedidos}
    )