from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
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

# ============================================================
#   AGREGAR ITEMS A PEDIDO (pantalla única)
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


# ============================================================
#   API: CONSULTAR NS  (modo A)
# ============================================================

@login_required
def api_consultar_ns(request):
    ns = request.GET.get("ns", "").strip()

    if not ns:
        return JsonResponse({"ok": False, "error": "NS vacío."})

    seg = (
        Seguimiento.objects
        .using("rpg2")
        .filter(seg_numero_serie=ns)
        .order_by("-seg_fecha_liberacion")
        .first()
    )

    if not seg or not seg.equi_codigo:
        return JsonResponse({
            "ok": True,
            "existe": False,
            "garantia": "INEXISTENTE",
        })

    # En tu código legacy, equi_codigo funciona como id_mate_equipo
    equipo_id_mate = int(seg.equi_codigo)
    fecha_liberacion = seg.seg_fecha_liberacion

    # Plazo garantía configurable (meses). Fallback a 36.
    meses = getattr(settings, "GARANTIA_MESES", 36)

    try:
        from dateutil.relativedelta import relativedelta
        fin_garantia = fecha_liberacion + relativedelta(months=meses)
    except Exception:
        fin_garantia = fecha_liberacion + timezone.timedelta(days=meses * 30)

    hoy = timezone.now()
    en_garantia = hoy <= fin_garantia

    return JsonResponse({
        "ok": True,
        "existe": True,
        "equipo_id_mate": equipo_id_mate,
        "fecha_liberacion": fecha_liberacion.strftime("%Y-%m-%d"),
        "fin_garantia": fin_garantia.strftime("%Y-%m-%d"),
        "garantia": "EN_GARANTIA" if en_garantia else "FUERA_DE_GARANTIA"
    })


# ============================================================
#   API: BUSCAR EQUIPOS (modo B)
#   Equipo = Material grupo 55 (con checkbox Ver obsoletos)
# ============================================================

@login_required
def buscar_equipo(request):
    texto = request.GET.get("texto", "").strip()

    print(">>> buscar_equipo EJECUTADA, texto =", texto)

    equipos = (
        Material.objects.using("remota")
        .filter(id_grup__id_grup=55)    # *** ESTA ES LA CORRECCIÓN IMPORTANTE ***
        .filter(valor__icontains=texto)
        .order_by("valor")
    )

    return render(request, "pedidos/buscar_equipo.html", {
        "equipos": equipos,
        "texto": texto,
    })


# ============================================================
#   API: LISTA MATERIALES DE EQUIPO (BOM)
#   Reutiliza tu get_materiales_por_equipo()
# ============================================================

@login_required
def api_lista_materiales_equipo(request):
    equipo_id_mate = request.GET.get("equipo_id_mate")
    if not equipo_id_mate:
        return JsonResponse({"ok": False, "error": "Falta equipo_id_mate"})

    materiales = get_materiales_por_equipo(int(equipo_id_mate))
    return JsonResponse({"ok": True, "materiales": materiales})


# ============================================================
#   API: BUSCAR MATERIALES LIBRES (modo C)
#   Igual que buscar_manual, pero JSON
# ============================================================

@login_required
def api_buscar_materiales(request):
    texto = request.GET.get("texto", "").strip()
    grupo = request.GET.get("grupo", "---")
    ver_obsoletos = request.GET.get("ver_obsoletos", "0") == "1"

    if not texto and grupo == "---":
        return JsonResponse({"ok": True, "materiales": []})

    qs = (
        Material.objects.using("remota")
        .select_related("id_grup", "material2")
    )

    if texto:
        qs = qs.filter(Q(valor__icontains=texto) | Q(descripcio__icontains=texto))

    if grupo != "---":
        qs = qs.filter(id_grup__GRUPO=grupo)

    if not ver_obsoletos:
        qs = qs.filter(material2__obsoleto=0)

    materiales = [{
        "id_mate": m.id_mate,
        "valor": m.valor,
        "grupo": m.id_grup.GRUPO if m.id_grup else "",
    } for m in qs[:300]]

    return JsonResponse({"ok": True, "materiales": materiales})


# ============================================================
#   API: AGREGAR ITEM AL PEDIDO
# ============================================================

@require_POST
@login_required
def api_agregar_item(request):
    pedido_id = request.POST.get("pedido_id")
    id_mate = request.POST.get("id_mate")
    cantidad = request.POST.get("cantidad", "1")

    pedido = get_object_or_404(Pedido, id=int(pedido_id))

    if not _pedido_editable(pedido):
        return JsonResponse({"ok": False, "error": "Pedido no editable."})

    try:
        cantidad = float(cantidad)
        if cantidad <= 0:
            raise ValueError()
    except Exception:
        return JsonResponse({"ok": False, "error": "Cantidad inválida."})

    detalle, created = DetallePedido.objects.get_or_create(
        cod_pedido=pedido,
        cod_repuesto=int(id_mate),
        defaults={"cantidad": cantidad}
    )

    if not created:
        detalle.cantidad = float(detalle.cantidad) + cantidad
        detalle.save()

    return JsonResponse({
        "ok": True,
        "created": created,
        "id_mate": int(id_mate),
        "cantidad_total": float(detalle.cantidad)
    })


@login_required
def equipo_materiales(request, id_mate):
    """
    Recibe id_mate del equipo seleccionado y obtiene su BOM real.
    """
    from repuestos.utils import get_materiales_por_equipo

    materiales = get_materiales_por_equipo(id_mate)

    return render(request, "pedidos/equipo_materiales.html", {
        "materiales": materiales,
        "id_mate": id_mate,
    })


