from __future__ import annotations

import io
from pathlib import Path

from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


PAGE = (612, 612)
MARGIN = 36

# Fonte de história (serif amigável). Fallback: Helvetica.
_FONT_REG = "StoryBody"
_FONT_BOLD = "StoryBody-Bold"
_fonts_ready = False


def _register_fonts() -> tuple[str, str]:
    global _fonts_ready
    if _fonts_ready:
        return _FONT_REG, _FONT_BOLD

    windir = Path(r"C:\Windows\Fonts")
    candidates = [
        # Georgia — serif clássica de livro infantil / storytelling
        (windir / "georgia.ttf", windir / "georgiab.ttf"),
        (windir / "Georgia.ttf", windir / "Georgiab.ttf"),
        # Palatino / Book Antiqua
        (windir / "pala.ttf", windir / "palab.ttf"),
        (windir / "BOOKOS.TTF", windir / "BOOKOSB.TTF"),
        # Linux containers
        (Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf")),
        (Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"), Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf")),
    ]
    for reg, bold in candidates:
        if reg.is_file() and bold.is_file():
            pdfmetrics.registerFont(TTFont(_FONT_REG, str(reg)))
            pdfmetrics.registerFont(TTFont(_FONT_BOLD, str(bold)))
            _fonts_ready = True
            return _FONT_REG, _FONT_BOLD

    _fonts_ready = True
    return "Helvetica", "Helvetica-Bold"


def _wrap(c: canvas.Canvas, text: str, font: str, size: float, max_width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if c.stringWidth(test, font, size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def build_pdf(
    *,
    title: str,
    child_name: str,
    cover_image: bytes,
    pages: list[tuple[bytes, str]],
) -> bytes:
    body, bold = _register_fonts()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=PAGE)
    width, height = PAGE

    cover = ImageReader(io.BytesIO(cover_image))
    c.drawImage(cover, 0, 0, width=width, height=height, preserveAspectRatio=True, anchor="c")
    band_h = 120
    c.setFillColorRGB(0.12, 0.18, 0.32)
    c.rect(0, 0, width, band_h, fill=1, stroke=0)
    c.setFillColorRGB(1, 0.96, 0.88)
    c.setFont(bold, 22)
    for i, line in enumerate(_wrap(c, title, bold, 22, width - 2 * MARGIN)[:3]):
        c.drawCentredString(width / 2, 70 - i * 24, line)
    c.setFont(body, 11)
    c.drawCentredString(width / 2, 18, "Story R Us")
    c.showPage()

    for img_bytes, text in pages:
        img = ImageReader(io.BytesIO(img_bytes))
        c.drawImage(img, 0, 0, width=width, height=height, preserveAspectRatio=True, anchor="c")
        text_band = 150
        c.setFillColorRGB(0.98, 0.97, 0.94)
        c.rect(0, 0, width, text_band, fill=1, stroke=0)
        c.setFillColorRGB(0.15, 0.18, 0.25)
        c.setFont(bold, 14)
        lines = _wrap(c, text, bold, 14, width - 2 * MARGIN)
        y = text_band - 28
        for line in lines[:5]:
            c.drawCentredString(width / 2, y, line)
            y -= 18
        c.showPage()

    c.setFillColorRGB(0.95, 0.92, 0.86)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setFillColorRGB(0.15, 0.2, 0.35)
    c.setFont(bold, 20)
    c.drawCentredString(width / 2, height / 2 + 20, f"Feito com carinho para {child_name}")
    c.setFont(body, 12)
    c.drawCentredString(width / 2, height / 2 - 10, "Story R Us")
    c.showPage()

    c.save()
    return buf.getvalue()
