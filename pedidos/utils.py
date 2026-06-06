from reportlab.platypus import Image
import os
from django.conf import settings

import io

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch


def build_pdf_preliminar(pedido):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer)

    elements = []

    styles = getSampleStyleSheet()

    # -----------------------------------------
    # LOGO
    # -----------------------------------------
    logo_path = os.path.join(
        settings.BASE_DIR,"static","images","favicon.png"
    )

    if os.path.exists(logo_path):

        logo = Image(logo_path)

        logo.drawHeight = 0.23 * inch
        logo.drawWidth = 0.45 * inch

        tabla_titulo = Table([
            [
                logo,
                Paragraph(
                    f"COMPROBANTE PRELIMINAR - Pedido Nº{pedido.id}",
                    styles["Heading1"]
                )
            ]
        ], colWidths=[40, 390])

        tabla_titulo.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))

        elements.append(tabla_titulo)

    else:

        elements.append(
            Paragraph(
                f"COMPROBANTE PRELIMINAR - Pedido Nº{pedido.id}",
                styles["Heading1"]
            )
        )

    elements.append(Spacer(1, 0.2 * inch))

    # -----------------------------------------
    # DATOS PEDIDO
    # -----------------------------------------
    cliente = str(pedido.cliente) if pedido.cliente else "Sin cliente"

    encabezado = [
        ["Cliente", cliente],
        ["Estado", pedido.estado],
        ["Fecha", pedido.fecha.strftime("%d/%m/%Y %H:%M")],
    ]

    tabla_encabezado = Table(encabezado, colWidths=[70, 360])

    tabla_encabezado.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (0,-1), colors.lightgrey),
    ]))

    elements.append(tabla_encabezado)

    elements.append(Spacer(1, 0.3 * inch))

    # -----------------------------------------
    # ITEMS
    # -----------------------------------------
    data = [
        [
            "ID",
            "Descripción",
            "Cant.",
            "Precio",
            "Subtotal"
        ]
    ]

    total = 0

    for d in pedido.detalles.all():

        try:
            precio = float(d.material.precio)
        except Exception:
            precio = 0

        subtotal = precio * float(d.cantidad)

        total += subtotal

        data.append([
            str(d.cod_repuesto),
            d.material.valor,
            f"{d.cantidad:.3f}".rstrip("0").rstrip("."),
            f"${precio:,.2f}",
            f"${subtotal:,.2f}",
        ])

    data.append([
        "",
        "",
        "",
        "TOTAL",
        f"${total:,.2f}"
    ])

    tabla = Table(
        data,
        colWidths=[50, 200, 50, 60, 70]
    )

    tabla.setStyle(TableStyle([
        ("ALIGN", (0,0), (-1,0), "CENTER"),

        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),

        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),

        ("ALIGN", (0,0), (0,-1), "CENTER"),

        ("ALIGN", (2,1), (2,-1), "CENTER"),
        
        ("ALIGN", (3,1), (4,-1), "RIGHT"),

        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),

        ("FONTNAME", (3,-1), (4,-1), "Helvetica-Bold"),

    ]))

    elements.append(tabla)

    elements.append(Spacer(1, 0.3 * inch))

    elements.append(
        Paragraph(
            "Documento preliminar no fiscal.",
            styles["Italic"]
        )
    )

    doc.build(elements)

    buffer.seek(0)

    return buffer.getvalue()

#Me va a indicar si se está accediendo desde un dispositivo movil.
def es_movil(request):
    user_agent = request.META.get("HTTP_USER_AGENT", "").lower()

    return any(x in user_agent for x in (
        "android",
        "iphone",
        "ipad",
        "mobile"
    ))