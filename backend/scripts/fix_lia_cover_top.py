# -*- coding: utf-8 -*-
"""Regenera capa-oceano com top/blusa (cliente: sereia sem camisa nao ficou legal).

Uso (Story2/backend):
  python scripts/fix_lia_cover_top.py
"""
from __future__ import annotations

import asyncio
import io
import os
import sys
from pathlib import Path

from PIL import Image

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

from app.ai import gemini  # noqa: E402
from app.config import settings  # noqa: E402

settings.gemini_ssl_verify = False

EXEMPLOS = ROOT / "apps" / "web" / "public" / "exemplos"
PHOTO = EXEMPLOS / "foto-bebe.jpg"
AVATAR = EXEMPLOS / "_avatar-mar.png"
COVER = EXEMPLOS / "capa-oceano.jpg"
REF_WITH_TOP = EXEMPLOS / "mar-2.jpg"

PROMPT = """\
Children's book COVER illustration. No text, letters, captions, watermarks, or logos.

Edit / recreate this underwater book cover of Lia the little mermaid:
- Keep the SAME underwater coral reef composition, friendly pufferfish, purple octopus,
  colorful fish, sunbeams, and magical painterly children's-book style.
- Keep Lia's face identity from the attached photo + character portrait (same toddler face,
  short blonde hair, blue eyes, gentle smile).
- CRITICAL MODESTY FIX: Lia MUST wear a cute modest short-sleeved white blouse (or seashell
  bikini top) covering her chest completely. NO bare torso, NO topless mermaid.
- She still has a colorful iridescent mermaid fish tail from the waist down.
- Premium refined children's picture book, soft realistic lighting. Vertical cover, no text.
"""


def to_jpg(img_bytes: bytes, out: Path, max_w: int = 1180) -> None:
    im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
    im.save(out, "JPEG", quality=92, optimize=True)


async def main() -> None:
    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY ausente")
    for p in (PHOTO, AVATAR, COVER):
        if not p.is_file():
            raise SystemExit(f"arquivo ausente: {p}")

    os.environ.setdefault("GEMINI_FALLBACK_MODELS", "gemini-2.5-flash-image")
    photo = PHOTO.read_bytes()
    char = AVATAR.read_bytes()
    cover = COVER.read_bytes()
    parts = [
        {"text": PROMPT},
        gemini._inline(cover, "image/jpeg"),
        gemini._inline(photo, "image/jpeg"),
        gemini._inline(char, "image/png"),
    ]
    if REF_WITH_TOP.is_file():
        parts.append(gemini._inline(REF_WITH_TOP.read_bytes(), "image/jpeg"))
        parts[0] = {
            "text": PROMPT
            + "\nUse mar-2 (last image) as clothing reference: white short-sleeved blouse covering chest."
        }

    print("regenerando capa-oceano com top...", flush=True)
    scene = await gemini._generate(parts)
    # backup
    bak = COVER.with_suffix(".bak.jpg")
    if not bak.is_file():
        bak.write_bytes(COVER.read_bytes())
        print(f"backup -> {bak.name}", flush=True)
    to_jpg(scene, COVER)
    print(f"ok {COVER.name}", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
