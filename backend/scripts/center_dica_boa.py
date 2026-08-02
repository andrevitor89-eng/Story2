# -*- coding: utf-8 -*-
"""Recorta dica-boa.png em quadrado centrado no rosto do Matteo."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

EX = Path(__file__).resolve().parents[2] / "apps" / "web" / "public" / "exemplos"
OUT = EX / "dica-boa.png"
SRC = EX / "dica-boa.bak.png"
if not SRC.is_file():
    SRC = OUT


def main() -> None:
    im = Image.open(SRC).convert("RGB")
    w, h = im.size
    # Matteo: olhos no centro vertical/horizontal do quadrado
    cx = int(w * 0.55)
    cy = int(h * 0.36)
    side = int(min(w, h) * 0.90)
    left = max(0, min(w - side, cx - side // 2))
    top = max(0, min(h - side, cy - side // 2))
    crop = im.crop((left, top, left + side, top + side))
    # exporta em tamanho bom para retina
    crop = crop.resize((512, 512), Image.LANCZOS)
    crop.save(OUT, optimize=True)
    print(f"ok {OUT.name} from {SRC.name} focus=({cx},{cy}) box=({left},{top},{side}) -> {crop.size}")


if __name__ == "__main__":
    main()
