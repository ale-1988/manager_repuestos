function getCSRFToken() {
    return document.querySelector(
        "#csrf-form input[name=csrfmiddlewaretoken]"
    ).value;
}

function mostrarToast(mensaje) {

    document.getElementById("toastTexto").innerText =
        mensaje;

    const toast =
        new bootstrap.Toast(
            document.getElementById("toastExito"),
            {
                delay: 4000
            }
        );

    toast.show();
}

function confirmar(mensaje) {

    return new Promise((resolve) => {

        document.getElementById(
            "modalConfirmacionTexto"
        ).innerText = mensaje;

        const modalEl =
            document.getElementById(
                "modalConfirmacion"
            );

        const modal =
            new bootstrap.Modal(modalEl);

        const btnConfirmar =
            document.getElementById(
                "btnConfirmarModal"
            );

        const confirmarClick = () => {
            btnConfirmar.removeEventListener(
                "click",
                confirmarClick
            );

            modal.hide();
            resolve(true);
        };

        btnConfirmar.addEventListener(
            "click",
            confirmarClick
        );

        modalEl.addEventListener(
            "hidden.bs.modal",
            () => resolve(false),
            { once: true }
        );

        modal.show();
    });
}