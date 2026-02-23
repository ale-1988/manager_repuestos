import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch


def build_pdf_factura(factura):
    """
    Genera el PDF de una factura y devuelve los bytes.
    No genera HttpResponse.
    """

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []

    styles = getSampleStyleSheet()

    elements.append(
        Paragraph(f"{factura.tipo} Nº {factura.numero}", styles["Heading1"])
    )
    elements.append(Spacer(1, 0.3 * inch))

    data = [
        ["Cliente", str(factura.cliente)],
        ["Estado", factura.estado],
        ["Importe Total", f"${factura.importe_total}"],
        ["Total Pagado", f"${factura.total_pagado()}"],
        ["Total Notas Crédito", f"${factura.total_notas_credito()}"],
        ["Saldo", f"${factura.saldo_actual()}"],
    ]

    table = Table(data)
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)

    doc.build(elements)

    buffer.seek(0)
    return buffer.getvalue()
