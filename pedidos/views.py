from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from pedidos.models import Pedido, DetallePedido
from clientes.models import Clientes


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
# API AJAX — BUSCAR CLIENTES
# ==========================================================
@login_required
def api_buscar_clientes(request):
    """
    Devuelve JSON con clientes filtrados por nombre o CUIT.
    Usa base remota 'cliente', tabla 'datos'.
    """
    q = (request.GET.get("q") or "").strip()

    if len(q) < 2:
        return JsonResponse([], safe=False)

    # Importante: la tabla clientes está en la BD remota "cliente"
    clientes_qs = Clientes.objects.using("cliente").filter(
        Q(nombre__icontains=q) | Q(cuit__icontains=q)
    ).order_by("nombre")[:20]

    data = []
    for c in clientes_qs:
        data.append({
            "id": c.pk,
            "nombre": getattr(c, "nombre", str(c.pk)),
            "cuit": getattr(c, "cuit", "") or "",
        })

    return JsonResponse(data, safe=False)


# ==========================================================
# EDITAR PEDIDO
# ==========================================================
@login_required
def editar_pedido(request, id):
    pedido = get_object_or_404(Pedido, id=id)
    items = DetallePedido.objects.filter(cod_pedido=pedido)

    return render(request, "pedidos/editar_pedido.html", {
        "pedido": pedido,
        "items": items,
    })


# ==========================================================
# BUSCAR / LISTAR PEDIDOS
# ==========================================================
@login_required
def buscar_pedido(request):
    q = request.GET.get("q", "").strip()

    if q:
        pedidos = Pedido.objects.filter(
            Q(id__icontains=q) |
            Q(cod_cliente__icontains=q)
        ).order_by("-id")
    else:
        pedidos = Pedido.objects.all().order_by("-id")[:50]

    return render(request, "pedidos/buscar.html", {
        "pedidos": pedidos,
        "q": q,
    })


# ==========================================================
# DETALLE DEL PEDIDO (OPCIONAL)
# ==========================================================
@login_required
def detalle_pedido(request, id):
    pedido = get_object_or_404(Pedido, id=id)
    items = DetallePedido.objects.filter(cod_pedido=pedido)

    return render(request, "pedidos/detalle_pedido.html", {
        "pedido": pedido,
        "items": items,
    })


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





# ==========================================================
# AGREGAR ITEMS (DEPRECATED)
# ==========================================================
@login_required
def agregar_items_desde_modal(request):
    if request.method == "POST":
        pedido_id = request.POST.get("pedido_id")
        pedido = get_object_or_404(Pedido, id=pedido_id)

        for key, value in request.POST.items():
            if key.startswith("cant_"):
                try:
                    repuesto_id = int(key.replace("cant_", ""))
                    cantidad = float(value)
                except:
                    cantidad = 0

                if cantidad > 0:
                    DetallePedido.objects.create(
                        cod_pedido=pedido,
                        cod_repuesto=repuesto_id,
                        cantidad=cantidad,
                    )

        return redirect("pedidos:editar", pedido.id)

    messages.error(request, "Método no permitido.")
    return redirect("pedidos:listar")
