from __future__ import annotations

CHARACTER_PROMPT = """Create a children's book character portrait from the reference photo.

Requirements:
- Keep the child's facial features, skin tone, hair color/style, and eye color faithful to the photo.
- Stylize as a warm illustrated children's book character (soft shading, friendly look).
- Full upper body portrait, facing camera, plain soft pastel background.
- No text, watermarks, or logos.
- Age approximately {age} years old, presenting as {gender_label}.
"""

SCENE_PROMPT = """Children's book illustration page.

Character consistency: reuse the attached character reference exactly (same face, hair, skin).
Child name: {name}
Scene description: {illustration_note}
Story text for mood/expression: {page_text}

Style: warm illustrated children's picture book, soft colors, whimsical, full-bleed scene.
Leave a soft lower band with slightly quieter detail so text can overlay later.
No text, letters, captions, watermarks, or logos in the image.
"""

GENDER_LABELS = {
    "boy": "a boy",
    "girl": "a girl",
    "unisex": "a child",
}
