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
    puede_dividir = (items.count() > 1) and (pedido.estado in ["BORRADOR", "CREADO"])
    
    return render(request, "pedidos/editar_pedido.html", {
        "pedido": pedido,
        "modo_dividir": modo_dividir,
        "items": items,
        "puede_dividir": puede_dividir,
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
            estado="BORRADOR",   # o el estado que quieras
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
#@login_required
# def listar_pedidos(request):
#     q = request.GET.get("q", "").strip()

#     pedidos = Pedido.objects.all()

#     if q:
#         pedidos = pedidos.filter(id__icontains=q) | pedidos.filter(cod_cliente__icontains=q)

#     pedidos = pedidos.annotate(
#         total_items=Count("detalles"),               # cantidad de repuestos distintos
#         total_cantidades=Sum("detalles__cantidad")   # suma de cantidades
#     ).order_by("-id")

#     return render(request, "pedidos/listar_pedidos.html", {
#         "pedidos": pedidos,
#         "q": q,
#     })
@login_required
def listar_pedidos(request):
    q = request.GET.get("q", "").strip()

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

    # Si es borrador → borrar
    if pedido.estado == "BORRADOR":
        pedido.delete()
        messages.success(request, "El pedido en borrador fue eliminado correctamente.")
        return redirect("pedidos:listar")

    # Caso normal: cancelar
    pedido.estado = "CANCELADO"
    pedido.save()

    messages.success(request, "El pedido fue cancelado correctamente.")
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
            pedido.estado = nuevo_estado
            pedido.save()
            messages.success(request, "Estado actualizado correctamente.")

    return redirect("pedidos:editar", id)

# ============================================================
#   AGREGAR ITEMS — Pantalla principal
# ============================================================
def _pedido_editable(pedido: Pedido) -> bool:
    return pedido.estado in ("BORRADOR", "CREADO", "CONFIRMADO")

@login_required
def agregar_items(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if not _pedido_editable(pedido):
        messages.error(request, "Este pedido no permite agregar ítems en su estado actual.")
        return redirect("pedidos:editar", pedido_id)

    return render(request, "pedidos/agregar_items.html", {
        "pedido": pedido,
        "cliente": pedido.cliente,
        "editable": True,
    })


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
