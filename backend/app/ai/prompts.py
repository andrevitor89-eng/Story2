from __future__ import annotations

CHARACTER_PROMPT = """Create a children's book character portrait from the reference photo.

Requirements:
- Keep the child's facial features, skin tone, hair color/style, and eye color faithful to the photo.
- Style: refined, painterly children's book illustration — soft realistic lighting, rich detail, premium picture-book quality.
- Avoid flat cartoon, clip-art, doodle, or simplistic drawing looks.
- Full upper body portrait, facing camera, plain soft pastel background.
- No text, watermarks, or logos.
- Age approximately {age} years old, presenting as {gender_label}.
"""

SCENE_PROMPT = """Children's book illustration page.

Character consistency: reuse the attached character reference exactly (same face, hair, skin).
Child name: {name}
Scene description: {illustration_note}
Story text for mood/expression: {page_text}

Style: refined painterly children's picture book — soft realistic lighting, rich detail, cohesive color grading, premium quality.
Avoid flat cartoon, doodle, clip-art, or rough sketch looks. Full-bleed scene.
Leave a soft lower band with slightly quieter detail so text can overlay later.
No text, letters, captions, watermarks, or logos in the image.
"""

ALPHABET_SCENE_PROMPT = """Children's book alphabet illustration page.

Character consistency: reuse the attached character reference exactly (same face, hair, skin).
Child name: {name}
Scene description: {illustration_note}
Story text for mood/expression: {page_text}

Style: refined painterly children's picture book — soft realistic lighting, rich detail, cohesive color grading, premium quality.
Avoid flat cartoon, doodle, clip-art, or rough sketch looks. Full-bleed scene.
Leave a soft lower band with slightly quieter detail so text can overlay later.

Alphabet-page rules:
- Feature clearly the fruits or animals named in the scene description.
- You MAY include large decorative letter silhouettes as environmental design (wood cutouts, soft foam shapes, garden topiary, balloon forms) matching the page's target letters.
- Letter forms must be abstract shapes only — never readable words, captions, labels, watermarks, or logos.
- Do not render the story text or any written words in the image.
"""

GENDER_LABELS = {
    "boy": "a boy",
    "girl": "a girl",
    "unisex": "a child",
}
