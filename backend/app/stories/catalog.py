from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

STORIES_DIR = Path(__file__).resolve().parent

AGE_BANDS: tuple[str, ...] = ("2-5", "5-9", "6-9", "9-12")


@lru_cache
def load_all() -> dict[str, dict]:
    stories: dict[str, dict] = {}
    for path in sorted(STORIES_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        stories[data["id"]] = data
    return stories


def parse_band(band: str) -> tuple[int, int]:
    lo, hi = band.split("-", 1)
    return int(lo), int(hi)


def suggest_age_band(age: int) -> str:
    """Escolhe a faixa mais especifica que contem a idade."""
    age = max(1, min(12, int(age)))
    matching: list[tuple[str, int, int]] = []
    for band in AGE_BANDS:
        lo, hi = parse_band(band)
        if lo <= age <= hi:
            matching.append((band, lo, hi))
    if not matching:
        return "2-5" if age < 2 else "9-12"
    matching.sort(key=lambda item: (item[2] - item[1], abs((item[1] + item[2]) / 2 - age)))
    return matching[0][0]


def list_stories(gender: str | None = None) -> list[dict]:
    items = []
    for story in load_all().values():
        if gender and gender != "unisex":
            if story["gender"] not in (gender, "unisex"):
                continue
        variants = story.get("variants") or {}
        sample_pages = next(iter(variants.values()), {}).get("pages") or story.get("pages") or []
        items.append(
            {
                "id": story["id"],
                "title": story["title"],
                "gender": story["gender"],
                "age_range": " / ".join(AGE_BANDS),
                "age_bands": list(AGE_BANDS),
                "theme": story["theme"],
                "page_count": len(sample_pages),
            }
        )
    return items


def get_story(story_id: str) -> dict | None:
    return load_all().get(story_id)


def resolve_story(
    story_id: str,
    age_band: str | None = None,
    child_age: int | None = None,
) -> dict | None:
    story = get_story(story_id)
    if story is None:
        return None

    band = age_band if age_band in AGE_BANDS else None
    if band is None and child_age is not None:
        band = suggest_age_band(child_age)
    if band is None:
        band = "5-9"

    variants = story.get("variants") or {}
    pages = (variants.get(band) or {}).get("pages")
    if not pages:
        # legado: historia sem variantes
        pages = story.get("pages") or []

    return {
        "id": story["id"],
        "title": story["title"],
        "gender": story["gender"],
        "theme": story["theme"],
        "age_range": band,
        "age_band": band,
        "pages": pages,
    }


def personalize(story: dict, child_name: str) -> dict:
    name = child_name.strip()
    return {
        **story,
        "title": story["title"].replace("{NOME}", name),
        "pages": [
            {
                **page,
                "text": page["text"].replace("{NOME}", name),
                "illustration_note": page["illustration_note"].replace("{NOME}", name),
            }
            for page in story["pages"]
        ],
    }
