from collections import defaultdict, OrderedDict
from repuestos.models import Listamat, Material


def get_lista_materiales_por_equipo(id_equi):
    """
    Devuelve un diccionario:
    {
       "Grupo A": [material1, material2, material3],
       "Grupo B": [...],
       ...
    }
    Todos ordenados alfabéticamente por Material.valor
    """

    # 1) obtener las entradas listamat del equipo
    items = Listamat.objects.filter(id_equi=id_equi, imprimir=1)

    # 2) obtener los materiales involucrados
    materiales_ids = [item.id_mate for item in items]

    materiales = (
        Material.objects
        .select_related("id_grup")        # grupos
        .filter(id_mate__in=materiales_ids)
        .order_by("valor")                # orden alfabético
    )

    # 3) agrupar por nombre de grupo
    grupos_dict = defaultdict(list)

    for mat in materiales:
        grupo = mat.id_grup.GRUPO if mat.id_grup and mat.id_grup.GRUPO else "Sin Grupo"
        grupos_dict[grupo].append(mat)

    # 3.5) ordenar grupos alfabeticamente
    grupos_ordenados=OrderedDict(
        sorted(grupos_dict.items(),key=lambda x: x[0].lower())
    )


    # 4) El diccionario está listo
    #return grupos_dict
    return grupos_ordenados
