# -*- coding: utf-8 -*-
"""Gera capas do hero com titulo dourado estilo Historia Surpresa (Gemini).

Uso (Story2/backend):
  python scripts/gen_hero_titles.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from PIL import Image
import io

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

from app.ai import gemini  # noqa: E402
from app.config import settings  # noqa: E402

EXEMPLOS = ROOT / "apps" / "web" / "public" / "exemplos"

HEROES = [
    {
        "src": "capa-dino2.jpg",
        "out": "hero-dino.jpg",
        "title": "Matteo e o Mundo\ndos Dinossauros",
        "title_one_line": "Matteo e o Mundo dos Dinossauros",
    },
    {
        "src": "capa-floresta2.jpg",
        "out": "hero-flor.jpg",
        "title": "Sofia e a Floresta\nEncantada",
        "title_one_line": "Sofia e a Floresta Encantada",
    },
    {
        "src": "capa-circo.jpg",
        "out": "hero-circo.jpg",
        "title": "Noah e o Circo\ndas Luzes",
        "title_one_line": "Noah e o Circo das Luzes",
    },
]


def to_jpg(img_bytes: bytes, out: Path, max_w: int = 1400) -> None:
    im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
    im.save(out, "JPEG", quality=92, optimize=True)


async def paint_title(src: Path, ref: Path | None, title: str, title_one_line: str) -> bytes:
    prompt = (
        "You are editing a children's personalized book COVER for a premium product hero banner.\n"
        "KEEP the exact same illustration: same child face, same pose, same animals, same background, "
        "same colors and composition. Do NOT redraw the scene from scratch.\n"
        "ONLY add (or replace any existing title with) a large, irresistible COVER TITLE at the TOP CENTER.\n"
        "Title typography MUST match premium gold glitter kids-book lettering like 'História Surpresa': "
        "bold rounded sans letters, metallic sparkling gold fill, soft outer glow, subtle drop shadow, "
        "slight 3D emboss, highly attractive and magical.\n"
        f"Title text EXACTLY (use line breaks as shown):\n{title}\n"
        f"(same words as: {title_one_line})\n"
        "Portuguese spelling must be perfect. No other text, watermarks, logos, or captions.\n"
        "Leave clear space at the top for the title; do not cover the child's face."
    )
    parts: list[dict] = [{"text": prompt}, gemini._inline(src.read_bytes(), "image/jpeg")]
    if ref and ref.is_file():
        parts.append({"text": "Reference for the GOLD GLITTER title style only (ignore the scene):"})
        parts.append(gemini._inline(ref.read_bytes(), "image/jpeg"))
    return await gemini._generate(parts)


async def main() -> None:
    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY missing")
    ref = EXEMPLOS / "capa-surpresa.jpg"
    for h in HEROES:
        src = EXEMPLOS / h["src"]
        out = EXEMPLOS / h["out"]
        if not src.is_file():
            raise FileNotFoundError(src)
        print(f"=== {h['out']} from {h['src']} ===", flush=True)
        img = await paint_title(src, ref, h["title"], h["title_one_line"])
        to_jpg(img, out)
        print(f"  wrote {out} ({out.stat().st_size} bytes)", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
