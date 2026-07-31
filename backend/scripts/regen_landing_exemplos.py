# -*- coding: utf-8 -*-
"""Regenera imagens de exemplo da landing (estilo refinado + fonte unica).

Uso (a partir de Story2/backend):
  python scripts/regen_landing_exemplos.py
  python scripts/regen_landing_exemplos.py --only mar
  python scripts/regen_landing_exemplos.py --force
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import os
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent  # Story2/
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

from app.ai import gemini  # noqa: E402
from app.config import settings  # noqa: E402

EXEMPLOS = ROOT / "apps" / "web" / "public" / "exemplos"
STORIES = BACKEND / "app" / "stories"

STYLE_EXTRA = (
    "Refined painterly children's picture book, soft realistic lighting, "
    "rich detail, premium quality. Avoid flat cartoon, doodle, clip-art."
)

# Regras duras por tema (corrige erros recorrentes do modelo).
THEME_RULES = {
    "mar": (
        "CRITICAL: The child is a MERMAID / merboy with a colorful fish tail from the waist down "
        "in EVERY underwater scene. Face must match the character reference. "
        "Never put the child in shorts/shirt underwater. Recurring friends: friendly pufferfish, "
        "purple octopus, small yellow fish."
    ),
    "dino": (
        "CRITICAL: Dino is ALWAYS a cute GREEN DINOSAUR (triceratops-like, dog-sized, friendly big eyes) "
        "- NEVER a second human child. Matteo is the only human child. "
        "Both appear together when the note mentions the two friends."
    ),
    "flor": (
        "Sofia is the only human child. Fireflies are small glowing insects, not people."
    ),
    "circo": (
        "Noah is a toddler in the audience. The clown is gentle and child-friendly, never scary."
    ),
}

THEMES = {
    "mar": {
        "story_id": "fundo_do_mar",
        "photo": "foto-bebe.jpg",
        "name": "Lia",
        "age": 2,
        "gender": "girl",
        "prefix": "mar",
        "cover": "capa-oceano.jpg",
        "pages": 6,
        "page_offset": 1,
        "band": "5-9",
    },
    "dino": {
        "story_id": "aventuras_dino",
        "photo": "foto-matteo.png",
        "name": "Matteo",
        "age": 4,
        "gender": "boy",
        "prefix": "dino",
        "cover": "capa-dino2.jpg",
        "pages": 6,
        "page_offset": 1,
        "band": "5-9",
        "char_out": "personagem-dino.jpg",
    },
    "flor": {
        "story_id": None,
        "photo": "foto-sofia.png",
        "name": "Sofia",
        "age": 3,
        "gender": "girl",
        "prefix": "flor",
        "cover": "capa-floresta2.jpg",
        "pages": 6,
        "demo": [
            {
                "text": "Na floresta encantada, as arvores sussurram um segredo de luz.",
                "illustration_note": "Sofia numa floresta mistica ao entardecer, vaga-lumes suaves ao fundo.",
            },
            {
                "text": "Um vaga-lume pisca: plim, plim, boa noite!",
                "illustration_note": "Close de vaga-lume brilhante perto do rosto de Sofia.",
            },
            {
                "text": "Eu falo com luz, no meu jeitinho! Mas hoje estou triste, sem brilho.",
                "illustration_note": "Vaga-lume apagado e triste; Sofia preocupada, floresta mais escura.",
            },
            {
                "text": "A floresta apagou! Me ajuda, por favor?",
                "illustration_note": "Floresta escura; Sofia estendendo a mao gentilmente para ajudar.",
            },
            {
                "text": "Com um toque gentil, os vaga-lumes acendem de novo, um por um.",
                "illustration_note": "Sofia tocando suavemente; luzes acendendo entre folhas e musgo.",
            },
            {
                "text": "E a noite fica magica: luzes dancando, amizade brilhando.",
                "illustration_note": "Cena final: floresta iluminada por vaga-lumes; Sofia sorrindo.",
            },
        ],
    },
    "circo": {
        "story_id": None,
        "photo": "foto-bebe.jpg",
        "name": "Noah",
        "age": 2,
        "gender": "boy",
        "prefix": "circo",
        "cover": "capa-circo.jpg",
        "pages": 6,
        "demo": [
            {
                "text": "Sob as luzes do circo, a plateia espera o show comecar.",
                "illustration_note": "Tenda do circo iluminada; bebe Noah na plateia, olhos brilhando.",
            },
            {
                "text": "Um palhaco malabarista jogava bolinhas no ceu.",
                "illustration_note": "Palhaco gentil fazendo malabares coloridos; Noah assiste.",
            },
            {
                "text": "Malabares treinam as maos! Contou ao pequeno espectador.",
                "illustration_note": "Palhaco explicando com carinho; Noah atento na primeira fila.",
            },
            {
                "text": "Zup, zup! As esferas dancavam sem cair.",
                "illustration_note": "Bolinhas coloridas no ar sob holofotes dourados.",
            },
            {
                "text": "E o bebe batia palminhas so de assistir, cheio de alegria.",
                "illustration_note": "Noah batendo palmas, sorriso largo, plateia ao fundo.",
            },
            {
                "text": "No final, aplausos e um brilho especial: a magia do circo.",
                "illustration_note": "Aplausos finais; luzes do circo; Noah radiante.",
            },
        ],
    },
}


def _font(size: int) -> ImageFont.ImageFont:
    for path in (
        Path(r"C:\Windows\Fonts\georgia.ttf"),
        Path(r"C:\Windows\Fonts\Georgia.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
    ):
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def compose_page(img_bytes: bytes, caption: str, out: Path, width: int = 1180) -> None:
    im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    if im.width != width:
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    W, H = im.size
    font = _font(max(26, W // 36))
    wrap_w = max(28, W // (font.size // 2 or 14))
    lines: list[str] = []
    for para in caption.replace("{NOME}", " ").splitlines():
        para = para.strip()
        if not para:
            continue
        lines.extend(textwrap.wrap(para, width=wrap_w) or [para])
    lines = lines[:4]
    if lines:
        lh = int(font.size * 1.32)
        pad = int(font.size * 0.85)
        bh = lh * len(lines) + pad * 2
        y0 = H - bh - int(H * 0.03)
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rectangle((0, y0 - 8, W, H), fill=(18, 22, 36, 110))
        im = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(im)
        y = y0 + pad
        for ln in lines:
            tw = draw.textlength(ln, font=font)
            x = (W - tw) / 2
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (1, 1), (-1, 1)):
                draw.text((x + dx, y + dy), ln, font=font, fill=(20, 24, 36))
            draw.text((x, y), ln, font=font, fill=(255, 252, 245))
            y += lh
    im.save(out, "JPEG", quality=90, optimize=True)


def to_jpg(img_bytes: bytes, out: Path, max_w: int = 1180) -> None:
    im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
    im.save(out, "JPEG", quality=90, optimize=True)


def load_pages(theme: dict) -> list[dict]:
    if theme.get("demo"):
        return theme["demo"]
    data = json.loads((STORIES / f"{theme['story_id']}.json").read_text(encoding="utf-8"))
    band = theme["band"]
    pages = data["variants"][band]["pages"]
    start = theme.get("page_offset", 0)
    chunk = pages[start : start + theme["pages"]]
    name = theme["name"]
    out = []
    for pg in chunk:
        out.append(
            {
                "text": pg["text"].replace("{NOME}", name),
                "illustration_note": pg["illustration_note"].replace("{NOME}", name),
            }
        )
    return out


async def regen_theme(key: str, force: bool) -> None:
    theme = THEMES[key]
    photo_path = EXEMPLOS / theme["photo"]
    if not photo_path.is_file():
        raise FileNotFoundError(photo_path)

    avatar_cache = EXEMPLOS / f"_avatar-{theme['prefix']}.png"
    if force and avatar_cache.is_file():
        avatar_cache.unlink()
    if avatar_cache.is_file() and not force:
        char = avatar_cache.read_bytes()
        print(f"[{key}] avatar reutilizado", flush=True)
    else:
        print(f"[{key}] gerando personagem...", flush=True)
        mime = "image/png" if photo_path.suffix.lower() == ".png" else "image/jpeg"
        char = await _retry(
            lambda: gemini.generate_character(
                photo_path.read_bytes(),
                name=theme["name"],
                age=theme["age"],
                gender=theme["gender"],
                photo_mime=mime,
            ),
            label=f"{key}/avatar",
        )
        avatar_cache.write_bytes(char)
        if theme.get("char_out"):
            to_jpg(char, EXEMPLOS / theme["char_out"])

    pages = load_pages(theme)
    rules = THEME_RULES.get(key, "")
    for i, pg in enumerate(pages, 1):
        out = EXEMPLOS / f"{theme['prefix']}-{i}.jpg"
        if out.is_file() and not force:
            print(f"[{key}] {out.name} ja existe - pulando", flush=True)
            continue
        note = f"{pg['illustration_note']}. {rules} {STYLE_EXTRA}".strip()
        print(f"[{key}] pagina {i}/{len(pages)}...", flush=True)
        try:
            scene = await _retry(
                lambda pg=pg, note=note, i=i: gemini.generate_scene(
                    char,
                    name=theme["name"],
                    page=i,
                    page_text=pg["text"],
                    illustration_note=note,
                ),
                label=f"{key}/p{i}",
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[{key}] FALHA pagina {i}: {exc}", flush=True)
            continue
        compose_page(scene, pg["text"], out)
        if i == 1:
            to_jpg(scene, EXEMPLOS / theme["cover"])
        print(f"[{key}] ok {out.name}", flush=True)


async def _retry(fn, *, label: str, attempts: int = 5):
    last: Exception | None = None
    for n in range(1, attempts + 1):
        try:
            return await fn()
        except Exception as exc:  # noqa: BLE001
            last = exc
            wait = min(60.0, 4.0 * n)
            print(f"[{label}] tentativa {n}/{attempts} falhou: {exc}", flush=True)
            print(f"[{label}] aguardando {wait:.0f}s...", flush=True)
            await asyncio.sleep(wait)
    assert last is not None
    raise last


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=list(THEMES), default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY ausente - configure Story2/backend/.env")

    # Fallback antigo 404; manter so o modelo principal de imagem.
    os.environ.setdefault("GEMINI_FALLBACK_MODELS", "gemini-2.5-flash-image")

    print(f"exemplos={EXEMPLOS}", flush=True)
    print(f"model={settings.gemini_model}", flush=True)
    keys = [args.only] if args.only else list(THEMES)
    for key in keys:
        await regen_theme(key, force=args.force)
    print("DONE", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
