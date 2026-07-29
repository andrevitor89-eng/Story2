from __future__ import annotations

import base64
import logging
import os

import httpx

from app.ai import offline
from app.ai.prompts import CHARACTER_PROMPT, GENDER_LABELS, SCENE_PROMPT
from app.config import settings

logger = logging.getLogger("gemini")
MODEL = "gemini-2.5-flash-image"
BASE = "https://generativelanguage.googleapis.com/v1beta"


def _use_offline() -> bool:
    if not settings.gemini_api_key:
        return True
    return settings.offline_fallback and os.getenv("FORCE_OFFLINE", "").lower() in (
        "1",
        "true",
        "yes",
    )


def _inline(image: bytes, mime: str = "image/png") -> dict:
    return {"inline_data": {"mime_type": mime, "data": base64.b64encode(image).decode()}}


async def _generate(parts: list[dict]) -> bytes:
    url = f"{BASE}/models/{MODEL}:generateContent"
    headers = {"x-goog-api-key": settings.gemini_api_key, "content-type": "application/json"}
    payload = {"contents": [{"role": "user", "parts": parts}]}
    verify = settings.gemini_ssl_verify
    async with httpx.AsyncClient(timeout=120.0, verify=verify) as client:
        resp = await client.post(url, json=payload, headers=headers)
    if resp.status_code >= 400:
        raise RuntimeError(f"Gemini {resp.status_code}: {resp.text[:400]}")
    data = resp.json()
    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            inline = part.get("inline_data") or part.get("inlineData")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])
    raise RuntimeError("Gemini respondeu sem imagem")


async def generate_character(
    photo_bytes: bytes,
    *,
    name: str,
    age: int,
    gender: str,
    photo_mime: str = "image/jpeg",
) -> bytes:
    if not settings.gemini_api_key:
        logger.info("Offline character for %s", name)
        return offline.placeholder_character(name)

    prompt = CHARACTER_PROMPT.format(
        age=age,
        gender_label=GENDER_LABELS.get(gender, "a child"),
    )
    try:
        return await _generate([{"text": prompt}, _inline(photo_bytes, photo_mime)])
    except Exception as exc:  # noqa: BLE001
        if settings.offline_fallback:
            logger.warning("Gemini character failed (%s); using offline", exc)
            return offline.placeholder_character(name)
        raise


async def generate_scene(
    character_bytes: bytes,
    *,
    name: str,
    page: int,
    page_text: str,
    illustration_note: str,
) -> bytes:
    if not settings.gemini_api_key:
        return offline.placeholder_scene(name, page, illustration_note)

    prompt = SCENE_PROMPT.format(
        name=name,
        illustration_note=illustration_note,
        page_text=page_text,
    )
    try:
        return await _generate(
            [{"text": prompt}, _inline(character_bytes, "image/png")]
        )
    except Exception as exc:  # noqa: BLE001
        if settings.offline_fallback:
            logger.warning("Gemini scene p%s failed (%s); using offline", page, exc)
            return offline.placeholder_scene(name, page, illustration_note)
        raise
