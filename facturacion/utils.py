def fmt_cantidad(valor):
    return f"{valor:f}".rstrip("0").rstrip(".")


def build_pdf_factura(factura):
    """
    Genera el PDF de una factura y devuelve los bytes.
    """

    def add_metadata(canvas, doc):
        canvas.setTitle(f"Factura {factura.numero}")
        canvas.setAuthor(settings.EMPRESA_NOMBRE)
        canvas.setSubject("Factura")
        canvas.setCreator("Manager de Repuestos")


    import io

    from django.conf import settings
    from pathlib import Path
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        Image,
    )

    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.units import mm
    from reportlab.lib import enums

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )
    ANCHO_TOTAL = 540
    styles = getSampleStyleSheet()

    style_centro = styles["BodyText"].clone("centro")
    style_centro.alignment = TA_CENTER

    style_derecha = styles["BodyText"].clone("derecha")
    style_derecha.alignment = TA_RIGHT

    style_titulo = styles["Heading1"].clone("titulo")
    style_titulo.alignment = TA_CENTER

    elements = []

    cliente = factura.cliente

    logo_widget = ""

    if Path(settings.EMPRESA_LOGO).exists():

        logo_widget = Image(
            str(settings.EMPRESA_LOGO),
            width=36 * mm,
            height=18 * mm,
        )

        columna_empresa = Table(
            [
                [logo_widget],
                [Paragraph(
                    f"""
                    <b>{settings.EMPRESA_NOMBRE}</b><br/>
                    {settings.EMPRESA_DIRECCION}
                    """,
                    styles["BodyText"],
                )]
            ]
        )

        columna_empresa.setStyle(
            TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ])
        )

    else:

        columna_empresa = Paragraph(
            f"""
            <b>{settings.EMPRESA_NOMBRE}</b><br/>
            {settings.EMPRESA_DIRECCION}
            """,
            styles["BodyText"],
        )

    # ==========================================================
    # ENCABEZADO
    # ==========================================================

    encabezado = Table(
        [
            [
                columna_empresa,

                Paragraph(
                    "<b>FACTURA</b>",
                    style_titulo,
                ),

                Paragraph(
                    f"""
                    <b>Factura N°:</b> {factura.numero}<br/>
                    <b>Fecha:</b> {factura.fecha_emision.strftime("%d/%m/%Y")}<br/>
                    <b>CUIT:</b> {settings.EMPRESA_CUIT}<br/>
                    <b>Ing. Brutos:</b> {settings.EMPRESA_INGRESOS_BRUTOS}<br/>
                    <b>Inicio Activ.:</b> {settings.EMPRESA_INICIO_ACTIVIDADES}
                    """,
                    styles["BodyText"],
                ),
            ]
        ],
        colWidths=[140, 260, 140],
    )

    encabezado.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    elements.append(encabezado)
    elements.append(Spacer(1, 10))

    # ==========================================================
    # CLIENTE + TOTAL
    # ==========================================================

    bloque_cliente = Table(
        [
            [
                Paragraph(
                    f"""
                    <b>Cliente:</b> {cliente.nombre}<br/>
                    <b>CUIT:</b> {cliente.cuit}<br/>
                    <b>Domicilio:</b> {cliente.domicilio}<br/>
                    <b>Ciudad:</b> {cliente.ciudad}<br/>
                    <b>Provincia:</b> {cliente.provincia}
                    """,
                    styles["BodyText"],
                ),

                Paragraph(
                    f"""
                    <para align="center">
                    <b>TOTAL A PAGAR</b><br/><br/>
                    <font size="16">
                    $ {factura.importe_total:,.2f}
                    </font>
                    </para>
                    """,
                    styles["BodyText"],
                ),
            ]
        ],
        colWidths=[360, 180],
    )

    bloque_cliente.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    elements.append(bloque_cliente)
    elements.append(Spacer(1, 10))

    # ==========================================================
    # ITEMS
    # ==========================================================

    data_items = [
        [
            "ID",
            "Cant.",
            "Denominación",
            "P. Unitario",
            "Importe",
        ]
    ]

    subtotal = 0

    for detalle in factura.pedido.detalles.all():

        material = detalle.material

        precio = material.precio
        importe = detalle.cantidad * precio

        subtotal += importe

        data_items.append(
            [
                str(detalle.cod_repuesto),
                fmt_cantidad(detalle.cantidad),
                material.valor,
                f"$ {precio:,.2f}",
                f"$ {importe:,.2f}",
            ]
        )

    tabla_items = Table(
        data_items,
        colWidths=[50, 50, 270, 80, 90],
        repeatRows=1,
    )

    tabla_items.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

                # ID
                ("ALIGN", (0, 1), (0, -1), "CENTER"),

                # Cantidad
                ("ALIGN", (1, 1), (1, -1), "CENTER"),

                # Denominación
                ("ALIGN", (2, 1), (2, -1), "LEFT"),

                # Precios
                ("ALIGN", (3, 1), (4, -1), "CENTER"),

                # Encabezados
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),

                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(tabla_items)
    elements.append(Spacer(1, 10))

    # ==========================================================
    # TOTALES
    # ==========================================================

    tabla_totales = Table(
        [
            ["Subtotal", f"$ {subtotal:,.2f}"],
            ["Pagado", f"$ {factura.total_pagado():,.2f}"],
            ["Saldo", f"$ {factura.saldo_actual():,.2f}"],
        ],
        colWidths=[100, 100],
    )

    tabla_totales.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ]
        )
    )

    tabla_contenedor = Table(
        [["", tabla_totales]],
        colWidths=[280, 200],
    )

    elements.append(tabla_contenedor)

    # ==========================================================
    # OBSERVACIONES
    # ==========================================================

    if factura.observaciones:
        elements.append(Spacer(1, 10))

        elements.append(
            Paragraph(
                f"<b>Observaciones:</b><br/>{factura.observaciones}",
                styles["BodyText"],
            )
        )

    doc.build(elements,
                onFirstPage=add_metadata,
                onLaterPages=add_metadata,
                )

    buffer.seek(0)

    return buffer.getvalue()