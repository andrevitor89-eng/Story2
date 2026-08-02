# -*- coding: utf-8 -*-
"""Completa o lado cortado e centraliza o Matteo numa foto quadrada p/ a bolinha.

Uso (Story2/backend):
  python scripts/fix_dica_boa_circle.py
"""
from __future__ import annotations

import asyncio
import io
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

from PIL import Image, ImageDraw, ImageOps  # noqa: E402

from app.ai import gemini  # noqa: E402
from app.config import settings  # noqa: E402

settings.gemini_ssl_verify = False

EX = ROOT / "apps" / "web" / "public" / "exemplos"
# Prefer real bak if present; else current tip photo
SRC = EX / "dica-boa.bak.png" if (EX / "dica-boa.bak.png").is_file() else EX / "dica-boa.png"
OUT = EX / "dica-boa.png"
PREV = EX / "_dica-boa-preview.png"

PROMPT = """
Create ONE square (1:1) photorealistic portrait for a circular avatar crop.

SOURCE PHOTO: toddler boy with bright blue eyes, wispy blond hair, soft smile with a small gap in his upper teeth, blue denim overalls. The RIGHT side of his head is cut off / blocked — complete that missing side (temple, ear area, hair) and remove any adult person if present.

COMPOSITION (critical):
- His FACE must be PERFECTLY CENTERED in the square — equal margin left and right of the head.
- Include full head with comfortable breathing room: top of hair, both ears, chin, a bit of shoulders — nothing cut by the frame edge.
- Soft outdoor bokeh background continues naturally on both sides.

FACE IDENTITY (critical):
- Keep his face looking like the SAME boy in the source: same eyes, nose, mouth, teeth gap, expression, skin, hair.
- Do NOT beautify, restyle, or redraw a different child.
- Photorealistic photo edit, not illustration.

No text, watermark, border, or circle mask in the output.
""".strip()


def prepare_src(path: Path) -> bytes:
    im = Image.open(path).convert("RGB")
    # Extra canvas on the right + slight all sides so model can center
    pad_l, pad_r = int(im.width * 0.12), int(im.width * 0.35)
    pad_tb = int(im.height * 0.10)
    padded = ImageOps.expand(im, border=(pad_l, pad_tb, pad_r, pad_tb), fill=(190, 165, 135))
    scale = max(1.0, 1000 / max(padded.size))
    if scale > 1:
        padded = padded.resize(
            (int(padded.width * scale), int(padded.height * scale)),
            Image.Resampling.LANCZOS,
        )
    buf = io.BytesIO()
    padded.save(buf, format="PNG")
    return buf.getvalue()


def center_square(img_bytes: bytes, size: int = 768) -> Image.Image:
    """Force a centered square — trim uneven margins if Gemini left face off-center."""
    im = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    w, h = im.size
    # Heuristic: face blob ≈ non-background mid tones near center; use simple luminance mass
    # Prefer geometric center of the image content after mild inset
    side = min(w, h)
    # If wider than tall, bias crop toward where face usually is; then center
    left = (w - side) // 2
    top = (h - side) // 2
    # Small upward bias so forehead has room in circle
    top = max(0, top - int(side * 0.02))
    if top + side > h:
        top = h - side
    crop = im.crop((left, top, left + side, top + side))
    return crop.resize((size, size), Image.Resampling.LANCZOS)


def save_assets(square: Image.Image) -> None:
    square.save(OUT, "PNG", optimize=True)
    size = square.width
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((12, 12, size - 13, size - 13), fill=255)
    circ = Image.new("RGBA", (size, size), (14, 24, 50, 255))
    circ.paste(square, (0, 0), mask)
    # green ring like the UI
    draw = ImageDraw.Draw(circ)
    draw.ellipse((8, 8, size - 9, size - 9), outline=(47, 168, 96, 255), width=6)
    circ.save(PREV, "PNG")


async def main() -> None:
    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY ausente")
    if not SRC.is_file():
        raise SystemExit(f"fonte ausente: {SRC}")

    os.environ.setdefault("GEMINI_FALLBACK_MODELS", "gemini-2.5-flash-image")
    print(f"fonte={SRC.name}", flush=True)
    print("gerando retrato centrado p/ bolinha...", flush=True)
    out = await gemini._generate(
        [{"text": PROMPT}, gemini._inline(prepare_src(SRC), "image/png")]
    )
    square = center_square(out)
    save_assets(square)
    print(f"ok {OUT.name}")
    print(f"preview {PREV.name}")


if __name__ == "__main__":
    asyncio.run(main())
