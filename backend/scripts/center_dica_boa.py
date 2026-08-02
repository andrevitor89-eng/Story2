# -*- coding: utf-8 -*-
"""Restaura dica-boa.png a partir do backup (retrato original).

O enquadramento na bolinha é feito via CSS (object-position + scale),
para mostrar o rosto inteiro centralizado.
"""
from __future__ import annotations

from pathlib import Path
import shutil

EX = Path(__file__).resolve().parents[2] / "apps" / "web" / "public" / "exemplos"
OUT = EX / "dica-boa.png"
SRC = EX / "dica-boa.bak.png"


def main() -> None:
    if not SRC.is_file():
        raise SystemExit(f"backup ausente: {SRC}")
    shutil.copyfile(SRC, OUT)
    print(f"ok restaurou {OUT.name} a partir de {SRC.name}")


if __name__ == "__main__":
    main()
