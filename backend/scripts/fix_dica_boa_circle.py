# -*- coding: utf-8 -*-
"""Completa SÓ o lado direito da foto do Matteo (remove adulto), sem alterar o rosto.

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
SRC = EX / "dica-boa.bak.png"
OUT = EX / "dica-boa.png"
PREV = EX / "_dica-boa-preview.png"

PROMPT = """
PHOTO EDIT — inpaint / outpaint ONLY the right edge.

SOURCE: real photo of a toddler boy (Matteo). On the RIGHT edge, an adult's tan cheek and hair are pressed against his face and cut him off.

DO THIS:
1) Remove the adult completely from the right side.
2) Complete ONLY what is missing on Matteo's RIGHT side: right temple, right ear area, right side of blond hair, and a bit of outdoor background.
3) Output a SQUARE 1:1 portrait with his face centered, full head visible with small margin — ready for a circular crop.

ABSOLUTE RULES — DO NOT CHANGE HIS FACE:
- Keep the LEFT side of his face, eyes, nose, mouth, teeth gap, cheeks, skin, hair color/texture PIXEL-IDENTICAL to the source.
- Do NOT beautify, smooth, rejuvenate, restyle, or redraw his face.
- Do NOT change eye color, eye shape, smile, or expression.
- The result must look like the SAME photograph, only with the adult removed and the missing right edge filled.

Photorealistic. No text, watermark, border, or circle mask.
""".strip()


def prepare_src(path: Path) -> bytes:
    """Pad right side so the model has canvas to fill, keep face intact."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    # Extra canvas on the right (adult zone) + slight top/bottom for square room
    pad_r = int(w * 0.28)
    pad_tb = int(h * 0.06)
    padded = ImageOps.expand(im, border=(0, pad_tb, pad_r, pad_tb), fill=(196, 170, 140))
    # Upscale a bit for quality
    scale = max(1.0, 900 / max(padded.size))
    if scale > 1:
        padded = padded.resize(
            (int(padded.width * scale), int(padded.height * scale)),
            Image.Resampling.LANCZOS,
        )
    buf = io.BytesIO()
    padded.save(buf, format="PNG")
    return buf.getvalue()


def to_circle_assets(img_bytes: bytes) -> None:
    im = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    w, h = im.size
    side = min(w, h)
    # Bias slightly left so completed right side has room but face stays center
    left = max(0, min(w - side, (w - side) // 2 - int(side * 0.02)))
    top = max(0, min(h - side, (h - side) // 2 - int(side * 0.03)))
    crop = im.crop((left, top, left + side, top + side))
    crop = crop.resize((768, 768), Image.Resampling.LANCZOS)
    crop.save(OUT, "PNG", optimize=True)

    mask = Image.new("L", (768, 768), 0)
    ImageDraw.Draw(mask).ellipse((10, 10, 758, 758), fill=255)
    circ = Image.new("RGBA", (768, 768), (14, 24, 50, 255))
    circ.paste(crop, (0, 0), mask)
    circ.save(PREV, "PNG")


async def main() -> None:
    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY ausente")
    if not SRC.is_file():
        raise SystemExit(f"fonte ausente: {SRC}")

    os.environ.setdefault("GEMINI_FALLBACK_MODELS", "gemini-2.5-flash-image")
    src_bytes = prepare_src(SRC)

    print("completando lado direito (rosto intacto)...", flush=True)
    out = await gemini._generate(
        [{"text": PROMPT}, gemini._inline(src_bytes, "image/png")]
    )
    to_circle_assets(out)
    print(f"ok {OUT.name}")
    print(f"preview {PREV.name}")


if __name__ == "__main__":
    asyncio.run(main())
