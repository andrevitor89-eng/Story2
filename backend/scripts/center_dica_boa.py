# -*- coding: utf-8 -*-
"""Recorta dica-boa.png em quadrado com o rosto do Matteo bem no centro."""
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
    # Foto 236x352: rosto um pouco à direita; incluir testa → queixo
    cx, cy = 138, 155  # ~58% x, ~44% y
    side = 200
    left = max(0, min(w - side, cx - side // 2))
    top = max(0, min(h - side, cy - side // 2))
    crop = im.crop((left, top, left + side, top + side)).resize((640, 640), Image.LANCZOS)
    crop.save(OUT, optimize=True)
    print(f"ok {OUT.name} box=({left},{top},{side}) size={crop.size}")


if __name__ == "__main__":
    main()
