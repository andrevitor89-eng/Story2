from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import storage
from app.db import get_db
from app.models import Asset, AssetKind, Book, BookStatus, Job, User
from app.schemas import BookCreate, BookOut, GenerateRequest, JobOut
from app.security import get_current_user, get_current_user_flexible
from app.services.jobs import enqueue_generate
from app.stories.catalog import AGE_BANDS, get_story, suggest_age_band

router = APIRouter(prefix="/v1/books", tags=["books"])

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}


def _book_out(book: Book) -> BookOut:
    has_photo = any(a.kind == AssetKind.photo for a in book.assets)
    pdf = next((a for a in book.assets if a.kind == AssetKind.pdf), None)
    pages = sorted(
        [a for a in book.assets if a.kind == AssetKind.page],
        key=lambda a: a.page_number or 0,
    )
    # URLs via API proxy (evita SigV4 quebrado do MinIO no navegador)
    return BookOut(
        id=book.id,
        child_name=book.child_name,
        child_age=book.child_age,
        child_gender=book.child_gender,
        story_id=book.story_id,
        age_band=book.age_band,
        suggested_age_band=suggest_age_band(book.child_age),
        status=book.status.value,
        progress=book.progress,
        progress_message=book.progress_message,
        error_message=book.error_message,
        created_at=book.created_at,
        has_photo=has_photo,
        pdf_url=f"/v1/books/{book.id}/pdf" if pdf else None,
        page_urls=[f"/v1/books/{book.id}/pages/{p.page_number}" for p in pages],
    )


def _get_owned(db: Session, book_id: uuid.UUID, user: User) -> Book:
    book = db.get(Book, book_id)
    if book is None or book.user_id != user.id:
        raise HTTPException(status_code=404, detail="Livro nao encontrado")
    return book


@router.post("", response_model=BookOut, status_code=status.HTTP_201_CREATED)
def create_book(
    body: BookCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BookOut:
    book = Book(
        user_id=user.id,
        child_name=body.child_name.strip(),
        child_age=body.child_age,
        child_gender=body.child_gender,
        status=BookStatus.draft,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return _book_out(book)


@router.get("", response_model=list[BookOut])
def list_books(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BookOut]:
    books = (
        db.execute(select(Book).where(Book.user_id == user.id).order_by(Book.created_at.desc()))
        .scalars()
        .all()
    )
    return [_book_out(b) for b in books]


@router.get("/{book_id}", response_model=BookOut)
def get_book(
    book_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BookOut:
    return _book_out(_get_owned(db, book_id, user))


@router.get("/{book_id}/pages/{page_number}")
def get_page_image(
    book_id: uuid.UUID,
    page_number: int,
    user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
) -> Response:
    book = _get_owned(db, book_id, user)
    asset = next(
        (
            a
            for a in book.assets
            if a.kind == AssetKind.page and a.page_number == page_number
        ),
        None,
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Pagina nao encontrada")
    data = storage.get_bytes(asset.storage_key)
    return Response(content=data, media_type=asset.mime_type, headers={"Cache-Control": "private, max-age=3600"})


@router.get("/{book_id}/pdf")
def get_pdf(
    book_id: uuid.UUID,
    user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
) -> Response:
    book = _get_owned(db, book_id, user)
    asset = next((a for a in book.assets if a.kind == AssetKind.pdf), None)
    if asset is None:
        raise HTTPException(status_code=404, detail="PDF nao encontrado")
    data = storage.get_bytes(asset.storage_key)
    filename = f"livro-{book.child_name}.pdf".replace(" ", "-")
    return Response(
        content=data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "private, max-age=3600",
        },
    )


@router.post("/{book_id}/photo", response_model=BookOut)
async def upload_photo(
    book_id: uuid.UUID,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BookOut:
    book = _get_owned(db, book_id, user)
    if book.status not in (BookStatus.draft, BookStatus.failed):
        raise HTTPException(status_code=400, detail="Nao e possivel alterar a foto neste estagio")

    mime = file.content_type or "image/jpeg"
    if mime not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail="Envie JPEG, PNG ou WebP")

    data = await file.read()
    if len(data) > 12 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Foto muito grande (max. 12MB)")

    for old in [a for a in book.assets if a.kind == AssetKind.photo]:
        db.delete(old)

    key = f"books/{book.id}/photo/{uuid.uuid4().hex}"
    storage.put_bytes(key, data, mime)
    db.add(Asset(book_id=book.id, kind=AssetKind.photo, storage_key=key, mime_type=mime))
    db.commit()
    db.expire(book)
    book = _get_owned(db, book_id, user)
    return _book_out(book)


@router.post("/{book_id}/generate", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def generate_book(
    book_id: uuid.UUID,
    body: GenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobOut:
    book = _get_owned(db, book_id, user)
    if book.status in (BookStatus.queued, BookStatus.generating):
        raise HTTPException(status_code=400, detail="Geracao ja em andamento")

    if get_story(body.story_id) is None:
        raise HTTPException(status_code=404, detail="Historia nao encontrada")

    if body.age_band_mode == "manual":
        if body.age_band not in AGE_BANDS:
            raise HTTPException(status_code=400, detail="Faixa etaria invalida")
        age_band = body.age_band
    else:
        age_band = body.age_band if body.age_band in AGE_BANDS else suggest_age_band(book.child_age)

    if not any(a.kind == AssetKind.photo for a in book.assets):
        raise HTTPException(status_code=400, detail="Envie a foto da crianca antes de gerar")

    for asset in list(book.assets):
        if asset.kind != AssetKind.photo:
            db.delete(asset)

    book.story_id = body.story_id
    book.age_band = age_band
    return enqueue_generate(db, book)


@router.get("/{book_id}/jobs", response_model=list[JobOut])
def book_jobs(
    book_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Job]:
    book = _get_owned(db, book_id, user)
    return sorted(book.jobs, key=lambda j: j.created_at, reverse=True)
