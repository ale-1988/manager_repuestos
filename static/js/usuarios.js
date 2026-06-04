// =====================================================
// ELIMINAR USUARIO
// =====================================================

document.addEventListener("click", async function(ev) {

    if (!(ev.target instanceof Element)) return;

    const btn =
        ev.target.closest(".btn-eliminar-usuario");

    if (!btn) return;

    ev.preventDefault();

    const ok =
        await confirmar(
            "¿Eliminar usuario?"
        );

    if (!ok) {
        return;
    }

    const form =
        document.createElement("form");

    form.method = "POST";
    form.action = btn.href;

    const csrf =
        document.createElement("input");

    csrf.type = "hidden";
    csrf.name = "csrfmiddlewaretoken";
    csrf.value = getCSRFToken();

    form.appendChild(csrf);

    document.body.appendChild(form);

    form.submit();

});