from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from pathlib import Path

STORIES_DIR = Path(__file__).resolve().parent

AGE_BANDS: tuple[str, ...] = ("2-5", "5-9", "6-9", "9-12")

ALPHABET_STORY_IDS = frozenset(
    {
        "alfabeto_frutas_animais",
        "alfabeto_frutas",
        "alfabeto_animais",
    }
)
# Compat: id legado do livro misto
ALPHABET_STORY_ID = "alfabeto_frutas_animais"

_ACROSTIC_POOLS: dict[str, dict[str, list[str]]] = {
    "alfabeto_frutas": {
        "A": ["Abacaxi", "Amora", "Acerola"],
        "B": ["Banana", "Bacuri"],
        "C": ["Caju", "Cereja", "Coco"],
        "D": ["Damasco"],
        "E": ["Embauba"],
        "F": ["Figo", "Framboesa"],
        "G": ["Goiaba", "Graviola"],
        "H": ["Hibisco", "Hortela"],
        "I": ["Inga"],
        "J": ["Jabuticaba", "Jaca"],
        "K": ["Kiwi"],
        "L": ["Laranja", "Limao"],
        "M": ["Melancia", "Manga", "Morango"],
        "N": ["Noz", "Nespera"],
        "O": ["Oliva", "Oiti"],
        "P": ["Pessego", "Pera", "Pitanga"],
        "Q": ["Quarana"],
        "R": ["Roma"],
        "S": ["Seriguela", "Sapoti"],
        "T": ["Tangerina", "Tamarindo"],
        "U": ["Uva", "Uvaia"],
        "V": ["Vagem"],
        "W": ["Watermelon"],
        "X": ["Xixa"],
        "Y": ["Yacon"],
        "Z": ["Zimbro"],
    },
    "alfabeto_animais": {
        "A": ["Abelha", "Anta", "Arara"],
        "B": ["Baleia", "Boi", "Borboleta"],
        "C": ["Cachorro", "Cavalo", "Coelho"],
        "D": ["Dinossauro", "Dragao"],
        "E": ["Elefante", "Ema"],
        "F": ["Foca", "Formiga"],
        "G": ["Girafa", "Gato"],
        "H": ["Hipopotamo", "Hamster"],
        "I": ["Iguana"],
        "J": ["Jacare", "Joaninha"],
        "K": ["Koala"],
        "L": ["Leao", "Lagarta"],
        "M": ["Macaco", "Morcego"],
        "N": ["Nambu"],
        "O": ["Ovelha", "Onca", "Ourico"],
        "P": ["Pato", "Porco", "Panda"],
        "Q": ["Quati"],
        "R": ["Raposa", "Rato"],
        "S": ["Sapo", "Siri"],
        "T": ["Tigre", "Tartaruga", "Touro"],
        "U": ["Urso"],
        "V": ["Vaca", "Veado"],
        "W": ["Wombat"],
        "X": ["Xexeu"],
        "Y": ["Yorkshire"],
        "Z": ["Zebra", "Zangao"],
    },
}

# Livro misto: ordem classica do acrostico (animal/fruta conhecidos primeiro)
_ACROSTIC_POOLS["alfabeto_frutas_animais"] = {
    letter: list(
        dict.fromkeys(
            _ACROSTIC_POOLS["alfabeto_animais"].get(letter, [])
            + _ACROSTIC_POOLS["alfabeto_frutas"].get(letter, [])
        )
    )
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
}
_ACROSTIC_POOLS["alfabeto_frutas_animais"].update(
    {
        "A": ["Abacaxi", "Abelha", "Anta", "Amora"],
        "E": ["Elefante", "Ema", "Embauba"],
        "M": ["Macaco", "Melancia", "Morango"],
        "O": ["Onca", "Ourico", "Ovelha", "Oliva"],
        "T": ["Tigre", "Tartaruga", "Tangerina", "Tamarindo", "Touro"],
    }
)

_ACROSTIC_CLOSING = {
    "alfabeto_frutas": "Frutas do pomar, vamos conhecer!",
    "alfabeto_animais": "Animais do mundo, vamos conhecer!",
    "alfabeto_frutas_animais": "Frutas e animais, vamos conhecer!",
}


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


def _name_letters(name: str) -> list[str]:
    normalized = unicodedata.normalize("NFD", name.upper())
    return [ch for ch in normalized if "A" <= ch <= "Z"]


def _pick_acrostic_word(letter: str, used: dict[str, int], pool: dict[str, list[str]]) -> str:
    options = pool.get(letter) or [letter]
    idx = used.get(letter, 0)
    used[letter] = idx + 1
    return options[idx % len(options)]


def build_name_acrostic(
    child_name: str,
    *,
    age_band: str = "5-9",
    gender: str | None = None,
    story_id: str = ALPHABET_STORY_ID,
) -> tuple[str, str] | None:
    """Gera texto + nota de ilustracao do acrostico do nome (pagina 1)."""
    name = child_name.strip()
    letters = _name_letters(name)
    if not letters:
        return None

    pool = _ACROSTIC_POOLS.get(story_id) or _ACROSTIC_POOLS[ALPHABET_STORY_ID]
    used: dict[str, int] = {}
    pairs = [(letter, _pick_acrostic_word(letter, used, pool)) for letter in letters]
    if len(pairs) > 10:
        pairs = pairs[:10]

    if gender == "girl":
        meet = f"Conheça a {name}"
    elif gender == "boy":
        meet = f"Conheça o {name}"
    else:
        meet = f"Conheça {name}"

    closing = _ACROSTIC_CLOSING.get(story_id, _ACROSTIC_CLOSING[ALPHABET_STORY_ID])
    # Faixas do livro misto: P1 com ritmo diferente
    if story_id == ALPHABET_STORY_ID and age_band == "2-5":
        body = ", ".join(f"{letter} de {word}" for letter, word in pairs)
        text = f"{body}! {meet}, pronto pra aprender!"
    elif story_id == ALPHABET_STORY_ID and age_band == "6-9":
        body = "; ".join(f"{letter} de {word}" for letter, word in pairs)
        text = f"{body} — escute cada som. {meet}: cada letra do nome abre um som novo!"
    elif story_id == ALPHABET_STORY_ID and age_band == "9-12":
        body = ",\n".join(f"{letter} de {word}" for letter, word in pairs)
        text = (
            f"{body} —\n{meet}, pronto para ligar letra, som e mundo "
            "com frutas, animais e descobertas!"
        )
    else:
        body = ",\n".join(f"{letter} de {word}" for letter, word in pairs)
        text = f"{body} —\n{meet}, pronto pra aprender!\n{closing}"

    words = [word for _, word in pairs]
    if len(words) == 1:
        surround = words[0]
    elif len(words) == 2:
        surround = f"{words[0]} e {words[1]}"
    else:
        surround = ", ".join(words[:-1]) + f" e {words[-1]}"

    if story_id == "alfabeto_animais":
        place = "campo vivo"
    elif story_id == "alfabeto_frutas":
        place = "pomar colorido"
    else:
        place = "jardim alegre"

    note = (
        f"{name} no centro de um {place}, rodeado por {surround}; "
        "silhuetas decorativas grandes das letras do nome em madeira ou espuma "
        "(formas abstratas, sem texto legivel na arte); luz suave de manha."
    )
    return text, note


def personalize(
    story: dict,
    child_name: str,
    gender: str | None = None,
) -> dict:
    name = child_name.strip()
    pages = [
        {
            **page,
            "text": page["text"].replace("{NOME}", name),
            "illustration_note": page["illustration_note"].replace("{NOME}", name),
        }
        for page in story["pages"]
    ]

    story_id = str(story.get("id") or "")
    if story_id in ALPHABET_STORY_IDS and pages:
        acrostic = build_name_acrostic(
            name,
            age_band=str(story.get("age_band") or "5-9"),
            gender=gender,
            story_id=story_id,
        )
        if acrostic is not None:
            text, note = acrostic
            pages[0] = {**pages[0], "text": text, "illustration_note": note}

    return {
        **story,
        "title": story["title"].replace("{NOME}", name),
        "pages": pages,
    }
