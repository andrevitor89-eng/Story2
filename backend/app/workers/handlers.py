from __future__ import annotations

import json
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import storage
from app.ai import gemini
from app.models import Asset, AssetKind, Book, BookStatus, Job, UserVoice
from app.pdf.ebook import build_pdf
from app.stories.catalog import personalize, resolve_story

logger = logging.getLogger("handlers")


def _set_progress(db: Session, book: Book, progress: int, message: str) -> None:
    book.progress = progress
    book.progress_message = message
    db.commit()


def _resolve_elevenlabs_voice_id(
    db: Session, user_id: uuid.UUID, job_payload: str | None
) -> str | None:
    """Resolve voice_id interno do job (ou default do usuário) para ID ElevenLabs."""
    voice_uuid: uuid.UUID | None = None
    if job_payload:
        try:
            data = json.loads(job_payload)
            raw = (data or {}).get("voice_id")
            if raw:
                voice_uuid = uuid.UUID(str(raw))
        except (json.JSONDecodeError, ValueError, TypeError):
            voice_uuid = None
    if voice_uuid is not None:
        voice = db.get(UserVoice, voice_uuid)
        if voice and voice.user_id == user_id:
            return voice.elevenlabs_voice_id
    default = db.scalar(
        select(UserVoice).where(UserVoice.user_id == user_id, UserVoice.is_default.is_(True))
    )
    if default:
        return default.elevenlabs_voice_id
    return None


async def process_generate_job(db: Session, job: Job) -> None:
    book = db.get(Book, job.book_id)
    if book is None:
        raise RuntimeError("Livro nao encontrado")
    if not book.story_id:
        raise RuntimeError("Historia nao selecionada")

    story_raw = resolve_story(book.story_id, age_band=book.age_band, child_age=book.child_age)
    if story_raw is None:
        raise RuntimeError(f"Historia invalida: {book.story_id}")

    if not book.age_band:
        book.age_band = story_raw.get("age_band")
        db.commit()

    story = personalize(story_raw, book.child_name, gender=book.child_gender)
    photo = next((a for a in book.assets if a.kind == AssetKind.photo), None)
    if photo is None:
        raise RuntimeError("Foto ausente")

    photo_bytes = storage.get_bytes(photo.storage_key)
    _set_progress(db, book, 5, "Criando personagem...")

    character_bytes = await gemini.generate_character(
        photo_bytes,
        name=book.child_name,
        age=book.child_age,
        gender=book.child_gender,
        photo_mime=photo.mime_type,
    )
    char_key = f"books/{book.id}/character/{uuid.uuid4().hex}.png"
    storage.put_bytes(char_key, character_bytes, "image/png")
    db.add(
        Asset(
            book_id=book.id,
            kind=AssetKind.character,
            storage_key=char_key,
            mime_type="image/png",
        )
    )
    db.commit()

    page_images: list[tuple[bytes, str]] = []
    total = len(story["pages"])
    for i, page in enumerate(story["pages"]):
        pct = 10 + int(80 * (i / max(total, 1)))
        _set_progress(db, book, pct, f"Ilustrando pagina {page['page']} de {total}...")
        scene = await gemini.generate_scene(
            character_bytes,
            name=book.child_name,
            page=page["page"],
            page_text=page["text"],
            illustration_note=page["illustration_note"],
            story_id=book.story_id,
        )
        page_key = f"books/{book.id}/pages/{page['page']:02d}_{uuid.uuid4().hex}.png"
        storage.put_bytes(page_key, scene, "image/png")
        db.add(
            Asset(
                book_id=book.id,
                kind=AssetKind.page,
                storage_key=page_key,
                mime_type="image/png",
                page_number=page["page"],
            )
        )
        db.commit()
        page_images.append((scene, page["text"]))

    _set_progress(db, book, 92, "Montando PDF...")
    cover = page_images[0][0] if page_images else character_bytes
    pdf_bytes = build_pdf(
        title=story["title"],
        child_name=book.child_name,
        cover_image=cover,
        pages=page_images,
    )
    pdf_key = f"books/{book.id}/ebook/{uuid.uuid4().hex}.pdf"
    storage.put_bytes(pdf_key, pdf_bytes, "application/pdf")
    db.add(
        Asset(
            book_id=book.id,
            kind=AssetKind.pdf,
            storage_key=pdf_key,
            mime_type="application/pdf",
        )
    )
    db.commit()
    logger.info("Book %s ready (%s pages)", book.id, total)


def _offline_animation_gif(label: str) -> bytes:
    from io import BytesIO

    from PIL import Image, ImageDraw, ImageFont

    frames = []
    colors = [
        ((221, 236, 255), (255, 250, 240)),
        ((255, 237, 222), (255, 248, 244)),
        ((234, 245, 228), (250, 250, 245)),
    ]
    try:
        font = ImageFont.truetype("arial.ttf", 38)
    except Exception:
        font = ImageFont.load_default()

    for idx, (bg, panel) in enumerate(colors):
        frame = Image.new("RGB", (960, 540), bg)
        draw = ImageDraw.Draw(frame)
        draw.rounded_rectangle((40, 40, 920, 500), radius=36, fill=panel)
        draw.ellipse((110 + idx * 30, 135, 350 + idx * 30, 375), fill=(246, 214, 170))
        draw.text((560, 205), label[:24], fill=(34, 42, 54), font=font)
        draw.text((560, 255), f"Cena {idx + 1}", fill=(84, 98, 112), font=font)
        frames.append(frame)

    buf = BytesIO()
    frames[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=700,
        loop=0,
        disposal=2,
    )
    return buf.getvalue()


def _video_reference_bytes(book: Book) -> bytes:
    character = next((a for a in book.assets if a.kind == AssetKind.character), None)
    if character:
        return storage.get_bytes(character.storage_key)
    pages = sorted(
        [a for a in book.assets if a.kind == AssetKind.page],
        key=lambda a: a.page_number or 0,
    )
    if pages:
        return storage.get_bytes(pages[0].storage_key)
    raise RuntimeError("Gere o ebook antes (personagem/paginas ausentes)")


async def process_video_job(db: Session, job: Job) -> None:
    """Animacao curta via Kling (ou GIF offline)."""
    import asyncio
    import time

    from app.ai.kling import KlingVideoProvider, clamp_duration, use_video_offline
    from app.config import settings

    book = db.get(Book, job.book_id)
    if book is None:
        raise RuntimeError("Livro nao encontrado")
    if book.status != BookStatus.ready and not any(
        a.kind in (AssetKind.character, AssetKind.page) for a in book.assets
    ):
        raise RuntimeError("Ebook precisa estar pronto para gerar animacao")

    _set_progress(db, book, 10, "Preparando animacao...")
    image = _video_reference_bytes(book)
    prompt = f"Anime suavemente o personagem infantil {book.child_name} com movimento expressivo e alegre."

    # Remove animacao anterior
    for old in [a for a in book.assets if a.kind == AssetKind.video]:
        db.delete(old)
    book.video_url = None
    db.commit()

    if use_video_offline():
        _set_progress(db, book, 60, "Gerando animacao offline...")
        data = _offline_animation_gif(f"Animacao {book.child_name}"[:28])
        key = f"books/{book.id}/video/{uuid.uuid4().hex}.gif"
        storage.put_bytes(key, data, "image/gif")
        db.add(
            Asset(
                book_id=book.id,
                kind=AssetKind.video,
                storage_key=key,
                mime_type="image/gif",
            )
        )
        book.video_url = key
        _set_progress(db, book, 100, "Animacao pronta!")
        db.commit()
        return

    provider = KlingVideoProvider()
    duration_s = clamp_duration(settings.default_video_duration_s)
    _set_progress(db, book, 20, "Enviando para Kling...")
    task = await provider.create_video(image=image, prompt=prompt, duration_s=duration_s)

    deadline = time.monotonic() + settings.video_poll_timeout_s
    while task.status not in ("DONE", "FAILED"):
        if time.monotonic() > deadline:
            raise RuntimeError("Timeout aguardando animacao")
        await asyncio.sleep(settings.video_poll_interval_s)
        _set_progress(db, book, 50, "Renderizando animacao...")
        task = await provider.poll_video(provider_task_id=task.provider_task_id)

    if task.status == "FAILED" or not task.video_url:
        raise RuntimeError("Provedor de video falhou")

    _set_progress(db, book, 80, "Baixando animacao...")
    import httpx

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.get(task.video_url)
        resp.raise_for_status()
        video_bytes = resp.content

    key = f"books/{book.id}/video/{uuid.uuid4().hex}.mp4"
    storage.put_bytes(key, video_bytes, "video/mp4")
    db.add(
        Asset(
            book_id=book.id,
            kind=AssetKind.video,
            storage_key=key,
            mime_type="video/mp4",
        )
    )
    book.video_url = key
    _set_progress(db, book, 100, "Animacao pronta!")
    db.commit()
    logger.info("Book %s animation ready", book.id)


def _build_deterministic_storyboard(book: Book) -> dict:
    """Roteiro a partir das paginas personalizadas do catalogo (sem LLM)."""
    from app.media.motion import build_motion_prompt

    story_raw = resolve_story(book.story_id or "", age_band=book.age_band, child_age=book.child_age)
    if story_raw is None:
        raise RuntimeError("Historia invalida para storyboard")
    story = personalize(story_raw, book.child_name, gender=book.child_gender)
    story_id = (book.story_id or story.get("id") or "").lower()
    theme = (story.get("theme") or story_id).lower()
    scenes = []
    for page in story["pages"][:6]:
        text = (page.get("text") or "").strip()
        note = (page.get("illustration_note") or "").strip()
        scenes.append(
            {
                "n": int(page.get("page") or len(scenes) + 1),
                "narration": text or f"Cena {page.get('page')}.",
                "setting": note[:200],
                "action": note[:200],
                "camera": "plano medio",
                "mood": "alegre",
                "duration_s": 5,
                "image_prompt": note,
                "video_prompt": build_motion_prompt(
                    note, theme=theme, story_id=story_id
                ),
            }
        )
    return {
        "version": 1,
        "title": story.get("title") or f"Historia de {book.child_name}",
        "language": "pt-BR",
        "theme": theme,
        "story_id": story_id,
        "scenes": scenes,
        "total_duration_s": sum(s["duration_s"] for s in scenes),
    }


async def process_narrated_video_job(db: Session, job: Job) -> None:
    """Video narrado: Kling por cena + TTS + ffmpeg (Ken Burns se sem Kling)."""
    from pathlib import Path

    from app.ai.kling import KlingError, KlingVideoProvider, kling_configured
    from app.media.assemble import (
        AssembleError,
        SceneClip,
        assemble_narrated_video,
        assemble_slideshow_gif,
        concat_mp4_clips,
        ffmpeg_available,
        mux_video_with_audio,
        probe_audio_duration_bytes,
    )
    from app.media.motion import build_motion_prompt, duration_for_audio_seconds
    from app.media.tts import TtsError, get_tts_provider

    book = db.get(Book, job.book_id)
    if book is None:
        raise RuntimeError("Livro nao encontrado")
    pages = sorted(
        [a for a in book.assets if a.kind == AssetKind.page],
        key=lambda a: a.page_number or 0,
    )
    if not pages:
        raise RuntimeError("Paginas ilustradas ausentes")

    _set_progress(db, book, 5, "Montando roteiro...")
    sb = _build_deterministic_storyboard(book)
    sb_key = f"books/{book.id}/storyboard/{uuid.uuid4().hex}.json"
    storage.put_bytes(
        sb_key, json.dumps(sb, ensure_ascii=False, indent=2).encode("utf-8"), "application/json"
    )
    for old in [a for a in book.assets if a.kind == AssetKind.storyboard]:
        db.delete(old)
    db.add(
        Asset(
            book_id=book.id,
            kind=AssetKind.storyboard,
            storage_key=sb_key,
            mime_type="application/json",
        )
    )
    db.commit()

    el_voice_id = _resolve_elevenlabs_voice_id(db, book.user_id, job.payload)
    tts = get_tts_provider(voice_id=el_voice_id)
    theme = sb.get("theme") or ""
    story_id = sb.get("story_id") or book.story_id or ""
    use_kling = kling_configured() and ffmpeg_available()
    scenes = sb["scenes"][:6]
    total = max(len(scenes), 1)
    provider = KlingVideoProvider() if use_kling else None
    ordered_parts: list[bytes] = []
    gif_stills: list[SceneClip] = []
    kling_ok = 0

    for i, sc in enumerate(scenes):
        n = int(sc.get("n") or i + 1)
        page_asset = next((p for p in pages if p.page_number == n), None)
        if page_asset is None:
            page_asset = pages[min(i, len(pages) - 1)]
        image = storage.get_bytes(page_asset.storage_key)
        narration = (sc.get("narration") or "").strip() or f"Cena {n}."
        _set_progress(db, book, 10 + int(70 * (i / total)), f"Narrando cena {i + 1} de {total}...")
        try:
            audio = await tts.synthesize(narration, language="pt-BR")
        except TtsError:
            audio = b""

        still = SceneClip(image_bytes=image, audio_bytes=audio, image_ext="png")
        gif_stills.append(still)

        if use_kling and provider is not None and audio:
            prompt = sc.get("video_prompt") or build_motion_prompt(
                sc.get("image_prompt") or narration,
                theme=theme,
                story_id=story_id,
            )
            audio_s = probe_audio_duration_bytes(audio)
            dur = duration_for_audio_seconds(audio_s)
            _set_progress(
                db, book, 10 + int(70 * ((i + 0.4) / total)), f"Animando cena {i + 1} de {total}..."
            )
            try:
                video_bytes = await provider.create_and_download(
                    image=image, prompt=prompt, duration_s=dur
                )
                ordered_parts.append(
                    mux_video_with_audio(video_bytes, audio, width=720, height=960)
                )
                kling_ok += 1
                continue
            except KlingError as exc:
                logger.warning("Kling cena %s falhou, fallback Ken Burns: %s", n, exc)
                # Auth/config permanente: nao insistir nas cenas seguintes
                msg = str(exc).lower()
                if "401" in msg or "access key" in msg or "ausentes" in msg:
                    use_kling = False

        if audio and ffmpeg_available():
            ordered_parts.append(
                assemble_narrated_video([still], music_bytes=None, width=720, height=960)
            )

    music = None
    music_path = Path(__file__).resolve().parent.parent / "assets" / "audio" / "bed.mp3"
    if music_path.is_file():
        music = music_path.read_bytes()

    _set_progress(db, book, 85, "Montando video...")
    try:
        if ordered_parts:
            video_bytes = concat_mp4_clips(ordered_parts, music_bytes=music)
            ext, mime = "mp4", "video/mp4"
        else:
            video_bytes = assemble_slideshow_gif(gif_stills)
            ext, mime = "gif", "image/gif"
    except AssembleError:
        video_bytes = assemble_slideshow_gif(gif_stills)
        ext, mime = "gif", "image/gif"

    for old in [a for a in book.assets if a.kind == AssetKind.narrated_video]:
        db.delete(old)
    key = f"books/{book.id}/narrated/{uuid.uuid4().hex}.{ext}"
    storage.put_bytes(key, video_bytes, mime)
    db.add(
        Asset(
            book_id=book.id,
            kind=AssetKind.narrated_video,
            storage_key=key,
            mime_type=mime,
        )
    )
    book.narrated_video_url = key
    _set_progress(db, book, 100, "Video narrado pronto!")
    db.commit()
    logger.info(
        "Book %s narrated video ready (%s scenes kling=%s)", book.id, len(scenes), kling_ok
    )
