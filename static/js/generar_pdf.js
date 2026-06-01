function generarPDF(baseUrl, checkboxId="chkEmail") {

    let url = baseUrl;

    let chk = document.getElementById(checkboxId);

    if (chk && chk.checked) {
        url += "?email=1";
    }

    window.open(url, "_blank");
}