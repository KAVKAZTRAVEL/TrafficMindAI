from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def font_name() -> str:
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    if font_path.exists():
        pdfmetrics.registerFont(TTFont("DejaVuSans", str(font_path)))
        return "DejaVuSans"
    return "Helvetica"


def generate_pdf_report(path: str, title: str, summary: str, recommendations: list[str]) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    font = font_name()
    pdf = canvas.Canvas(str(output), pagesize=A4)
    width, height = A4
    pdf.setFont(font, 18)
    pdf.drawString(48, height - 64, title)
    pdf.setFont(font, 11)
    y = height - 100
    for line in [summary, "", "Recommendations:"] + [f"- {item}" for item in recommendations]:
        pdf.drawString(48, y, line[:110])
        y -= 18
    pdf.save()
    return str(output)
