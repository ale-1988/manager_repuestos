from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Material, Material2, Equipos, Listamat, Seguimiento, Grupos
from repuestos.utils import get_materiales_por_equipo
from pedidos.models import Pedido, DetallePedido
from django.contrib import messages
from collections import defaultdict, OrderedDict
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


# ============================================================
#   BÚSQUEDA MANUAL DE REPUESTOS (por texto o grupo)
# ============================================================

from django.db.models import Q
from .models import Material, Grupos
from django.shortcuts import render

def buscar_manual(request):
    """
    Búsqueda manual de repuestos con filtros:
      - texto
      - grupo (combobox)
      - mostrar_obsoletos (checkbox)
      - orden y dirección (ID, Valor, Grupo, Stock)
    """

    texto = request.GET.get("texto", "").strip()
    grupo = request.GET.get("grupo", "---")  # --- = Todos
    mostrar_obsoletos = request.GET.get("mostrar_obsoletos", "") == "on"

    # Orden y dirección
    orden = request.GET.get("orden", "valor")      # campo por defecto
    direccion = request.GET.get("dir", "asc")      # asc o desc

    # Traer grupos desde la BD remota
    grupos = Grupos.objects.using("remota").order_by("GRUPO")

    materiales = []

    # Solo buscar si se tocó algo
    if texto or grupo != "---" or mostrar_obsoletos or request.GET.get("orden"):
        qs = (
            Material.objects
            .using("remota")
            .select_related("id_grup", "material2")  # para mat.id_grup y mat.material2
        )

        # Filtro por texto
        if texto:
            qs = qs.filter(
                Q(valor__icontains=texto) |
                Q(descripcio__icontains=texto)
            )

        # Filtro por grupo (si no es Todos)
        if grupo != "---":
            qs = qs.filter(id_grup__GRUPO=grupo)

        # Filtro por obsoletos
        if not mostrar_obsoletos:
            qs = qs.filter(material2__obsoleto=0)

        # Orden
        if direccion == "asc":
            qs = qs.order_by(orden)
        else:
            qs = qs.order_by("-" + orden)

        # Límite de seguridad
        materiales = qs[:500]

    return render(request, "repuestos/buscar_manual.html", {
        "materiales": materiales,
        "texto": texto,
        "grupo": grupo,
        "grupos": grupos,
        "mostrar_obsoletos": mostrar_obsoletos,
        "orden": orden,
        "direccion": direccion,
    })

@login_required
def repuesto_por_id(request, id_mate):
    try:
        material = (
            Material.objects
            .using("remota")
            .select_related("id_grup", "material2")
            .get(id_mate=id_mate)
        )
    except Material.DoesNotExist:
        return render(request, "repuestos/repuesto_por_id.html", {
            "error": "Repuesto no encontrado",
            "material": None
        })

    return render(request, "repuestos/repuesto_por_id.html", {
        "material": material,
    })



@login_required
def api_grupos(request):
    grupos = (
        Grupos.objects.using("remota")
        .order_by("GRUPO")
        .values_list("GRUPO", flat=True)
    )
    return JsonResponse({"ok": True, "grupos": list(grupos)})
