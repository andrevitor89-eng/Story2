from __future__ import annotations

import io
import random

from PIL import Image, ImageDraw, ImageFont


def _font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def placeholder_character(name: str, size: int = 1024) -> bytes:
    img = Image.new("RGB", (size, size), (255, 236, 210))
    draw = ImageDraw.Draw(img)
    draw.ellipse((280, 180, 744, 644), fill=(255, 210, 170), outline=(120, 80, 60), width=4)
    draw.ellipse((400, 360, 460, 420), fill=(60, 40, 30))
    draw.ellipse((560, 360, 620, 420), fill=(60, 40, 30))
    draw.arc((420, 430, 600, 540), 20, 160, fill=(180, 80, 80), width=6)
    draw.text((size // 2, 780), name[:18], fill=(80, 50, 40), font=_font(48), anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def placeholder_scene(name: str, page: int, note: str, size: int = 1024) -> bytes:
    palette = [
        (180, 220, 255),
        (200, 240, 200),
        (255, 230, 200),
        (240, 210, 255),
        (255, 220, 230),
    ]
    random.seed(page * 97 + len(name))
    bg = palette[page % len(palette)]
    img = Image.new("RGB", (size, size), bg)
    draw = ImageDraw.Draw(img)
    for _ in range(12):
        x = random.randint(40, size - 120)
        y = random.randint(40, size - 200)
        r = random.randint(30, 90)
        color = tuple(max(0, min(255, c + random.randint(-40, 40))) for c in bg)
        draw.ellipse((x, y, x + r, y + r), fill=color)
    draw.ellipse((380, 280, 640, 540), fill=(255, 210, 170), outline=(100, 70, 50), width=3)
    draw.rectangle((0, size - 220, size, size), fill=(250, 248, 240))
    draw.text((40, 40), f"Pag. {page} - {name}", fill=(40, 40, 60), font=_font(36))
    y = size - 180
    words = note.split()
    line = ""
    for word in words:
        test = f"{line} {word}".strip()
        if len(test) > 48:
            draw.text((40, y), line, fill=(60, 60, 80), font=_font(22))
            y += 28
            line = word
        else:
            line = test
    if line:
        draw.text((40, y), line[:60], fill=(60, 60, 80), font=_font(22))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()