document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll(".cantidad-control").forEach(control => {

        const input = control.querySelector(".cantidad-input");
        const btnMas = control.querySelector(".cantidad-mas");
        const btnMenos = control.querySelector(".cantidad-menos");

        btnMas?.addEventListener("click", () => {

            const max = parseFloat(
                (input.dataset.max || "999999").replace(",", ".")
            );

            let valor = parseFloat(
                (input.value || "0").replace(",", ".")
            ) || 0;

            if (valor < max) {
                input.value = valor + 1;
            }
        });

        btnMenos?.addEventListener("click", () => {

            const min = parseFloat(
                (input.min || "0").replace(",", ".")
            );

            let valor = parseFloat(
                (input.value || "0").replace(",", ".")
            ) || 0;

            if (valor > min) {
                input.value = valor - 1;
            }
        });

        // Normaliza coma decimal al salir del campo

        input?.addEventListener("change", () => {

            input.value = input.value.replace(",", ".");

        });

    });
});