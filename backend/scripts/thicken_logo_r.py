# -*- coding: utf-8 -*-
"""Engrossa o contorno do R na logo STORY.R.US (anel ao redor da letra, nao bloco)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
LOGO = ROOT / "apps" / "web" / "src" / "assets" / "logo.png"


def main() -> None:
    src = LOGO.with_suffix(".bak.png")
    if not src.is_file():
        src = LOGO
    im = Image.open(src).convert("RGBA")
    a = np.asarray(im).copy()
    h, w = a.shape[:2]

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
    r_mask = navy & (np.abs(np.arange(band.shape[1])[None, :] - cx) < 78)

    # ~6–8px de contorno (forma da letra)
    mask_img = Image.fromarray((r_mask.astype(np.uint8) * 255))
    thick = mask_img.filter(ImageFilter.MaxFilter(9))
    thick = thick.filter(ImageFilter.MaxFilter(7))
    thick = thick.filter(ImageFilter.MaxFilter(5))
    thick_a = np.array(thick) > 40
    stroke_only = thick_a & ~r_mask

    # contorno claro (quase branco), bem visível no R azul
    stroke_rgb = np.array([242, 246, 252], dtype=np.uint8)

    print(
        f"R x~{cx} fill={int(r_mask.sum())} stroke={int(stroke_only.sum())} "
        f"color={tuple(int(v) for v in stroke_rgb)}"
    )

    out = a.copy()
    region = out[y0:y1]
    region[stroke_only, 0] = stroke_rgb[0]
    region[stroke_only, 1] = stroke_rgb[1]
    region[stroke_only, 2] = stroke_rgb[2]
    region[stroke_only, 3] = 255
    region[r_mask] = band[r_mask]
    out[y0:y1] = region

    Image.fromarray(out).save(LOGO, optimize=True)
    preview = Image.fromarray(out).crop((int(w * 0.08), y0, int(w * 0.95), y1))
    preview_path = LOGO.parent / "logo-r-preview.png"
    preview.save(preview_path)
    print(f"ok {LOGO}")


if __name__ == "__main__":
    main()
