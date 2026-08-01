# -*- coding: utf-8 -*-
"""Regenera capa-dino2 com composição de capa premium (rosto livre + espaço pro titulo).

Uso (Story2/backend):
  python scripts/fix_matteo_cover.py
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
PHOTO = EXEMPLOS / "foto-matteo.png"
AVATAR = EXEMPLOS / "_avatar-dino.png"
COVER = EXEMPLOS / "capa-dino2.jpg"
HERO = EXEMPLOS / "hero-dino.jpg"

PROMPT = """\
Children's book COVER illustration. Vertical portrait. NO text, letters, captions, watermarks, or logos anywhere.

Create a PREMIUM cover for Matteo and the dinosaur world:
- Matteo: toddler boy matching the attached photo/character — short blonde hair, blue eyes,
  gentle happy smile, blue denim overalls with a green tractor patch, brown shoes.
- Beside him: ONE cute small green triceratops (friendly big eyes, dog-sized), never a second child.
- Scene: sunny grassy meadow with soft wildflowers, rolling hills, bright blue sky with soft clouds.
- Painterly refined children's picture book, soft realistic lighting, high detail, premium quality.

CRITICAL COMPOSITION (book cover layout):
- Leave a CLEAR empty sky band in the TOP 22% of the image for a title overlay later.
- Place Matteo's FULL FACE in the middle band of the cover (around 35–55% from the top) —
  face must be large, sharp, fully visible, never cut off.
- Characters stand more in the LOWER two-thirds; do NOT put the face in the top title zone.
- Matteo slightly left of center, dinosaur to his right, both running/playing toward camera.
- Natural anatomy: correct hands, feet, legs — no deformed limbs.
"""


def to_jpg(img_bytes: bytes, out: Path, max_w: int = 1180) -> None:
    im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
    im.save(out, "JPEG", quality=92, optimize=True)


async def main() -> None:
    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY ausente")
    for p in (PHOTO, COVER):
        if not p.is_file():
            raise SystemExit(f"arquivo ausente: {p}")

    os.environ.setdefault("GEMINI_FALLBACK_MODELS", "gemini-2.5-flash-image")
    photo = PHOTO.read_bytes()
    cover = COVER.read_bytes()
    parts: list[dict] = [
        {"text": PROMPT},
        gemini._inline(cover, "image/jpeg"),
        gemini._inline(photo, "image/png"),
    ]
    if AVATAR.is_file():
        parts.append(gemini._inline(AVATAR.read_bytes(), "image/png"))
        parts[0] = {
            "text": PROMPT
            + "\nUse the character portrait for clothing/style consistency; match the real photo face most strictly."
        }

    print("regenerando capa-dino2 (composicao premium)...", flush=True)
    scene = await gemini._generate(parts)
    bak = COVER.with_suffix(".bak.jpg")
    if not bak.is_file():
        bak.write_bytes(COVER.read_bytes())
        print(f"backup -> {bak.name}", flush=True)
    to_jpg(scene, COVER)
    to_jpg(scene, HERO)
    print(f"ok {COVER.name} / {HERO.name}", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
