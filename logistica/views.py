from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import OuterRef, Subquery, Case, When, Value, IntegerField

from decimal import Decimal, InvalidOperation
from pedidos.models import Pedido, DetallePedido, HistorialEstadoPedido
from pedidos.utils import fmt_decimal
from repuestos.models import Repuesto
from usuarios.models import Usuario

from datetime import timedelta

from django.core.paginator import Paginator
from pedidos.utils import es_movil

from django.conf import settings
from django.contrib.auth.decorators import login_required

#*****************************
#*****************************
#*****************************
@login_required
def listar_preparacion(request):

    orden = request.GET.get("orden", "fecha")
    dir = request.GET.get("dir", "desc")

    campos_ordenables = {
        "id": "id",
        "estado": "estado",
        "fecha": "fecha",
    }

    campo_orden = campos_ordenables.get(orden, "fecha")

    if dir == "desc":
        campo_orden = f"-{campo_orden}"

    pedidos = Pedido.objects.filter(
        estado__in=["PAGADO", "PREPARANDO"]
    ).order_by(campo_orden)

    cantidad_pedidos = pedidos.count()

    for pedido in pedidos:

        total = 0
        preparado = 0
        items = 0

        for item in pedido.detalles.all():
            items += 1
            total += item.cantidad
            preparado += item.cantidad_preparada

        pedido.total_items = items
        pedido.total_cantidad = total
        pedido.total_preparado = preparado

        if total > 0:
            pedido.progreso_preparacion = int(
                (preparado / total) * 100
            )
        else:
            pedido.progreso_preparacion = 0

    # Paginación
    items_por_pagina = (
        settings.PAGINACION_MOVIL
        if es_movil(request)
        else settings.PAGINACION_PC
    )

    paginator = Paginator(pedidos, items_por_pagina)
    page_number = request.GET.get("page")
    pedidos = paginator.get_page(page_number)

    return render(
        request,
        "logistica/listar_preparacion.html",
        {
            "pedidos": pedidos,
            "cantidad_pedidos": cantidad_pedidos,
            "orden": orden,
            "dir": dir,
        }
    )
    
#*****************************
#*****************************
#*****************************
@login_required
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

#*****************************
#*****************************
#*****************************
@login_required
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

#*****************************
#*****************************
#*****************************
@login_required
def consolidar_pedido(request, id):

    pedido = get_object_or_404(Pedido, pk=id)

    try:
        pedido.cambiar_estado(
            Pedido.CONSOLIDADO,
            usuario=request.user,
            observacion="Pedido consolidado"
        )

        messages.success(
            request, 
            "El pedido fue CONSOLIDADO correctamente, "
            "está disponible para su gestión en Entregas.")

    except ValidationError as e:
        messages.error(request, str(e))

    return redirect("logistica:detalle_preparacion", id=pedido.id)

#*****************************
#*****************************
#*****************************
@login_required
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

#*****************************
#*****************************
#*****************************
@login_required
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

#*****************************
#*****************************
#*****************************
@login_required
def guardar_preparacion(request, id):

    pedido = get_object_or_404(Pedido, pk=id)

    if request.method == "POST":

        for item in pedido.detalles.all():

            campo = f"prep_{item.id}"

            if campo in request.POST:

                valor = request.POST[campo]

                if not valor:
                    continue
                try:
                    item.actualizar_preparacion(valor)
                except ValidationError as e:

                    messages.error(request,str(e))
                    continue

    return redirect(
        "logistica:detalle_preparacion",
        id=pedido.id
    )

    return redirect(
        "logistica:detalle_preparacion",
        id=pedido.id
    )

#*****************************
#*****************************
#*****************************
@login_required
def actualizar_preparado(request, id):

    item = get_object_or_404(DetallePedido, pk=id)

    if request.method == "POST":
        valor = request.POST.get("cantidad_preparada")
        if valor:
            try:
                item.actualizar_preparacion(valor)
            except ValidationError as e:
                messages.error(
                    request,
                    str(e)
                )

    return redirect(
        "logistica:detalle_preparacion",
        id=item.cod_pedido.id
    )




#*****************************
#*****************************
#*****************************
@login_required
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
    
#*****************************
#*****************************
#*****************************
@login_required
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

#*****************************
#*****************************
#*****************************
@login_required
def confirmar_entrega(request, id):

    pedido = get_object_or_404(Pedido, pk=id)

    pedido.cambiar_estado(
        "ENTREGADO",
        usuario=request.user,
        observacion="Entrega confirmada"
    )

    return redirect("logistica:listar_entregas")

#*****************************
#*****************************
#*****************************
@login_required
def listar_entregas(request):

    filtro = request.GET.get("entregados", "ninguno")

    orden = request.GET.get("orden", "fecha")
    dir = request.GET.get("dir", "desc")

    hoy = timezone.now().date()

    # Siempre mostramos los pedidos activos
    pedidos_activos = Pedido.objects.filter(
        estado__in=[
            Pedido.CONSOLIDADO,
            Pedido.ENVIADO,
        ]
    )

    # Armamos el queryset de entregados según el filtro
    pedidos_entregados = Pedido.objects.none()

    if filtro == "mes":
        pedidos_entregados = Pedido.objects.filter(
            estado=Pedido.ENTREGADO,
            fecha__gte=hoy - timedelta(days=30)
        )

    elif filtro == "anio":
        pedidos_entregados = Pedido.objects.filter(
            estado=Pedido.ENTREGADO,
            fecha__gte=hoy - timedelta(days=365)
        )

    elif filtro == "todos":
        pedidos_entregados = Pedido.objects.filter(
            estado=Pedido.ENTREGADO
        )

    # Campo de ordenamiento
    if orden == "id":
        campo_orden = "id"
    else:
        campo_orden = "fecha"

    if dir == "desc":
        campo_orden = f"-{campo_orden}"

    pedidos = (
        pedidos_activos | pedidos_entregados
    ).annotate(
        prioridad=Case(
            # Sin transportista
            When(cod_transportista__isnull=True, then=Value(0)),

            # Entregados
            When(estado=Pedido.ENTREGADO, then=Value(2)),

            # Consolidados y enviados
            default=Value(1),

            output_field=IntegerField(),
        )
    ).order_by(
        "prioridad",
        campo_orden,
    )

    for pedido in pedidos:
        fechas = pedido.fechas_logisticas()
        pedido.fecha_logistica = fechas["logistica"]
        pedido.fecha_consolidado = fechas["consolidado"]
        pedido.fecha_enviado = fechas["enviado"]
        pedido.fecha_entregado = fechas["entregado"]

    # Paginación
    items_por_pagina = (
        settings.PAGINACION_MOVIL
        if es_movil(request)
        else settings.PAGINACION_PC
    )

    paginator = Paginator(pedidos, items_por_pagina)
    page_number = request.GET.get("page")
    pedidos = paginator.get_page(page_number)

    return render(
        request,
        "logistica/listar_entregas.html",
        {
            "pedidos": pedidos,
            "filtro_entregados": filtro,
            "orden": orden,
            "dir": dir,
        }
    )