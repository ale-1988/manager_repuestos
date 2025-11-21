from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import models
from django.contrib.auth.decorators import login_required

from pedidos.models import Pedido, DetallePedido
from clientes.models import Clientes
from repuestos.models import Material


# ==========================================================
# NUEVO PEDIDO
# ==========================================================
@login_required
def nuevo_pedido(request):
    """Crea un pedido en estado BORRADOR y redirige a editar."""
    pedido = Pedido.objects.create(
        estado="BORRADOR",
        observaciones=""
    )
    return redirect("pedidos:editar_pedido", id_pedido=pedido.id)


# ==========================================================
# EDITAR PEDIDO
# ==========================================================
@login_required
def editar_pedido(request, id_pedido):

    pedido = get_object_or_404(Pedido, pk=id_pedido)
    detalles = pedido.detalles.all()
    resultado_busqueda = None

    # ------------------------------------------------------
    # BUSCAR CLIENTE (por ID, nombre o CUIT)
    # ------------------------------------------------------
    if request.method == "POST" and "buscar_cliente_btn" in request.POST:
        texto = request.POST.get("buscar_cliente", "").strip()
        resultado_busqueda = []

        if texto:
            qs = Clientes.objects.using("cliente").all()

            # Si es número → buscar por ID o por CUIT numérico
            if texto.isdigit():
                qs = qs.filter(
                    models.Q(id=int(texto)) |
                    models.Q(cuit__icontains=texto)
                )
            else:
                # Texto general: nombre o CUIT
                qs = qs.filter(
                    models.Q(nombre__icontains=texto) |
                    models.Q(cuit__icontains=texto)
                )

            resultado_busqueda = qs[:50]   # máximo 50 resultados

        return render(
            request,
            "pedidos/editar_pedido.html",
            {
                "pedido": pedido,
                "detalles": detalles,
                "resultado_busqueda": resultado_busqueda,
            },
        )

    # ------------------------------------------------------
    # ASIGNAR CLIENTE (desde formulario simple)
    # ------------------------------------------------------
    if request.method == "POST" and "asignar_cliente" in request.POST:
        try:
            id_cliente = int(request.POST.get("id_cliente"))
            cliente = Clientes.objects.using("cliente").get(pk=id_cliente)
        except:
            messages.error(request, "Cliente inválido.")
            return redirect("pedidos:editar_pedido", id_pedido=id_pedido)

        pedido.cod_cliente = id_cliente
        pedido.save()
        messages.success(request, f"Cliente asignado correctamente.")
        return redirect("pedidos:editar_pedido", id_pedido=id_pedido)

    # ------------------------------------------------------
    # GUARDAR PEDIDO
    # ------------------------------------------------------
    if request.method == "POST" and "guardar_pedido" in request.POST:
        if pedido.estado == "BORRADOR" and pedido.cod_cliente is None:
            messages.error(request, "Debe asignar un cliente antes de guardar.")
            return redirect("pedidos:editar_pedido", id_pedido=id_pedido)

        pedido.estado = "CREADO"
        pedido.save()
        messages.success(request, "Pedido guardado.")

        return redirect("pedidos:listar_pedidos")

    # ------------------------------------------------------
    # CANCELAR PEDIDO (solo si es BORRADOR)
    # ------------------------------------------------------
    if request.method == "POST" and "cancelar_pedido" in request.POST:
        if pedido.estado == "BORRADOR":
            pedido.delete()
            messages.success(request, "Pedido cancelado.")
            return redirect("/")
        else:
            messages.error(request, "No se puede cancelar un pedido en este estado.")
        return redirect("pedidos:editar_pedido", id_pedido=id_pedido)

    # ------------------------------------------------------
    # ELIMINAR ÍTEM
    # ------------------------------------------------------
    if request.method == "POST" and "eliminar_item" in request.POST:
        id_item = request.POST.get("eliminar_item")
        try:
            item = DetallePedido.objects.get(pk=id_item, cod_pedido=pedido)
            item.delete()
            messages.success(request, "Ítem eliminado.")
        except:
            messages.error(request, "No se pudo eliminar el ítem.")
        return redirect("pedidos:editar_pedido", id_pedido=id_pedido)

    # Construir datos dinámicos del cliente (todos los campos no nulos)
    datos_cliente = None
    if pedido.cliente:
        datos_cliente = {}
        for field in pedido.cliente._meta.fields:
            valor = getattr(pedido.cliente, field.name)
            if valor not in (None, "", " "):
                datos_cliente[field.verbose_name.capitalize()] = valor

    # ------------------------------------------------------
    # RENDER NORMAL DE LA PANTALLA
    # ------------------------------------------------------
    return render(
        request,
        "pedidos/editar_pedido.html",
        {
            "pedido": pedido,
            "detalles": detalles,
            "resultado_busqueda": resultado_busqueda,
            "datos_cliente":datos_cliente,
        }
    )


# ==========================================================
# ASIGNAR CLIENTE DIRECTAMENTE (enlace desde búsqueda)
# ==========================================================
@login_required
def asignar_cliente_directo(request, id_pedido, id_cliente):

    pedido = get_object_or_404(Pedido, pk=id_pedido)

    try:
        cliente = Clientes.objects.using("cliente").get(pk=id_cliente)
    except Clientes.DoesNotExist:
        messages.error(request, "Cliente no encontrado.")
        return redirect("pedidos:editar_pedido", id_pedido=id_pedido)

    pedido.cod_cliente = id_cliente
    pedido.save()

    messages.success(request, f"Cliente asignado: {cliente.nombre}")
    return redirect("pedidos:editar_pedido", id_pedido=id_pedido)


def listar_pedidos(request):
    pedidos = Pedido.objects.all().order_by("-fecha")
    return render(request, "pedidos/listar_pedidos.html", {"pedidos": pedidos})


def agregar_item(request, pedido_id, id_mate):
    pedido = get_object_or_404(Pedido, pk=pedido_id)

    # Cantidad fija por ahora
    cantidad = 1

    DetallePedido.objects.create(
        cod_pedido=pedido,
        cod_repuesto=id_mate,
        cantidad=cantidad
    )

    messages.success(request, "Ítem agregado correctamente.")
    return redirect("pedidos:editar_pedido", id_pedido=pedido_id)




def agregar_items_desde_modal(request):
    if request.method != "POST":
        return redirect("/")

    pedido_id = request.POST.get("pedido_id")
    pedido = Pedido.objects.get(pk=pedido_id)

    # Procesar cantidades enviadas por el formulario
    for key, value in request.POST.items():
        if key.startswith("cantidad_"):
            id_mate = int(key.replace("cantidad_", ""))
            try:
                cantidad = float(value)
            except:
                cantidad = 0

            if cantidad > 0:
                DetallePedido.objects.create(
                    cod_pedido=pedido,
                    cod_repuesto=id_mate,
                    cantidad=cantidad,
                )

    # Si enviaron número de serie, lo podés registrar en auditoría más adelante
    # numero_serie = request.POST.get("numero_serie")

    return redirect("pedidos:editar_pedido", pedido_id)
