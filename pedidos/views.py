from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Pedido, DetallePedido
from clientes.models import Clientes

@login_required
def inicio(request):
    return render(request, "inicio.html")

@login_required
def nuevo_pedido(request):
    # Crea un pedido vacío en estado BORRADOR
    pedido = Pedido.objects.create(
        estado="BORRADOR",
        cod_cliente=None,
        observaciones=""
    )

    # Redirige a la edición del pedido
    return redirect("pedidos:editar_pedido", id_pedido=pedido.id)

@login_required
def editar_pedido(request, id_pedido):
    pedido = get_object_or_404(Pedido, pk=id_pedido)

    # ===========================
    # 1. Actualizar cliente
    # ===========================
    if request.method == "POST" and "actualizar_cliente" in request.POST:
        id_cliente = request.POST.get("id_cliente")

        if id_cliente:
            try:
                cliente = Clientes.objects.using("cliente").get(id=id_cliente)
                pedido.cod_cliente = cliente
                pedido.save()
                messages.success(request, "Cliente actualizado correctamente.")
            except Clientes.DoesNotExist:
                messages.error(request, "Cliente no encontrado.")

        return redirect("pedidos:editar_pedido", id_pedido=id_pedido)

    # ===========================
    # 2. Guardar pedido (CREAR)
    # ===========================
    if request.method == "POST" and "guardar_pedido" in request.POST:
        if not pedido.cod_cliente:
            messages.error(request, "Debe seleccionar un cliente antes de guardar el pedido.")
            return redirect("pedidos:editar_pedido", id_pedido=id_pedido)

        if pedido.detalles.count() == 0:
            messages.error(request, "Debe agregar al menos un ítem al pedido.")
            return redirect("pedidos:editar_pedido", id_pedido=id_pedido)

        pedido.estado = "CREADO"
        pedido.save()

        messages.success(request, f"Pedido {pedido.id} guardado correctamente.")
        return redirect("pedidos:listar_pedidos")

    # ===========================
    # 3. Cancelar pedido (BORRADOR)
    # ===========================
    if request.method == "POST" and "cancelar_pedido" in request.POST:
        if pedido.estado == "BORRADOR":
            pedido.detalles.all().delete()
            pedido.delete()
            messages.info(request, "Pedido cancelado.")
            return redirect("pedidos:listar_pedidos")
        else:
            messages.error(request, "No es posible cancelar un pedido ya creado.")

    # ===========================
    # 4. Eliminar un ítem
    # ===========================
    if request.method == "POST" and "eliminar_item" in request.POST:
        id_item = request.POST.get("eliminar_item")
        DetallePedido.objects.filter(id=id_item).delete()
        return redirect("pedidos:editar_pedido", id_pedido=id_pedido)

    # ===========================
    # 5. Asignar un cliente
    # ===========================
    # Asignar cliente
    if request.method == "POST" and "asignar_cliente" in request.POST:
        raw_id = request.POST.get("id_cliente", "").strip()

        try:
            id_cliente = int(raw_id)
            if id_cliente <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, "ID de cliente inválido.")
            return redirect("pedidos:editar_pedido", id_pedido=id_pedido)

        try:
            cliente = Clientes.objects.using("cliente").get(pk=id_cliente)
        except Clientes.DoesNotExist:
            messages.error(request, "Cliente no encontrado en base legacy.")
            return redirect("pedidos:editar_pedido", id_pedido=id_pedido)

        pedido.cod_cliente = id_cliente
        pedido.save()
        messages.success(request, "Cliente asignado correctamente.")
        return redirect("pedidos:editar_pedido", id_pedido=id_pedido)

    context = {
        "pedido": pedido,
        "detalles": detalles,
    }
    return render(request, "pedidos/editar_pedido.html", context)

    # ===========================
    # 6. Renderizar template
    # ===========================
    contexto = {
        "pedido": pedido,
        "detalles": pedido.detalles.all(),
    }

    return render(request, "pedidos/editar_pedido.html", contexto)




@login_required
def listar_pedidos(request):
    pedidos = Pedido.objects.all().order_by("-fecha")
    return render(request, "pedidos/listar_pedidos.html", {"pedidos": pedidos})

@property
def cliente(self):
    if self.cod_cliente:
        try:
            return Clientes.objects.using("cliente").get(pk=self.cod_cliente)
        except:
            return None
    return None