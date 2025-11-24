#Generales
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.conf import settings
from django.utils import timezone

#Modelos
from pedidos.models import Pedido, DetallePedido
from repuestos.models import Material, Material2, Grupos, Seguimiento
from clientes.models import Clientes

#Utilidades
from repuestos.utils import get_materiales_por_equipo

# ============================================================
#   HELPER: estados que permiten editar
# ============================================================

def _pedido_editable(pedido):
    return pedido.estado in ("BORRADOR", "CREADO", "CONFIRMADO")


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

    equipo_id_mate = int(seg.equi_codigo)
    
    # ---- Buscar nombre del equipo ----
    try:
        mat = Material.objects.using("remota").get(pk=equipo_id_mate)
        equipo_nombre = mat.valor
    except Material.DoesNotExist:
        equipo_nombre = "(Equipo ???)"
        
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
        "equipo_nombre": equipo_nombre, 
        "fecha_liberacion": fecha_liberacion.strftime("%Y-%m-%d"),
        "fin_garantia": fin_garantia.strftime("%Y-%m-%d"),
        "garantia": "EN_GARANTIA" if en_garantia else "FUERA_DE_GARANTIA"
    })


# ============================================================
#   API: BUSCAR EQUIPOS (modo B)
#   Equipo = Material grupo 55 (con checkbox Ver obsoletos)
# ============================================================
@login_required
def api_buscar_equipos(request):
    q = request.GET.get("q", "").strip()
    ver_obs = request.GET.get("ver_obsoletos") == "1"

    qs = Material.objects.using("remota").filter(id_grup=55)

    if q:
        qs = qs.filter(valor__icontains=q)

    if not ver_obs:
        qs = qs.filter(material2__obsoleto=0)

    data = [{
        "id_mate": m.id_mate,
        "valor": m.valor,
        "obsoleto": m.material2.obsoleto
    } for m in qs[:50]]

    return JsonResponse({"ok": True, "equipos": data})


# ============================================================
#   API: LISTA MATERIALES DE EQUIPO (Modo A/B
# ============================================================

@login_required
def api_lista_materiales_equipo(request):
    equipo_id_mate = request.GET.get("equipo_id_mate")
    if not equipo_id_mate:
        return JsonResponse({"ok": False, "error": "Falta equipo_id_mate"})

    materiales = get_materiales_por_equipo(int(equipo_id_mate))
    return JsonResponse({"ok": True, "materiales": materiales})


# ============================================================
#   API: BUSCAR MATERIALES SUELTOS (modo C)
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
        "unidad": m.unidad,
        "cantidad": 1,
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
    numero_serie = request.POST.get("numero_serie") or None

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
        numero_serie=numero_serie,
        defaults={"cantidad": cantidad}
    )

    if not created:
        detalle.cantidad = float(detalle.cantidad) + cantidad
        detalle.save()

    return JsonResponse({
        "ok": True,
        "created": created,
        "id_mate": int(id_mate),
        "cantidad_total": float(detalle.cantidad),
        "numero_serie": numero_serie
    })


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
