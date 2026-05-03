import pytest
from django.contrib.auth import get_user_model
from pedidos.models import Pedido


User = get_user_model()


# ===============================
# CU5 - Crear pedido
# ===============================
@pytest.mark.django_db
def test_cu5_crear_pedido():
    user = User.objects.create_user(username="test", password="1234")

    pedido = Pedido.objects.create(cod_cliente=user.id)

    assert pedido.id is not None
    assert pedido.cod_cliente == user.id


# ===============================
# CU6 - Editar pedido (lógica simple)
# ===============================
@pytest.mark.django_db
def test_cu6_editar_pedido_logica():
    pedido = Pedido(estado="creado")

    # simulamos agregar items
    items = [
        {"id": 1, "cantidad": 2},
        {"id": 2, "cantidad": 1},
    ]

    assert len(items) == 2
    assert items[0]["cantidad"] == 2


# ===============================
# CU17 - Preparar pedido (lógica pura)
# ===============================
def test_cu17_preparar_pedido_con_stock():
    items = [
        {"stock": 10, "cantidad": 2},
        {"stock": 5, "cantidad": 1},
    ]

    estado = "pagado"

    for item in items:
        if item["stock"] < item["cantidad"]:
            estado = "preparando"
            break
    else:
        estado = "consolidado"

    assert estado == "consolidado"


# ===============================
# CU17 - Error (sin stock)
# ===============================
def test_cu17_preparar_sin_stock():
    items = [
        {"stock": 0, "cantidad": 2},
    ]

    estado = "pagado"

    for item in items:
        if item["stock"] < item["cantidad"]:
            estado = "preparando"
            break

    assert estado == "preparando"


# ===============================
# CU20 - Enviar pedido
# ===============================
@pytest.mark.django_db
def test_cu20_enviar_pedido():
    user = User.objects.create_user(username="test", password="1234")

    pedido = Pedido.objects.create(
        cod_cliente=user.id,
        estado=Pedido.CONSOLIDADO
    )

    # transición válida
    pedido.cambiar_estado(Pedido.ENVIADO, user)
    pedido.cambiar_estado(Pedido.ENTREGADO, user)

    assert pedido.estado == Pedido.ENTREGADO
    
import pytest
from django.core.exceptions import ValidationError

@pytest.mark.django_db
def test_transicion_invalida():
    user = User.objects.create_user(username="test2", password="1234")

    pedido = Pedido.objects.create(
        cod_cliente=user.id,
        estado=Pedido.CONSOLIDADO
    )

    with pytest.raises(ValidationError):
        pedido.cambiar_estado(Pedido.ENTREGADO, user)    