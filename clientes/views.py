from django.shortcuts import render
from django.http import JsonResponse
from clientes.models import Clientes

def buscar_clientes_ajax(request):
    texto = request.GET.get("q", "").strip()

    if not texto:
        return JsonResponse([], safe=False)

    qs = (
        Clientes.objects.using("cliente")
        .filter(nombre__icontains=texto)[:20]
    )

    resultados = [
        {
            "id": c.id,
            "nombre": c.nombre,
            "cuit": c.cuit,
            "domicilio": c.domicilio,
            "ciudad": c.ciudad,
        }
        for c in qs
    ]

    return JsonResponse(resultados, safe=False)

