
function getCSRFToken() {

    return document.querySelector(
        "#csrf-form input[name=csrfmiddlewaretoken]"
    ).value;

}

// =====================================================
// MODIFICAR CANTIDAD (+ / -)
// =====================================================

document.addEventListener("click", async function(ev) {

    if (!(ev.target instanceof Element)) return;

    const btnCantidad =
        ev.target.closest(".btn-cantidad");

    if (!btnCantidad) return;

    const url =
        btnCantidad.dataset.url;

    const accion =
        btnCantidad.dataset.accion;

    const formData = new FormData();

    formData.append("accion", accion);

    formData.append(
        "csrfmiddlewaretoken",
        getCSRFToken()
    );

    const r = await fetch(url, {
        method: "POST",
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        },
        body: formData
    });

    const data = await r.json();

    

    if (!data.ok) {
        alert(data.error || "Error");
        return;
    }

    const input = document.querySelector(`.cantidad-input[data-detalle-id="${data.detalle_id}"]`);
    
    if (input) {
        input.value =
            parseFloat(data.cantidad).toString();
    }
    
});

// =====================================================
// ELIMINAR ITEM
// =====================================================

document.addEventListener("click", async function(ev) {

    if (!(ev.target instanceof Element)) return;

    const btnEliminar =
        ev.target.closest(".btn-eliminar");

    if (!btnEliminar) return;

    if (!confirm("¿Eliminar ítem del pedido?")) {
        return;
    }

    const url =
        btnEliminar.dataset.url;

    const formData = new FormData();

    formData.append("accion", "eliminar");

    formData.append(
        "csrfmiddlewaretoken",
        getCSRFToken()
    );

    const r = await fetch(url, {
        method: "POST",
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        },
        body: formData
    });

    const data = await r.json();

    if (!data.ok) {
        alert(data.error || "Error");
        return;
    }

    const fila =
        document.getElementById(
            `fila-item-${data.detalle_id}`
        );

    if (fila) {
        fila.remove();
    }

});

// =====================================================
// EDICIÓN MANUAL DE CANTIDAD
// =====================data-max="999999"================================

document.addEventListener("focusout", async function(ev) {

    const target = ev.target;

    if (!target || typeof target.closest !== "function") {
        return;
    }

    const input =
        target.closest(".cantidad-input");

    if (!input) return;

    const valor = input.value.trim();
    const fila = input.closest("tr");
    const btn = fila.querySelector(".btn-cantidad");

    if (!btn) return;

    const url = btn.dataset.url;
    const formData = new FormData();
    formData.append("accion", "setear");
    formData.append("cantidad", valor);
    formData.append(
        "csrfmiddlewaretoken",
        getCSRFToken()
    );

    const r = await fetch(url, {
        method: "POST",
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        },
        body: formData
    });

    const data = await r.json();

    if (!data.ok) {

        alert(data.error || "Error");

        return;
    }

    input.value = parseFloat(data.cantidad).toString();
 
}, true);

// =====================================================
// ENTER = PERDER FOCO
// =====================================================

document.addEventListener("keydown", function(ev) {

    if (!(ev.target instanceof Element)) return;

    const input =
        ev.target.closest(".cantidad-input");

    if (!input) return;

    if (ev.key === "Enter") {

        ev.preventDefault();

        input.blur();

    }

});
// =====================================================
// MOSTRAR O NO ICONO DIVIDIR
// =====================================================
document.addEventListener("DOMContentLoaded", () => {

    const checkboxes = document.querySelectorAll(
        'input[name="item_dividir"]'
    );

    const btnDividir = document.getElementById(
        "btn-dividir-confirmar"
    );
    if (!btnDividir || checkboxes.length === 0) {
        return;
    }

    function actualizarBotonDividir() {

        const total = checkboxes.length;

        const seleccionados = Array.from(checkboxes)
            .filter(cb => cb.checked)
            .length;

        const visible =
            seleccionados > 0 &&
            seleccionados < total;

        btnDividir.classList.toggle("d-none", !visible);
    }

    checkboxes.forEach(cb => {
        cb.addEventListener("change", actualizarBotonDividir);
    });

    actualizarBotonDividir();
});