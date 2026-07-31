# -*- coding: utf-8 -*-
"""Kids-safe motion prompts for Kling image2video."""
from __future__ import annotations


_THEME_BITS = {
    "mar": "bubbles rising, soft underwater currents, fish drifting slowly",
    "oceano": "bubbles rising, soft underwater currents, fish drifting slowly",
    "underwater": "bubbles rising, soft underwater currents, fish drifting slowly",
    "fundo_do_mar": "bubbles rising, soft underwater currents, fish drifting slowly",
    "flor": "fireflies glowing and drifting, leaves swaying gently",
    "floresta": "fireflies glowing and drifting, leaves swaying gently",
    "fantasy": "fireflies glowing and drifting, leaves swaying gently",
    "circo": "juggling balls arcing softly, warm circus lights twinkling",
    "dino": "gentle dinosaur looking around, soft prehistoric mist drifting",
    "aventuras_dino": "gentle dinosaur looking around, soft prehistoric mist drifting",
    "fazenda": "farm animals shifting softly, wind in the grass",
    "bichinhos_fazenda": "farm animals shifting softly, wind in the grass",
    "adventure": "gentle camera push-in, soft magical sparkles",
}


def _resolve_atmosphere(theme: str = "", story_id: str = "") -> str:
    keys = [
        (story_id or "").lower().strip(),
        (theme or "").lower().strip(),
    ]
    for key in keys:
        if key in _THEME_BITS:
            return _THEME_BITS[key]
    blob = " ".join(keys)
    for needle, value in _THEME_BITS.items():
        if needle in blob:
            return value
    return "subtle living background details"


def build_motion_prompt(note: str = "", *, theme: str = "", story_id: str = "") -> str:
    """Prompt de movimento suave, personagem estavel, fundo vivo."""
    base = (
        "Gentle cinematic motion for a children's storybook illustration. "
        "Keep the same child character face and body proportions. "
        "Soft ambient background movement. No text overlays, no morphing, "
        "no horror, no sudden cuts. Smooth and magical."
    )
    extra = _resolve_atmosphere(theme=theme, story_id=story_id)
    note = (note or "").strip()
    if note:
        return f"{base} Scene action: {note[:220]}. Atmosphere: {extra}."
    return f"{base} Atmosphere: {extra}."


def duration_for_audio_seconds(audio_s: float) -> int:
    """Kling so aceita 5 ou 10s; alinha ao TTS."""
    return 5 if float(audio_s) <= 6.0 else 10
