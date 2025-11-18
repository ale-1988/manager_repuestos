from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Material, Material2, Equipos, Listamat, Seguimiento, Grupos
from repuestos.utils import get_materiales_por_equipo
from pedidos.models import Pedido, DetallePedido
from django.contrib import messages
from collections import defaultdict
from collections import OrderedDict

# ============================================================
#   BUSCAR (entrada principal)
# ============================================================

def buscar(request):
    """
    Vista principal: determina si el input es ID o NS.
    Regla:
        - Si es numérico y < 30000 → ID de repuesto
        - Caso contrario → Número de serie
        - Si NS no existe → advertirlo
    """
    if request.method == "POST":
        numero = request.POST.get("numero", "").strip()

        # --- CASO 1: ID de repuesto ---
        if numero.isdigit():
            valor_num = int(numero)
            if valor_num < 30000:
                return redirect("repuestos:repuesto_por_id", valor_num)

        # --- CASO 2: número de serie ---
        s = Seguimiento.objects.using("rpg2").filter(
            seg_numero_serie=numero
        ).first()

        if s and s.equi_codigo:
            return redirect("repuestos:lista_materiales_equipo", int(s.equi_codigo))

        # --- CASO 3: NS no encontrado ---
        messages.error(request, "No se encontró el número de serie en la base de seguimiento.")
        return redirect("repuestos:buscar")

    return render(request, "repuestos/buscar.html")

    

# ============================================================
#   MOSTRAR REPUESTO POR ID
# ============================================================
from django.contrib import messages

def repuesto_por_id(request, id_mate):
    """
    Muestra un material individual.
    Si el ID no existe → error manejado.
    """
    try:
        mat = Material.objects.using("remota").get(id_mate=id_mate)
    except Material.DoesNotExist:
        messages.error(request, f"El ID de repuesto {id_mate} no existe en la base.")
        return redirect("repuestos:buscar")

    if request.method == "POST":
        qty = request.POST.get("cantidad", "1")

        # Aquí todavía NO agregamos al pedido (estamos testeando repuestos)
        messages.success(request, f"Cantidad {qty} seleccionada (prueba).")
        return redirect("repuestos:buscar")

    return render(request, "repuestos/repuesto_por_id.html", {
        "mat": mat,
    })



# ============================================================
#   LISTA DE MATERIALES DEL EQUIPO (agrupada por grupos)
# ============================================================

def lista_materiales_equipo(request, id_mate):
    """
    Vista agrupada por grupo.
    """

    # 1 — obtener el equipo
    try:
        m2 = Material2.objects.using("remota").get(material_id=id_mate)
    except Material2.DoesNotExist:
        return render(request, "repuestos/lista_materiales_equipo.html", {
            "error": "El material no tiene asociado un equipo.",
            "equipo": None,
            "grupos": {},
        })

    id_equi = m2.conjunto_id

    equipo = (
        Equipos.objects.using("remota")
        .filter(id_equi=id_equi)
        .first()
    )

    # 2 — obtener lista de materiales (ya ordenada)
    materiales = get_materiales_por_equipo(id_mate)

    # 3 — agrupar por GRUPO
    grupos = defaultdict(list)

    for m in materiales:
        grupos[m["grupo"]].append(m)

    # ordenar grupos alfabéticamente
    grupos = OrderedDict(sorted(grupos.items(), key=lambda x: x[0].lower()))

    return render(request, "repuestos/lista_materiales_equipo.html", {
        "equipo": equipo,
        "grupos": grupos,
    })



# ============================================================
#   SELECCIÓN MANUAL DE EQUIPO
# ============================================================

def seleccionar_equipo(request):
    equipos = Equipos.objects.using("remota").order_by("equipo")

    if request.method == "POST":
        id_equi = request.POST.get("id_equi")
        return redirect("repuestos:lista_materiales", id_equi)

    return render(request, "repuestos/seleccionar_equipo.html", {
        "equipos": equipos
    })


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
