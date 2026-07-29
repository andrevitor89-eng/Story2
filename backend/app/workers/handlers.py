from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app import storage
from app.ai import gemini
from app.models import Asset, AssetKind, Book, Job
from app.pdf.ebook import build_pdf
from app.stories.catalog import personalize, resolve_story

logger = logging.getLogger("handlers")


def _set_progress(db: Session, book: Book, progress: int, message: str) -> None:
    book.progress = progress
    book.progress_message = message
    db.commit()


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

    story = personalize(story_raw, book.child_name)
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