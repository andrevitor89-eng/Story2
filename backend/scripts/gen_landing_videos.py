# -*- coding: utf-8 -*-
"""Generate landing demo MP4s: Kling i2v + TTS + ffmpeg (Ken Burns fallback)."""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.ai.kling import KlingError, KlingVideoProvider, kling_configured
from app.media.assemble import (
    SceneClip,
    assemble_narrated_video,
    concat_mp4_clips,
    ffmpeg_available,
    mux_video_with_audio,
    probe_audio_duration_bytes,
)
from app.media.motion import build_motion_prompt, duration_for_audio_seconds
from app.media.tts import EdgeTtsProvider

DEMOS = [
    {
        "id": "mar",
        "file": "video-mar.mp4",
        "prefix": "mar",
        "theme": "mar",
        "narrations": [
            "No fundo do mar, a aventura comeca com um sorriso cheio de bolhas.",
            "Achou um recife de coral colorido, casinha dos peixes num cantinho escondido.",
            "E aqui que os peixinhos vivem em banco! Ela ri, bolinhas soltando.",
            "Um peixinho dourado nada perto e convida para explorar o oceano juntos.",
            "Entre algas suaves e conchas brilhantes, a coragem cresce a cada bracada.",
            "E assim, de volta a superficie, a historia do fundo do mar fica no coracao.",
        ],
    },
    {
        "id": "flor",
        "file": "video-flor.mp4",
        "prefix": "flor",
        "theme": "flor",
        "narrations": [
            "Na floresta encantada, as arvores sussurram um segredo de luz.",
            "Um vaga-lume pisca: plim, plim, boa noite!",
            "Eu falo com luz, e meu jeitinho! Mas hoje estou triste, sem brilho, sem cor.",
            "A floresta apagou! Me ajuda, por favor?",
            "Com um toque gentil, os vaga-lumes acendem de novo, um por um.",
            "E a noite fica magica: luzes dancando entre as folhas, amizade brilhando.",
        ],
    },
    {
        "id": "dino",
        "file": "video-dino.mp4",
        "prefix": "dino",
        "theme": "dino",
        "narrations": [
            "Matteo e seu amigo Dino brincam juntos todos os dias.",
            "Uma noite chove muito, muito, e o rio cresce e os deixa separados.",
            "Matteo e Dino querem voltar a brincar juntos e decidem construir uma ponte.",
            "Primeiro juntam folhas grandes e as colocam sobre o rio com muito cuidado.",
            "Mas o vento sopra... e leva todas as folhas voando.",
            "Matteo e Dino ficam pensando e tem uma ideia nova: usar gravetos!",
        ],
    },
    {
        "id": "circo",
        "file": "video-circo.mp4",
        "prefix": "circo",
        "theme": "circo",
        "narrations": [
            "Sob as luzes do circo, a plateia espera o show comecar.",
            "Um palhaco malabarista jogava bolinhas no ceu.",
            "Malabares treinam as maos! Contou ao pequeno espectador.",
            "Zup, zup! As esferas dancavam sem cair.",
            "E o bebe batia palminhas so de assistir, cheio de alegria.",
            "No final, aplausos e um brilho especial: a magia do circo das luzes.",
        ],
    },
]


async def build_one(
    demo: dict,
    exemplos: Path,
    out_dir: Path,
    tts: EdgeTtsProvider,
    *,
    use_kling: bool,
) -> Path:
    provider = KlingVideoProvider() if use_kling else None
    parts: list[bytes] = []
    theme = demo["theme"]

    for i, text in enumerate(demo["narrations"], start=1):
        img_path = exemplos / f"{demo['prefix']}-{i}.jpg"
        if not img_path.is_file():
            raise FileNotFoundError(f"Missing image: {img_path}")
        image = img_path.read_bytes()
        audio = await tts.synthesize(text, language="pt-BR")
        print(f"  scene {i}/6 TTS ok ({len(audio)} bytes)", flush=True)

        if use_kling and provider is not None:
            prompt = build_motion_prompt(text, theme=theme, story_id=theme)
            dur = duration_for_audio_seconds(probe_audio_duration_bytes(audio))
            print(f"  scene {i}/6 Kling {dur}s...", flush=True)
            try:
                video = await provider.create_and_download(
                    image=image, prompt=prompt, duration_s=dur
                )
                parts.append(mux_video_with_audio(video, audio, width=720, height=960))
                print(f"  scene {i}/6 Kling ok ({len(video)} bytes)", flush=True)
                continue
            except KlingError as exc:
                print(f"  scene {i}/6 Kling fail -> Ken Burns: {exc}", flush=True)
                msg = str(exc).lower()
                if "401" in msg or "access key" in msg or "ausentes" in msg:
                    use_kling = False
                    print("  Kling auth failed; remaining scenes use Ken Burns", flush=True)

        still = SceneClip(image_bytes=image, audio_bytes=audio, image_ext="jpg")
        parts.append(assemble_narrated_video([still], music_bytes=None, width=720, height=960))

    print("  concatenating...", flush=True)
    video = concat_mp4_clips(parts, music_bytes=None)
    out = out_dir / demo["file"]
    out.write_bytes(video)
    print(f"  wrote {out} ({len(video)} bytes)", flush=True)
    return out


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exemplos", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only", choices=["mar", "flor", "dino", "circo"], default=None)
    parser.add_argument(
        "--ken-burns",
        action="store_true",
        help="Force Ken Burns even if Kling keys are present",
    )
    args = parser.parse_args()

    if not ffmpeg_available():
        raise SystemExit("ffmpeg not found")

    use_kling = kling_configured() and not args.ken_burns
    print(f"mode={'kling' if use_kling else 'ken-burns'}", flush=True)

    args.out.mkdir(parents=True, exist_ok=True)
    tts = EdgeTtsProvider()
    demos = [d for d in DEMOS if args.only is None or d["id"] == args.only]
    for demo in demos:
        print(f"=== {demo['id']} ===", flush=True)
        await build_one(demo, args.exemplos, args.out, tts, use_kling=use_kling)
    print("DONE", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
