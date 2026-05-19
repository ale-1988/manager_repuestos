
function getCSRFToken() {

    return document.querySelector(
        "#csrf-form input[name=csrfmiddlewaretoken]"
    ).value;

}

// =====================================================
// MODIFICAR CANTIDAD
// =====================================================

document.addEventListener("click", async function(ev) {

    // ---------------------------------------------
    // BOTÓN + / -
    // ---------------------------------------------

    const btnCantidad =
        ev.target.closest(".btn-cantidad");

    if (btnCantidad) {

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

        
        const input =document.querySelector(
            `.cantidad-input[data-detalle-id="${data.detalle_id}"]`
        );

        if (input) {
            input.value = parseFloat(data.cantidad).toString();
        }
        return;
    }

    // ---------------------------------------------
    // ELIMINAR
    // ---------------------------------------------

    const btnEliminar =
        ev.target.closest(".btn-eliminar");

    if (btnEliminar) {

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

    }


    // =====================================================
    // EDICIÓN MANUAL DE CANTIDAD
    // =====================================================

    document.addEventListener("blur", async function(ev) {

        const input =
            ev.target.closest(".cantidad-input");

        if (!input) return;

        const detalleId =
            input.dataset.detalleId;

        const valor =
            input.value.trim();

        const fila =
            input.closest("tr");

        const btn =
            fila.querySelector(".btn-cantidad");

        if (!btn) return;

        const url =
            btn.dataset.url;

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

        input.value =
            parseFloat(data.cantidad)
                .toString();

    }, true);

    // =====================================================
    // ENTER = PERDER FOCO
    // =====================================================

    document.addEventListener("keydown", function(ev) {

        const input =
            ev.target.closest(".cantidad-input");

        if (!input) return;

        if (ev.key === "Enter") {

            ev.preventDefault();

            input.blur();

        }

    });
});

