const api = document.getElementById("api-urls").dataset;

function qs(id){ return document.getElementById(id); }

function show(id){
    qs(id).classList.remove("d-none");
}

function hide(id){
    qs(id).classList.add("d-none");
}

function setHTML(id, html){
    qs(id).innerHTML = html;
}

function getCSRFToken() {
    return document.querySelector(
        "#csrf-form input[name=csrfmiddlewaretoken]"
    ).value;
}

let equipoIdMateNS = null;

// =====================================================
// RESET
// =====================================================

function resetWorkflow() {

    equipoIdMateNS = null;

    setHTML("ns_input", "");
    setHTML("ns_resultado", "");
    setHTML("ns_garantia_info", "");
    setHTML("ns_equipo_nombre", "");

    setHTML("equipo_input", "");
    setHTML("equipo_resultados", "");

    setHTML("desc_input", "");
    setHTML("desc_resultados", "");

    hide("btn_bom_ns");

    hide("zona_lista_materiales");
    setHTML("lista_materiales", "");
}

// =====================================================
// MODOS
// =====================================================

document.querySelectorAll(".modo-radio").forEach(radio=>{

    radio.addEventListener("change", ()=>{

        resetWorkflow();

        hide("zona_ns");
        hide("zona_equipo");
        hide("zona_desc");
        hide("zona_lista_materiales");

        if(radio.value==="ns") show("zona_ns");
        if(radio.value==="equipo") show("zona_equipo");
        if(radio.value==="desc") show("zona_desc");

    });

});

// =====================================================
// MODO NS
// =====================================================

qs("btn_consultar_ns").addEventListener("click", async ()=>{

    equipoIdMateNS = null;

    hide("btn_bom_ns");

    setHTML("ns_resultado","Consultando...");

    const ns = qs("ns_input").value.trim();

    const r = await fetch(
        api.apiConsultarNs
        + "?ns="
        + encodeURIComponent(ns)
    );

    const data = await r.json();

    if(!data.ok){
        setHTML("ns_resultado", data.error);
        return;
    }

    if(!data.existe){

        setHTML("ns_resultado", "Inexistente");
        setHTML("ns_garantia_info", "");

        return;
    }

    equipoIdMateNS = data.equipo_id_mate;

    setHTML("ns_equipo_nombre", data.equipo_nombre);

    if(data.garantia==="EN_GARANTIA"){
        setHTML("ns_resultado", "En garantía");
    } else {
        setHTML("ns_resultado", "Fuera de garantía");
    }

    setHTML(
        "ns_garantia_info",
        "Liberación: "
        + data.fecha_liberacion
        + " — Fin garantía: "
        + data.fin_garantia
    );

    show("btn_bom_ns");

});

qs("btn_bom_ns").addEventListener("click", ()=>{

    if(equipoIdMateNS){
        cargarListaMateriales(equipoIdMateNS, true);
    }

});

// =====================================================
// MODO EQUIPO
// =====================================================

let equipoTimer=null;

qs("equipo_input").addEventListener("input", ()=>{

    clearTimeout(equipoTimer);

    equipoTimer=setTimeout(buscarEquipos, 300);

});

qs("chk_equipo_obsoletos")
.addEventListener("change", buscarEquipos);

async function buscarEquipos(){

    const q = qs("equipo_input").value.trim();

    const verObs =
        qs("chk_equipo_obsoletos").checked
            ? "1"
            : "0";

    if(!q){
        setHTML("equipo_resultados","");
        return;
    }

    const r = await fetch(
        api.apiBuscarEquipos
        + "?q="
        + encodeURIComponent(q)
        + "&ver_obsoletos="
        + verObs
    );

    const data = await r.json();

    if(!data.ok){

        setHTML("equipo_resultados", data.error);

        return;
    }

    if(data.equipos.length===0){

        setHTML(
            "equipo_resultados",
            "<div class='text-muted'>Sin resultados</div>"
        );

        return;
    }

    let html = "<ul class='list-group'>";

    data.equipos.forEach(e=>{

        html += `
        <li class="list-group-item d-flex justify-content-between align-items-center">

            <a href="#"
                data-id="${e.id_mate}"
                class="link-equipo">

                ${e.valor}

            </a>

            ${
                e.obsoleto==1
                    ? "<span class='badge bg-warning text-dark'>Obsoleto</span>"
                    : ""
            }

        </li>`;
    });

    html += "</ul>";

    setHTML("equipo_resultados", html);

    document.querySelectorAll(".link-equipo").forEach(a=>{

        a.addEventListener("click",(ev)=>{

            ev.preventDefault();

            cargarListaMateriales(a.dataset.id, false);

        });

    });

}

// =====================================================
// MODO DESCRIPCIÓN
// =====================================================

hide("zona_lista_materiales");

let descTimer=null;

qs("desc_input").addEventListener("input", ()=>{

    clearTimeout(descTimer);

    descTimer=setTimeout(buscarMaterialesLibres, 300);

});

qs("grupo_select")
.addEventListener("change", buscarMaterialesLibres);

qs("chk_desc_obsoletos")
.addEventListener("change", buscarMaterialesLibres);

// =====================================================
// CARGAR GRUPOS
// =====================================================

(async function cargarGrupos(){

    const r = await fetch(
        api.apiGrupos,
        {cache:"no-store"}
    ).catch(()=>null);

    if(!r) return;

    const data = await r.json();

    if(!data.ok) return;

    data.grupos.forEach(g=>{

        const opt=document.createElement("option");

        opt.value=g;
        opt.textContent=g;

        qs("grupo_select").appendChild(opt);

    });

})();

// =====================================================
// BUSCAR MATERIALES
// =====================================================

async function buscarMaterialesLibres(){

    const texto = qs("desc_input").value.trim();

    const grupo = qs("grupo_select").value;

    const verObs =
        qs("chk_desc_obsoletos").checked
            ? "1"
            : "0";

    if(!texto && grupo==="---"){

        setHTML("desc_resultados","");

        return;
    }

    const url =
        api.apiBuscarMateriales
        + "?texto="
        + encodeURIComponent(texto)
        + "&grupo="
        + encodeURIComponent(grupo)
        + "&ver_obsoletos="
        + verObs;

    const r = await fetch(url);

    const data = await r.json();

    if(!data.ok){

        setHTML("desc_resultados", data.error);

        return;
    }

    if(data.materiales.length===0){

        setHTML(
            "desc_resultados",
            "<div class='text-muted'>Sin resultados</div>"
        );

        return;
    }

    let html = `
    <table class="table table-striped table-bordered">

    <thead>
    <tr>
        <th>ID</th>
        <th>Descripción</th>
        <th>Grupo</th>
        <th style="width:120px">Cantidad</th>
        <th></th>
    </tr>
    </thead>

    <tbody>
    `;

    data.materiales.forEach(m=>{

        html += `
        <tr>
            <td>${m.id_mate}</td>
            <td>${m.valor}</td>
            <td>${m.grupo}</td>
            <td>
            <input 
                type="text"
                inputmode="decimal"
                value="1"
                class="form-control text-center qty"
                data-id="${m.id_mate}">
            </td>

            <td class="text-center">
            <button
                type="button"
                class="btn btn-success btn-sm agregar-link btn-touch"
                data-id="${m.id_mate}">
                <i class="bi bi-plus-circle fs-4"></i>
            </button>
            </td>
        </tr>
        `;
    });

    html += "</tbody></table>";

    setHTML("desc_resultados", html);

}

// =====================================================
// LISTA DE MATERIALES
// =====================================================

async function cargarListaMateriales(
    equipoIdMate,
    desdeNS
){

    const r = await fetch(
        api.apiListaMateriales
        + "?equipo_id_mate="
        + equipoIdMate
    );

    const data = await r.json();

    if(!data.ok){

        alert(data.error);

        return;
    }

    const titulo =
        desdeNS
            ? "Lista de materiales (por NS)"
            : "Lista de materiales del equipo";

    renderListaMateriales(data.materiales, titulo);

}

function renderListaMateriales(materiales, titulo){

    show("zona_lista_materiales");

    setHTML("lista_titulo", titulo);

    let html = `
    <table class="table table-striped table-bordered">
        <thead>
            <tr>
                <th>ID</th>
                <th>Descripción</th>
                <th>Grupo</th>
                <th style="width:120px">Cantidad</th>
                <th></th>
            </tr>
        </thead>
    <tbody>
    `;

    materiales.forEach(m=>{

        html += `
        <tr>
            <td>${m.id_mate}</td>
            <td>${m.valor}</td>
            <td>${m.grupo || ""}</td>
            <td>
                <input 
                    type="text"
                    inputmode="decimal"
                    value="1"
                    class="form-control text-center qty"
                    data-id="${m.id_mate}">            
            </td>
            <td class="text-center">
                <button
                    type="button"
                    class="btn btn-success btn-sm agregar-link btn-touch"
                    data-id="${m.id_mate}">
                    <i class="bi bi-plus-circle fs-4"></i>
                </button>
            </td>
        </tr>
        `;
    });

    html += "</tbody></table>";

    setHTML("lista_materiales", html);

}

// =====================================================
// EVENT DELEGATION
// =====================================================

document.addEventListener("click", function(ev) {

    const btn = ev.target.closest(".agregar-link");

    if (!btn) return;

    agregarItem(ev);

});

// =====================================================
// AGREGAR ITEM
// =====================================================

async function agregarItem(ev){

    ev.preventDefault();

    const btn =
        ev.target.closest(".agregar-link");

    const idMate =
        btn.dataset.id;

    const qtyInput =
        document.querySelector(
            `.qty[data-id="${idMate}"]`
        );

    const cantidad = qtyInput.value;

    let numeroSerie = null;

    if (equipoIdMateNS) {

        numeroSerie =
            qs("ns_input").value.trim();

    }

    const formData = new FormData();

    formData.append("pedido_id", pedidoId);

    formData.append("id_mate", idMate);

    formData.append("cantidad", cantidad);

    if (numeroSerie){

        formData.append(
            "numero_serie",
            numeroSerie
        );
    }

    formData.append(
        "csrfmiddlewaretoken",
        getCSRFToken()
    );

    const r = await fetch(
        api.apiAgregarItem,
        {
            method:"POST",
            body: formData
        }
    );

    const data = await r.json();

    if(!data.ok){

        alert(data.error);

        return;
    }

    let msg =
        `ID ${data.id_mate} agregado. `
        + `Total: ${data.cantidad_total}`;

    if (data.numero_serie) {

        msg += ` — NS: ${data.numero_serie}`;

    }
    mostrarToast(msg);


}

