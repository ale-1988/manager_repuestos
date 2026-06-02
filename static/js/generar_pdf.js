function generarPDF(baseUrl) {
    window.open(baseUrl, "_blank");
}

function confirmarEnvioFactura(url) {
    if (confirm("¿Enviar esta factura por email?")) {
        window.location.href = url;
    }
}