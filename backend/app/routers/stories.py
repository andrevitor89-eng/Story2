from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas import StoryDetail, StorySummary
from app.stories.catalog import AGE_BANDS, get_story, list_stories, resolve_story, suggest_age_band

router = APIRouter(prefix="/v1/stories", tags=["stories"])


@router.get("/meta/age-bands")
def age_bands(child_age: int | None = Query(default=None)) -> dict:
    suggested = suggest_age_band(child_age) if child_age is not None else None
    return {"age_bands": list(AGE_BANDS), "suggested_age_band": suggested}


@router.get("", response_model=list[StorySummary])
def stories(gender: str | None = Query(default=None)) -> list[dict]:
    return list_stories(gender=gender)


@router.get("/{story_id}", response_model=StoryDetail)
def story_detail(
    story_id: str,
    age_band: str | None = Query(default=None),
    child_age: int | None = Query(default=None),
) -> dict:
    story = resolve_story(story_id, age_band=age_band, child_age=child_age)
    if story is None or get_story(story_id) is None:
        raise HTTPException(status_code=404, detail="Historia nao encontrada")
    return {
        "id": story["id"],
        "title": story["title"],
        "gender": story["gender"],
        "age_range": story["age_range"],
        "age_bands": list(AGE_BANDS),
        "age_band": story["age_band"],
        "theme": story["theme"],
        "page_count": len(story["pages"]),
        "pages": story["pages"],
    }
