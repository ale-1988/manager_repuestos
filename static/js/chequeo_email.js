document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll(".btn-email").forEach(btn => {

        btn.addEventListener("click", function () {

            // Evita múltiples clics
            if (this.dataset.enviando === "1") {
                return;
            }

            this.dataset.enviando = "1";

            // Guarda icono original
            this.dataset.htmlOriginal = this.innerHTML;

            // Deshabilita botón
            this.disabled = true;

            // Spinner
            this.innerHTML = `
                <span class="spinner-border spinner-border-sm"
                      role="status"
                      aria-hidden="true"></span>
            `;

            // Navega a la URL
            window.location.href = this.dataset.url;
        });

    });

});