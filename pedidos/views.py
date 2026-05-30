from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from pedidos.models import Pedido, DetallePedido
from clientes.models import Clientes
from repuestos.models import Material, Material2, Grupos, Seguimiento
from repuestos.utils import get_materiales_por_equipo

from django.conf import settings
from django.utils import timezone

from pedidos.models import HistorialEstadoPedido
from facturacion.models import Factura
from django.core.exceptions import ValidationError

from django.http import HttpResponse

from django.core.mail import EmailMessage
from .utils import build_pdf_preliminar
from decimal import Decimal, InvalidOperation

# ==========================================================
# NUEVO PEDIDO — BUSCADOR DE CLIENTE (AJAX + LINKS)
# ==========================================================
@login_required
def nuevo_pedido_cliente(request):
    """
    Pantalla de búsqueda de cliente ANTES de crear pedido.
    Si viene cliente_id por GET, crea el pedido y redirige a editar.
    """

    # Si el usuario clickeó un cliente (link)
    cliente_id = request.GET.get("cliente_id")
    if cliente_id:
        try:
            cliente_id_int = int(cliente_id)
            # Validar que existe cliente en base remota
            Clientes.objects.using("cliente").get(pk=cliente_id_int)

            pedido = Pedido.objects.create(
                estado="BORRADOR",
                cod_cliente=cliente_id_int
            )
            return redirect("pedidos:editar", pedido.id)

        except (ValueError, Clientes.DoesNotExist):
            messages.error(request, "Cliente inválido o inexistente.")

    # Si no hay cliente_id, mostrar pantalla de búsqueda
    return render(request, "pedidos/nuevo_pedido_cliente.html")





# ==========================================================
# EDITAR PEDIDO
# ==========================================================
@login_required
def editar_pedido(request, id):
    pedido = get_object_or_404(Pedido, id=id)

    modo_dividir = request.GET.get("dividir") == "1"

    if request.method == "POST" and request.POST.get("dividir_confirmado") == "1":
        items_seleccionados = request.POST.getlist("item_dividir")

        if not items_seleccionados:
            messages.error(request, "Debe seleccionar al menos un item para dividir.")
            return redirect(f"/pedidos/{id}/editar?dividir=1")

        request.session["items_a_dividir"] = items_seleccionados
        return redirect("pedidos:confirmar_division", id=id)
    items = pedido.detalles.all()
    
    for item in items:
        #Mitad de la pila minima
        item.stock_critico = item.material.pila / 2
    puede_dividir = (items.count() > 1) and (pedido.estado == "CREADO")
    
    return render(request, "pedidos/editar_pedido.html", {
        "pedido": pedido,
        "modo_dividir": modo_dividir,
        "items": items,
        "puede_dividir": puede_dividir,
        "estados_posibles": pedido.estados_disponibles(),
        "todos_estados": [e[0] for e in Pedido.ESTADOS],
    })

# ==========================================================
# CONFIRMAR DIVISIÓN DEL PEDIDO
# ==========================================================
@login_required
def confirmar_division(request, id):
    pedido = get_object_or_404(Pedido, id=id)

    # Recuperar la lista guardada en la sesión
    items_ids = request.session.get("items_a_dividir", [])

    # Obtener los items seleccionados
    items = DetallePedido.objects.filter(id__in=items_ids, cod_pedido=pedido)

    if request.method == "POST":
        if not items:
            messages.error(request, "No hay ítems seleccionados para dividir.")
            return redirect("pedidos:editar", id=id)

        # ----------------------------------------------------
        # 1) Crear el pedido nuevo (pedido B)
        # ----------------------------------------------------
        nuevo = Pedido.objects.create(
            cod_cliente=pedido.cod_cliente,
            cod_transportista=pedido.cod_transportista,
            observaciones=pedido.observaciones,
            estado="CREADO",   
        )

        # ----------------------------------------------------
        # 2) Mover los ítems seleccionados al pedido nuevo
        # ----------------------------------------------------
        for it in items:
            DetallePedido.objects.create(
                cod_pedido=nuevo,
                cod_repuesto=it.cod_repuesto,
                cantidad=it.cantidad,
                numero_serie=it.numero_serie,
            )
            it.delete()  # eliminar del pedido original

        # Limpio la sesión
        try:
            del request.session["items_a_dividir"]
        except KeyError:
            pass

        # ----------------------------------------------------
        # HISTORIAL PEDIDO ORIGINAL
        # ----------------------------------------------------
        HistorialEstadoPedido.objects.create(
            pedido=pedido,
            usuario=request.user,
            estado_anterior=pedido.estado,
            estado_nuevo=pedido.estado,
            observacion="Algunos repuestos pasaron al pedido",
            pedido_relacionado=nuevo,
        )

        # ----------------------------------------------------
        # HISTORIAL PEDIDO NUEVO
        # ----------------------------------------------------
        HistorialEstadoPedido.objects.create(
            pedido=nuevo,
            usuario=request.user,
            estado_anterior="-",
            estado_nuevo="CREADO",
            observacion="Dividido del pedido",
            pedido_relacionado=pedido,
        )

        messages.success(
            request,
            f"Pedido dividido correctamente. Nuevo pedido creado: #{nuevo.id}"
        )

        return redirect("pedidos:editar", id=nuevo.id)

    # --------------------------------------------------------
    # GET → Mostrar pantalla de confirmación
    # --------------------------------------------------------
    return render(request, "pedidos/confirmar_division.html", {
        "pedido": pedido,
        "items": items,
    })


# ==========================================================
# LISTAR PEDIDOS
# ==========================================================
@login_required
def listar_pedidos(request):
    q = request.GET.get("q", "").strip()
    ver_entregados = request.GET.get("ver_entregados")
    
    # Parámetros para ordenar
    orden = request.GET.get("orden", "fecha")     # default → fecha
    direccion = request.GET.get("dir", "desc")    # default → descendente

    # Campos válidos (whitelist)
    campos_validos = {
        "id": "id",
        "cliente": "cod_cliente",
        "items": "total_items",
        "cant": "total_cantidades",
        "estado": "estado",
        "fecha": "fecha",
    }

    campo = campos_validos.get(orden, "fecha")

    # Construir orden real
    if direccion == "asc":
        order_by = campo
    else:
        order_by = "-" + campo

    pedidos = Pedido.objects.all()
    
    # Ocultar entregados por defecto
    if not ver_entregados:
        pedidos = pedidos.exclude(estado="ENTREGADO")
    
    # Filtro búsqueda
    if q:
        pedidos = pedidos.filter(id__icontains=q) | pedidos.filter(cod_cliente__icontains=q)

    pedidos = pedidos.annotate(
        total_items=Count("detalles"),
        total_cantidades=Sum("detalles__cantidad")
    ).order_by(order_by)

    return render(request, "pedidos/listar_pedidos.html", {
        "pedidos": pedidos,
        "q": q,
        "orden": orden,
        "dir": direccion,
    })

# ==========================================================
# CANCELAR PEDIDO
# ==========================================================
@login_required
def cancelar_pedido(request, id):
    """
    Si el pedido está en BORRADOR → se elimina.
    Si no → se marca como CANCELADO.
    Luego vuelve SIEMPRE al listado de pedidos.
    Solo admin o gerente pueden cancelar.
    """

    if request.user.rol not in ("admin", "gerente"):
        messages.error(request, "No tiene permisos para cancelar pedidos.")
        return redirect("pedidos:editar", id)

    pedido = get_object_or_404(Pedido, id=id)

    try:
        if pedido.estado == "BORRADOR":
            pedido.delete()
            messages.success(request, "El pedido en borrador fue eliminado correctamente.")
        else:
            pedido.cambiar_estado("CANCELADO",usuario=request.user)
            messages.success(request, "El pedido fue cancelado correctamente.")

    except ValidationError as e:
        messages.error(request,str(e))
    return redirect("pedidos:listar")            

# ==========================================================
# ACTUALIZAR ESTADO
# ==========================================================
@login_required
def actualizar_estado(request, id):
    """
    Permite cambiar el estado del pedido.
    Solo admin, gerente y operador pueden hacerlo.
    """
    if request.user.rol not in ("admin", "gerente", "operador"):
        messages.error(request, "No tiene permisos para modificar el estado.")
        return redirect("pedidos:editar", id)

    pedido = get_object_or_404(Pedido, id=id)

    if request.method == "POST":
        nuevo_estado = request.POST.get("estado")

        # Validar que sea uno de los estados posibles
        estados_validos = [e[0] for e in Pedido.ESTADOS]

        if nuevo_estado not in estados_validos:
            messages.error(request, "Estado inválido.")
        else:
            pedido.cambiar_estado(nuevo_estado,usuario=request.user)
            messages.success(request, "Estado actualizado correctamente.")

    return redirect("pedidos:editar", id)

# ============================================================
#   AGREGAR ITEMS — Pantalla principal
# ============================================================
def _pedido_editable(pedido: Pedido) -> bool:
    return pedido.estado == "CREADO"

@login_required
def agregar_items(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if not _pedido_editable(pedido):
        messages.error(request, "Este pedido no permite agregar ítems en su estado actual.")
        return redirect("pedidos:editar", pedido_id)

    return render(request, "pedidos/agregar_items.html", {
        "pedido": pedido,
        "cliente": pedido.cod_cliente,
        "editable": True,
    })


# ============================================================
# MODIFICAR CANTIDAD DE ITEM
# ============================================================

@login_required
@require_POST
def modificar_cantidad(request, detalle_id):

    detalle = get_object_or_404(
        DetallePedido,
        id=detalle_id
    )

    pedido = detalle.cod_pedido

    if pedido.estado not in ["BORRADOR", "CREADO", "CONFIRMADO"]:

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":

            return JsonResponse({
                "ok": False,
                "error": "Pedido no editable"
            })

        return redirect("pedidos:editar", pedido.id)

    accion = request.POST.get("accion")

    eliminado = False

    # --------------------------------------------------------
    # SUMA
    # --------------------------------------------------------
    if accion == "sumar":
        detalle.cantidad += 1
        detalle.save()

    # --------------------------------------------------------
    # RESTA
    # --------------------------------------------------------
    elif accion == "restar":
        if detalle.cantidad > 1:
            detalle.cantidad -= 1
            detalle.save()

    # --------------------------------------------------------
    # ELIMINAR
    # --------------------------------------------------------
    elif accion == "eliminar":
        detalle.delete()
        eliminado = True
        
    # -------------------------------------------------------- 
    # SETEAR CANTIDAD 
    # -------------------------------------------------------- 
    elif accion == "setear": 
        try: 
            nueva_cantidad = Decimal( request.POST.get("cantidad", "0")) 
            if nueva_cantidad > 0: 
                detalle.cantidad = nueva_cantidad
                detalle.save() 
        except (InvalidOperation, ValueError): 
            pass        

    # --------------------------------------------------------
    # RESPUESTA AJAX
    # --------------------------------------------------------
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "ok": True,
            "detalle_id": detalle_id,
            "cantidad": None if eliminado else detalle.cantidad,
            "eliminado": eliminado,
        })

    # --------------------------------------------------------
    # FALLBACK NORMAL
    # --------------------------------------------------------
    return redirect("pedidos:editar", pedido.id)


@login_required
def buscar_equipo(request):
    """
    Vista HTML que muestra lista de equipos para seleccionar.
    Equipo = Material en grupo 55.
    """
    texto = request.GET.get("texto", "").strip()

    equipos = (
        Material.objects.using("remota")
        .filter(id_grup=55)  # Grupo 55 = equipos
        .filter(valor__icontains=texto)
        .order_by("valor")
    )

    return render(request, "pedidos/buscar_equipo.html", {
        "equipos": equipos,
        "texto": texto,
    })

@login_required
def historial_global(request, pedido_id=None):

    historial = HistorialEstadoPedido.objects.select_related(
        "pedido", "usuario"
    )

    # Si viene pedido_id → modo pedido
    pedido = None
    if pedido_id:
        pedido = get_object_or_404(Pedido, id=pedido_id)
        historial = historial.filter(pedido=pedido)

    # -------------------------
    # Filtros
    # -------------------------
    pedido_q = request.GET.get("pedido")
    usuario_q = request.GET.get("usuario")
    estado_q = request.GET.get("estado")
    fecha_q = request.GET.get("fecha")

    if pedido_q and not pedido_id:
        historial = historial.filter(pedido__id__icontains=pedido_q)

    if usuario_q:
        historial = historial.filter(usuario__username__icontains=usuario_q)

    if estado_q:
        historial = historial.filter(
            Q(estado_anterior__icontains=estado_q) |
            Q(estado_nuevo__icontains=estado_q)
        )

    if fecha_q:
        historial = historial.filter(fecha__date=fecha_q)

    # -------------------------
    # ORDENAMIENTO
    # -------------------------
    orden = request.GET.get("orden", "fecha")
    direccion = request.GET.get("dir", "desc")

    campos_validos = {
        "fecha": "fecha",
        "usuario": "usuario__username",
        "estado_anterior": "estado_anterior",
        "estado_nuevo": "estado_nuevo",
        "pedido": "pedido__id",
    }

    campo = campos_validos.get(orden, "fecha")

    if direccion == "asc":
        order_by = campo
    else:
        order_by = "-" + campo

    historial = historial.order_by(order_by)

    return render(request, "pedidos/historial.html", {
        "historial": historial,
        "pedido_actual": pedido,
        "orden": orden,
        "dir": direccion,
    })
    
@login_required
def facturar_pedido(request, id):
    #print ("Entro en facturar_pedidos")
    pedido = get_object_or_404(Pedido, id=id)

    try:
        factura = pedido.crear_factura_desde_pedido(request.user)
        messages.success(request, "Factura creada correctamente.")

        return redirect("facturacion:detalle_factura", pk=factura.pk)

    except ValidationError as e:
        messages.error(request, str(e))
        return redirect("pedidos:editar", id=pedido.id)
    
@login_required
def comprobante_preliminar(request, id):

    pedido = get_object_or_404(Pedido, id=id)

    # --------------------------------------------
    # SOLO BORRADOR / CREADO / CONFIRMADO
    # --------------------------------------------
    estados_validos = ["BORRADOR", "CREADO", "CONFIRMADO"]

    if pedido.estado not in estados_validos:
        messages.error(
            request,
            "No puede emitirse comprobante preliminar para este estado."
        )
        return redirect("pedidos:editar", id=pedido.id)

    detalles = pedido.detalles.all()

    total = 0

    for d in detalles:
        try:
            subtotal = float(d.material.precio) * float(d.cantidad)
        except Exception:
            subtotal = 0
        d.subtotal=subtotal
        total += subtotal
        
    return render(
        request,
        "pedidos/comprobante_preliminar.html",
        {
            "pedido": pedido,
            "detalles": detalles,
            "total": total,
            "fecha": timezone.now(),
        }
    )    

@login_required
def generar_pdf_preliminar(request, id):

    pedido = get_object_or_404(Pedido, id=id)

    pdf_bytes = build_pdf_preliminar(pedido)

    # -----------------------------------------
    # ENVIO EMAIL OPCIONAL
    # -----------------------------------------
    enviar_email = request.GET.get("email") == "1"

    if enviar_email and pedido.cliente and pedido.cliente.email:

        email = EmailMessage(
            subject=f"Pedido preliminar #{pedido.id}",
            body="Adjuntamos comprobante preliminar.",
            to=[pedido.cliente.email],
        )

        email.attach(
            f"pedido_preliminar_{pedido.id}.pdf",
            pdf_bytes,
            "application/pdf",
        )

        email.send()

    response = HttpResponse(
        pdf_bytes,
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="pedido_preliminar_{pedido.id}.pdf"'
    )

    return response