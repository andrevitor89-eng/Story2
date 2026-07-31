# -*- coding: utf-8 -*-
"""Kling image2video client (api.klingai.com).

Modos de auth:
1) KLING_API_KEY (ex. api-key-kling-...): Bearer direto na API oficial
2) KLING_ACCESS_KEY + KLING_SECRET_KEY: JWT HS256 (console antigo)
"""
from __future__ import annotations

import base64
import time
from dataclasses import dataclass

import httpx
from jose import jwt

from app.config import settings

_BASE = "https://api.klingai.com"
_CREATE = "/v1/videos/image2video"


@dataclass
class VideoJob:
    provider_task_id: str
    status: str  # PENDING | RUNNING | DONE | FAILED
    video_url: str | None = None


class KlingError(Exception):
    def __init__(self, message: str, *, transient: bool = False):
        super().__init__(message)
        self.transient = transient


def _make_token(access_key: str, secret_key: str) -> str:
    now = int(time.time())
    payload = {"iss": access_key, "exp": now + 1800, "nbf": now - 5}
    return jwt.encode(
        payload, secret_key, algorithm="HS256", headers={"alg": "HS256", "typ": "JWT"}
    )


def _map_status(s: str) -> str:
    return {
        "submitted": "PENDING",
        "processing": "RUNNING",
        "succeed": "DONE",
        "failed": "FAILED",
    }.get((s or "").lower(), "RUNNING")


def clamp_duration(duration_s: int) -> int:
    return 10 if int(duration_s) >= 8 else 5


def resolve_kling_api_key() -> str:
    """Chave Bearer unica do console novo (sem Access/Secret separados)."""
    key = (settings.kling_api_key or "").strip()
    if key:
        return key
    ak = (settings.kling_access_key or "").strip()
    if ak.startswith("api-key-kling-"):
        return ak
    return ""


def kling_configured() -> bool:
    if resolve_kling_api_key():
        return True
    return bool(
        (settings.kling_access_key or "").strip() and (settings.kling_secret_key or "").strip()
    )


def use_video_offline() -> bool:
    """Sem chave: GIF offline. Com chave: sempre chama o provedor real."""
    return not kling_configured()


class KlingVideoProvider:
    name = "kling"

    def __init__(self, timeout: float = 60.0):
        self._api_key = resolve_kling_api_key()
        self._ak = (settings.kling_access_key or "").strip()
        self._sk = (settings.kling_secret_key or "").strip()
        self._timeout = timeout

    def _headers(self) -> dict:
        if self._api_key:
            token = self._api_key
        elif self._ak and self._sk:
            token = _make_token(self._ak, self._sk)
        else:
            raise KlingError(
                "KLING_API_KEY ou KLING_ACCESS_KEY/SECRET_KEY ausentes", transient=False
            )
        return {
            "Authorization": f"Bearer {token}",
            "content-type": "application/json",
        }

    def _check(self, resp: httpx.Response) -> dict:
        if resp.status_code in (429, 500, 502, 503, 504):
            raise KlingError(f"Kling {resp.status_code}", transient=True)
        if resp.status_code >= 400:
            raise KlingError(f"Kling {resp.status_code}: {resp.text[:300]}", transient=False)
        body = resp.json()
        if body.get("code", 0) != 0:
            raise KlingError(f"Kling code={body.get('code')}: {body.get('message')}")
        return body.get("data", {})

    async def create_video(self, *, image: bytes, prompt: str, duration_s: int) -> VideoJob:
        import asyncio

        payload = {
            "model_name": settings.kling_model_name or "kling-v2-1",
            "image": base64.b64encode(image).decode(),
            "prompt": prompt,
            "duration": str(clamp_duration(duration_s)),
            "mode": "std",
        }
        last_err: KlingError | None = None
        for attempt in range(6):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    resp = await client.post(
                        f"{_BASE}{_CREATE}", json=payload, headers=self._headers()
                    )
            except httpx.RequestError as exc:
                raise KlingError(f"Falha de rede: {exc}", transient=True) from exc
            try:
                data = self._check(resp)
                return VideoJob(
                    provider_task_id=data.get("task_id", ""),
                    status=_map_status(data.get("task_status", "submitted")),
                )
            except KlingError as exc:
                last_err = exc
                if resp.status_code == 429 or "1303" in str(exc) or "parallel" in str(exc).lower():
                    await asyncio.sleep(15 * (attempt + 1))
                    continue
                raise
        assert last_err is not None
        raise last_err

    async def poll_video(self, *, provider_task_id: str) -> VideoJob:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    f"{_BASE}{_CREATE}/{provider_task_id}", headers=self._headers()
                )
        except httpx.RequestError as exc:
            raise KlingError(f"Falha de rede: {exc}", transient=True) from exc
        data = self._check(resp)
        status = _map_status(data.get("task_status", "processing"))
        video_url = None
        videos = (data.get("task_result") or {}).get("videos") or []
        if videos:
            video_url = videos[0].get("url")
        return VideoJob(provider_task_id=provider_task_id, status=status, video_url=video_url)

    async def create_and_download(
        self,
        *,
        image: bytes,
        prompt: str,
        duration_s: int,
        poll_interval_s: float | None = None,
        poll_timeout_s: float | None = None,
    ) -> bytes:
        """Cria, faz poll e baixa o MP4 do provedor."""
        import asyncio

        interval = (
            poll_interval_s if poll_interval_s is not None else settings.video_poll_interval_s
        )
        timeout = poll_timeout_s if poll_timeout_s is not None else settings.video_poll_timeout_s
        task = await self.create_video(image=image, prompt=prompt, duration_s=duration_s)
        deadline = time.monotonic() + timeout
        while task.status not in ("DONE", "FAILED"):
            if time.monotonic() > deadline:
                raise KlingError("Timeout aguardando Kling", transient=True)
            await asyncio.sleep(interval)
            task = await self.poll_video(provider_task_id=task.provider_task_id)
        if task.status == "FAILED" or not task.video_url:
            raise KlingError("Kling falhou ao gerar video", transient=True)
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.get(task.video_url)
            resp.raise_for_status()
            return resp.content
