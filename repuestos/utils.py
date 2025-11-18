from collections import defaultdict, OrderedDict
from repuestos.models import Listamat, Material, Material2, Grupos


def get_materiales_por_equipo(id_mate):
    """
    Función definitiva.
    Dado un id_mate (proveniente de seguimiento), obtiene:
    1) el equipo al que pertenece ese material (material2.conjunto)
    2) todos los materiales de ese equipo desde listamat
    3) valor, grupo y cantidad de cada material
    4) ordena por grupo y valor

    Devuelve una lista de dicts:
    [
        {
            "id_mate": int,
            "valor": str,
            "grupo": str,
            "cantidad": float,
            "id_equi": int,
        },
        ...
    ]
    """

    # 1 — Obtener material2 para rescatar conjunto (id_equi)
    try:
        m2 = Material2.objects.using("remota").get(material_id=id_mate)
    except Material2.DoesNotExist:
        return []

    id_equi = m2.conjunto_id

    # 2 — Traer todas las filas listamat del equipo
    items = (
        Listamat.objects.using("remota")
        .filter(id_equi=id_equi)
        .values("id_mate", "cantidad")
    )

    resultado = []

    # 3 — Para cada id_mate de listamat, traer Material + Grupo
    for item in items:
        idm = item["id_mate"]
        cant_raw = item["cantidad"]
        
        # Formateo “int si es entero, sino dejar decimales”
        if cant_raw is None:
            cant_fmt = ""
        else:
            try:
                c = float(cant_raw)
                if c.is_integer():
                    cant_fmt = int(c)          # 1.0 -> 1
                else:
                    # respeta el valor con decimales, sin ceros sobrantes
                    cant_fmt = str(c).rstrip("0").rstrip(".")  # 0.100 -> "0.1"
            except Exception:
                cant_fmt = cant_raw  # por las dudas, dejar lo que venga

        try:
            mat = (
                Material.objects
                .using("remota")
                .select_related("id_grup")
                .get(id_mate=idm)
            )
            m2_child = mat.material2 # 1 a 1
        except Material.DoesNotExist:
            continue  # Material inexistente → skip

        grupo = mat.id_grup.GRUPO if mat.id_grup else "Sin grupo"

        # formateo de cantidad
        if cant_raw is None:
            cant_fmt = ""
        else:
            c = float(cant_raw)
            cant_fmt = int(c) if c.is_integer() else str(c).rstrip("0").rstrip(".")

        resultado.append({
            "id_mate": mat.id_mate,
            "valor": mat.valor,
            "grupo": grupo,
            "cantidad": cant_fmt,
            "is_conjunto": (m2_child.conjunto_id != 0),
        })

    # 4 — Ordenar por grupo y valor
        resultado_ordenado = sorted(
        resultado,
        key=lambda x: (x["grupo"].lower(), x["valor"].lower())
    )

    return resultado_ordenado




# def get_materiales_por_equipo_desde_idmate(id_mate):
#     """
#     Dado un id_mate:
#     1) obtiene el 'conjunto' desde material2 (id_equi)
#     2) busca en listamat todos los id_mate del equipo
#     3) obtiene Material + Grupo + Cantidad
#     4) ordena alfabeticamente por grupo y valor
#     """

#     # 1) Obtener material2 → conjunto (id_equi)
#     try:
#         m2 = Material2.objects.using("remota").get(material_id=id_mate)
#     except Material2.DoesNotExist:
#         return []

#     id_equi = m2.conjunto_id

#     # 2) Traer todos los items listamat del equipo
#     items = (
#         Listamat.objects.using("remota")
#         .filter(id_equi=id_equi)
#         .values("id_mate", "cantidad")
#     )

#     resultado = []

#     for item in items:
#         idm = item["id_mate"]
#         cant = item["cantidad"]

#         try:
#             mat = Material.objects.using("remota").select_related("id_grup").get(id_mate=idm)
#         except Material.DoesNotExist:
#             continue

#         grupo = mat.id_grup.GRUPO if mat.id_grup else "Sin grupo"

#         resultado.append({
#             "id_mate": mat.id_mate,
#             "valor": mat.valor,
#             "grupo": grupo,
#             "cantidad": cant,
#         })

#     # 3) Ordenar: primero por grupo, luego por valor
#     resultado_ordenado = sorted(
#         resultado,
#         key=lambda x: (x["grupo"].lower(), x["valor"].lower())
#     )

#     return resultado_ordenado



