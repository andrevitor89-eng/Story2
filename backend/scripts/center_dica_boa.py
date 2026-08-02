# -*- coding: utf-8 -*-
"""Gera dica-boa.png com rosto centralizado (recorte quadrado a partir do backup)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

EX = Path(__file__).resolve().parents[2] / "apps" / "web" / "public" / "exemplos"
SRC = EX / "dica-boa.bak.png"
OUT = EX / "dica-boa.png"
PREV = EX / "_dica-boa-preview.png"


def main() -> None:
    if not SRC.is_file():
        raise SystemExit(f"backup ausente: {SRC}")

    im = Image.open(SRC).convert("RGBA")
    w, h = im.size

    # Centro do rostinho (Matteo) no retrato original 236x352 —
    # ponto no meio do rosto (entre olhos e boca), com margem p/ testa→queixo.
    cx, cy = int(w * 0.52), int(h * 0.49)
    side = int(min(w, h) * 0.84)
    left = max(0, min(w - side, cx - side // 2))
    top = max(0, min(h - side, cy - side // 2))

    crop = im.crop((left, top, left + side, top + side))
    out = crop.resize((640, 640), Image.Resampling.LANCZOS)
    out.save(OUT)

    mask = Image.new("L", (640, 640), 0)
    ImageDraw.Draw(mask).ellipse((8, 8, 632, 632), fill=255)
    circ = Image.new("RGBA", (640, 640), (14, 24, 50, 255))
    circ.paste(out, (0, 0), mask)
    circ.save(PREV)

    print(f"ok crop=({left},{top},{left+side},{top+side}) -> {OUT.name} + preview")


if __name__ == "__main__":
    main()
