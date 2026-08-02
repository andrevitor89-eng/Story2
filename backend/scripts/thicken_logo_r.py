# -*- coding: utf-8 -*-
"""Contorno fino e uniforme no R da logo STORY.R.US (a partir do backup limpo).

Uso:
  python scripts/thicken_logo_r.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
LOGO = ROOT / "apps" / "web" / "src" / "assets" / "logo.png"
BAK = LOGO.with_suffix(".bak.png")
PREV = LOGO.parent / "logo-preview-dark.png"


def main() -> None:
    src = BAK if BAK.is_file() else LOGO
    im = Image.open(src).convert("RGBA")
    a = np.asarray(im).copy()
    h, w = a.shape[:2]

    # Faixa tipográfica (STORY.R.US)
    y0, y1 = int(h * 0.58), int(h * 0.88)
    band = a[y0:y1]

    navy = (
        (band[:, :, 2] > band[:, :, 0] + 15)
        & (band[:, :, 2] > band[:, :, 1] + 10)
        & (band[:, :, 0] < 80)
        & (band[:, :, 1] < 95)
        & (band[:, :, 2] < 150)
        & (band[:, :, 3] > 180)
    )
    nx = np.where(navy)[1]
    if len(nx) == 0:
        raise SystemExit("nao achei pixels do R")
    cx = int(np.median(nx))
    # só o R (centro tipográfico), evita vazar para outros azuis
    r_mask = navy & (np.abs(np.arange(band.shape[1])[None, :] - cx) < 70)

    # Contorno fino (~2–3px): um MaxFilter 3 + 3
    mask_img = Image.fromarray((r_mask.astype(np.uint8) * 255))
    thick = mask_img.filter(ImageFilter.MaxFilter(3))
    thick = thick.filter(ImageFilter.MaxFilter(3))
    thick_a = np.array(thick) > 40
    stroke_only = thick_a & ~r_mask

    stroke_rgb = np.array([248, 250, 253], dtype=np.uint8)
    print(
        f"src={src.name} R x~{cx} fill={int(r_mask.sum())} stroke={int(stroke_only.sum())}"
    )

    out = a.copy()
    region = out[y0:y1]
    region[stroke_only, 0] = stroke_rgb[0]
    region[stroke_only, 1] = stroke_rgb[1]
    region[stroke_only, 2] = stroke_rgb[2]
    region[stroke_only, 3] = 255
    region[r_mask] = band[r_mask]
    out[y0:y1] = region

    result = Image.fromarray(out)
    result.save(LOGO, optimize=True)

    # Preview em fundo escuro (como na landing) + contorno CSS fino simulado
    pad = 48
    canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (14, 24, 50, 255))
    # sombra/contorno branco fino uniforme (~1.5–2px)
    alpha = result.split()[-1]
    glow = Image.new("RGBA", result.size, (255, 255, 255, 0))
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1)):
        layer = Image.new("RGBA", result.size, (255, 255, 255, 0))
        layer.putalpha(alpha)
        white = Image.new("RGBA", result.size, (255, 255, 255, 230))
        white.putalpha(alpha)
        glow = Image.alpha_composite(glow, white.transform(result.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy)))
    canvas.paste(glow, (pad, pad), glow)
    canvas.paste(result, (pad, pad), result)
    canvas.save(PREV, optimize=True)
    print(f"ok {LOGO.name}")
    print(f"preview {PREV}")


if __name__ == "__main__":
    main()
