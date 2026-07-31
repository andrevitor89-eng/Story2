# -*- coding: utf-8 -*-
"""Regenera avatar + capa da Sofia com rosto fiel a foto-sofia.png.

Uso (Story2/backend):
  python scripts/fix_sofia_face.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

import io  # noqa: E402

from PIL import Image  # noqa: E402

from app.ai import gemini  # noqa: E402
from app.config import settings  # noqa: E402

# Ambiente Windows local às vezes falha o CA bundle; geração pontual não precisa travar nisso.
settings.gemini_ssl_verify = False

EXEMPLOS = ROOT / "apps" / "web" / "public" / "exemplos"


def to_jpg(img_bytes: bytes, out: Path, max_w: int = 1180) -> None:
    im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
    im.save(out, "JPEG", quality=90, optimize=True)
PHOTO = EXEMPLOS / "foto-sofia.png"
AVATAR = EXEMPLOS / "_avatar-flor.png"
COVER = EXEMPLOS / "capa-floresta2.jpg"
HERO = EXEMPLOS / "hero-flor.jpg"
PAGE1 = EXEMPLOS / "flor-1.jpg"


COVER_NOTE = (
    "BOOK COVER scene (no text anywhere). Sofia alone in a mystical enchanted forest "
    "at twilight, framed by two large dark tree trunks with soft hanging moss. "
    "Gentle yellow fireflies and tiny glowing blue mushrooms. She stands facing camera, "
    "barefoot, white dress with thin pink trim on V-neck and sleeves, soft curious smile. "
    "CRITICAL FACE RULES: face must be an exact likeness of the attached photo AND character "
    "reference — same round cheeks, same eye shape/spacing, same small closed-mouth smile, "
    "same wavy medium-brown hair, same skin tone. Natural symmetric features, soft painterly "
    "blend into the scene (not pasted-on), no uncanny asymmetry, no oversized anime eyes. "
    "Refined premium children's picture book, soft realistic lighting. No text, letters, logos."
)


async def main() -> None:
    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY ausente")
    if not PHOTO.is_file():
        raise SystemExit(f"foto ausente: {PHOTO}")

    os.environ.setdefault("GEMINI_FALLBACK_MODELS", "gemini-2.5-flash-image")
    photo = PHOTO.read_bytes()

    print("gerando avatar (rosto fiel)...", flush=True)
    char = await gemini.generate_character(
        photo,
        name="Sofia",
        age=3,
        gender="girl",
        photo_mime="image/png",
    )
    AVATAR.write_bytes(char)
    print(f"ok {AVATAR.name}", flush=True)

    print("gerando capa com rosto corrigido...", flush=True)
    # Foto + avatar juntos = mais fidelidade facial na capa
    prompt = (
        "Children's book COVER illustration. No text, letters, captions, watermarks, or logos.\n"
        f"Child name: Sofia\nScene: {COVER_NOTE}\n"
        "Use BOTH attached images as face identity: (1) real photo, (2) character portrait. "
        "Match the real photo's face most strictly."
    )
    scene = await gemini._generate(
        [
            {"text": prompt},
            gemini._inline(photo, "image/png"),
            gemini._inline(char, "image/png"),
        ]
    )
    to_jpg(scene, COVER)
    to_jpg(scene, HERO)
    print(f"ok {COVER.name} / {HERO.name}", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
