# -*- coding: utf-8 -*-
"""Completa a lateral do rosto (remove adulto) e gera dica-boa.png centrada p/ o círculo.

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
SRC = EX / "_dica-boa-src.png"
OUT = EX / "dica-boa.png"
BAK = EX / "dica-boa.bak.png"
PREV = EX / "_dica-boa-preview.png"

PROMPT = """
Photorealistic IMAGE EDIT / reconstruction. Output ONE square photo.

SOURCE: the attached close-up of a toddler boy. An adult's tan cheek/hair is stuck to the RIGHT edge of his face — that adult must be REMOVED completely.

GOAL: a clean head-and-shoulders portrait of ONLY the boy, for a circular avatar.
- Face PERFECTLY CENTERED in a 1:1 square frame
- Full head visible with comfortable margin: top of hair, both ears, both cheeks, chin all inside the frame
- Reconstruct the boy's missing RIGHT side of the head (cheek, jaw, ear, hair) so it mirrors naturally the left side
- Keep his exact identity from the source: bright blue eyes, soft smile with small teeth, fair skin, light blond hair, blue denim overalls strap with metal button
- Soft outdoor blur background (no other people, no adult arm)
- High resolution, natural daylight, photorealistic — not illustration
- No text, watermark, border, frame, or circle mask

Do NOT pull back to a wide full-body shot. Stay CLOSE on the face like the source crop, but completed and centered.
""".strip()


def upscale_src(path: Path, min_side: int = 768) -> bytes:
    """Upscale tiny source so the model has more pixels to edit."""
    im = Image.open(path).convert("RGB")
    # slight pad on the right so model has canvas to fill the adult area
    pad_r = int(im.width * 0.22)
    pad_t = int(im.height * 0.12)
    pad_b = int(im.height * 0.08)
    padded = ImageOps.expand(im, border=(pad_t, pad_t, pad_r, pad_b), fill=(210, 190, 160))
    w, h = padded.size
    scale = max(min_side / w, min_side / h)
    if scale > 1:
        padded = padded.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    padded.save(buf, format="PNG")
    return buf.getvalue()


def to_square_png(img_bytes: bytes, out: Path, size: int = 768) -> None:
    im = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    crop = im.crop((left, top, left + side, top + side))
    crop = crop.resize((size, size), Image.Resampling.LANCZOS)
    crop.save(out, "PNG", optimize=True)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((6, 6, size - 7, size - 7), fill=255)
    circ = Image.new("RGBA", (size, size), (14, 24, 50, 255))
    circ.paste(crop, (0, 0), mask)
    circ.save(PREV, "PNG")


async def main() -> None:
    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY ausente")
    if not SRC.is_file():
        raise SystemExit(f"fonte ausente: {SRC}")

    os.environ.setdefault("GEMINI_FALLBACK_MODELS", "gemini-2.5-flash-image")

    if OUT.is_file() and not BAK.is_file():
        BAK.write_bytes(OUT.read_bytes())

    src_bytes = upscale_src(SRC)
    print("gerando close-up centrado (IA)...", flush=True)
    out = await gemini._generate(
        [{"text": PROMPT}, gemini._inline(src_bytes, "image/png")]
    )
    to_square_png(out, OUT)
    print(f"ok {OUT.name} preview={PREV.name}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
