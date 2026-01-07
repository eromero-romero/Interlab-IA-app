from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def text_to_pdf_bytes(title: str, body: str) -> bytes:
    """
    Convierte texto (markdown simple) a un PDF básico.
    (No renderiza markdown complejo, pero queda limpio y profesional.)
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    width, height = letter
    x = 0.9 * inch
    y = height - 1.0 * inch

    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, title)
    y -= 0.35 * inch

    c.setFont("Helvetica", 10)

    # Limpieza mínima para PDF (quita algunos markdown)
    clean = body.replace("**", "").replace("🟢", "[OK]").replace("🟡", "[OBS]").replace("🔴", "[ALERTA]")
    lines = []
    for raw_line in clean.splitlines():
        line = raw_line.strip()
        if not line:
            lines.append("")
        else:
            # corta líneas muy largas
            while len(line) > 110:
                lines.append(line[:110])
                line = line[110:]
            lines.append(line)

    for line in lines:
        if y < 0.8 * inch:
            c.showPage()
            y = height - 1.0 * inch
            c.setFont("Helvetica", 10)

        c.drawString(x, y, line)
        y -= 0.18 * inch

    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
