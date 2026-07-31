from __future__ import annotations

import asyncio
import base64
import logging
import random

import httpx

from app.ai import offline
from app.ai.prompts import (
    ALPHABET_SCENE_PROMPT,
    CHARACTER_PROMPT,
    GENDER_LABELS,
    SCENE_PROMPT,
)

from app.config import settings
from app.stories.catalog import ALPHABET_STORY_IDS

logger = logging.getLogger("gemini")
BASE = "https://generativelanguage.googleapis.com/v1beta"
TRANSIENT_STATUS = {408, 429, 500, 502, 503, 504}


def _models() -> list[str]:
    primary = (settings.gemini_model or "gemini-2.5-flash-image").strip()
    extras = [
        m.strip()
        for m in (settings.gemini_fallback_models or "").split(",")
        if m.strip() and m.strip() != primary
    ]
    return [primary, *extras]


def _inline(image: bytes, mime: str = "image/png") -> dict:
    return {"inline_data": {"mime_type": mime, "data": base64.b64encode(image).decode()}}


def _extract_image(data: dict) -> bytes | None:
    for cand in data.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            inline = part.get("inline_data") or part.get("inlineData")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])
    return None


async def _generate_once(client: httpx.AsyncClient, model: str, parts: list[dict]) -> bytes:
    url = f"{BASE}/models/{model}:generateContent"
    headers = {"x-goog-api-key": settings.gemini_api_key, "content-type": "application/json"}
    payload = {"contents": [{"role": "user", "parts": parts}]}
    try:
        resp = await client.post(url, json=payload, headers=headers)
    except httpx.RequestError as exc:
        raise RuntimeError(f"Gemini rede: {exc}") from exc

    if resp.status_code in TRANSIENT_STATUS:
        raise RuntimeError(f"Gemini {resp.status_code}: {resp.text[:400]}")
    if resp.status_code >= 400:
        raise RuntimeError(f"Gemini {resp.status_code}: {resp.text[:400]}")

    image = _extract_image(resp.json())
    if image is None:
        raise RuntimeError("Gemini respondeu sem imagem")
    return image


def _is_transient(exc: Exception) -> bool:
    msg = str(exc)
    if "respondeu sem imagem" in msg:
        return True
    return any(f"Gemini {code}" in msg for code in TRANSIENT_STATUS) or "Gemini rede:" in msg


async def _generate(parts: list[dict]) -> bytes:
    models = _models()
    max_retries = max(1, int(settings.gemini_max_retries))
    base_delay = max(1.0, float(settings.gemini_retry_base_seconds))
    verify = settings.gemini_ssl_verify
    last_error: Exception | None = None

    async with httpx.AsyncClient(timeout=120.0, verify=verify) as client:
        for model in models:
            for attempt in range(1, max_retries + 1):
                try:
                    image = await _generate_once(client, model, parts)
                    if attempt > 1 or model != models[0]:
                        logger.info("Gemini ok model=%s attempt=%s", model, attempt)
                    return image
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    transient = _is_transient(exc)
                    logger.warning(
                        "Gemini falhou model=%s attempt=%s/%s transient=%s err=%s",
                        model,
                        attempt,
                        max_retries,
                        transient,
                        exc,
                    )
                    if not transient:
                        break  # tenta proximo modelo
                    if attempt >= max_retries:
                        break
                    delay = min(90.0, base_delay * (2 ** (attempt - 1)))
                    delay += random.uniform(0, 1.5)
                    await asyncio.sleep(delay)

    assert last_error is not None
    raise last_error


async def generate_character(
    photo_bytes: bytes,
    *,
    name: str,
    age: int,
    gender: str,
    photo_mime: str = "image/jpeg",
) -> bytes:
    if not settings.gemini_api_key:
        if settings.offline_fallback:
            logger.info("Offline character for %s (sem GEMINI_API_KEY)", name)
            return offline.placeholder_character(name)
        raise RuntimeError("GEMINI_API_KEY nao configurada no servidor")

    prompt = CHARACTER_PROMPT.format(
        age=age,
        gender_label=GENDER_LABELS.get(gender, "a child"),
    )
    try:
        return await _generate([{"text": prompt}, _inline(photo_bytes, photo_mime)])
    except Exception as exc:  # noqa: BLE001
        if settings.offline_fallback:
            logger.warning("Gemini character failed apos retries (%s); using offline", exc)
            return offline.placeholder_character(name)
        raise


async def generate_scene(
    character_bytes: bytes,
    *,
    name: str,
    page: int,
    page_text: str,
    illustration_note: str,
    story_id: str | None = None,
) -> bytes:
    if not settings.gemini_api_key:
        if settings.offline_fallback:
            return offline.placeholder_scene(name, page, illustration_note)
        raise RuntimeError("GEMINI_API_KEY nao configurada no servidor")

    template = (
        ALPHABET_SCENE_PROMPT
        if (story_id or "").strip() in ALPHABET_STORY_IDS
        else SCENE_PROMPT
    )
    prompt = template.format(
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
            logger.warning("Gemini scene p%s failed apos retries (%s); using offline", page, exc)
            return offline.placeholder_scene(name, page, illustration_note)
        raise
