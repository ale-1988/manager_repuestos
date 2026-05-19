function ordenar(campo) {

    const ordenInput = document.getElementById("orden");
    const dirInput = document.getElementById("dir");

    const ordenActual = ordenInput.value;
    const dirActual = dirInput.value;

    ordenInput.value = campo;

    if (ordenActual === campo) {

        dirInput.value =
            (dirActual === "asc") ? "desc" : "asc";

    } else {

        dirInput.value = "asc";

    }

    actualizarBusqueda();
}


function actualizarBusqueda() {

    const texto = document.getElementById("texto").value;
    const grupo = document.getElementById("grupo").value;
    const mostrar = document.getElementById("mostrar_obsoletos").checked
            ? "on"
            : "";

    const orden = document.getElementById("orden").value;
    const dir = document.getElementById("dir").value;

    const params =
        `?texto=${encodeURIComponent(texto)}`
        + `&grupo=${encodeURIComponent(grupo)}`
        + `&mostrar_obsoletos=${mostrar}`
        + `&orden=${orden}`
        + `&dir=${dir}`;

    fetch(params, {
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        }
    })
    .then(response => response.text())
    .then(html => {

        document.querySelector("#resultados").outerHTML =
            html;

    })
    .catch(error => {

        console.error(
            "Error actualizando búsqueda:",
            error
        );

    });
}
```
