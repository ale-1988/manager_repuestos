function generarPDF(baseUrl) {
    window.open(baseUrl, "_blank");
}

async function confirmarEnvioFactura(url) {

    const ok =
        await confirmar(
            "¿Enviar esta factura por email?"
        );

    if (!ok) {
        return;
    }

    window.location.href = url;
}