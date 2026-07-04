"""Post-commit reset de .sdd/current-spec (Principio V).

Limpia las specs declaradas tras cada commit exitoso, dejando solo el header
de comentarios. Fuerza declaración explícita al inicio de la próxima iteración,
evitando reutilización silenciosa de una spec de sesión anterior.

Wiring: hook post-commit en .pre-commit-config.yaml (stages: [post-commit]).
Requiere instalación explícita: pre-commit install --hook-type post-commit.
Ver docs/SDD-ENFORCEMENT.md.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _find_repo_root() -> Path:
    start = Path.cwd()
    for directory in (start, *start.parents):
        if (directory / "CONSTITUTION.md").exists() or (
            directory / "specs" / "SPECS_REGISTRY.md"
        ).exists():
            return directory
    return start


def main() -> int:
    repo_root = _find_repo_root()
    path = repo_root / ".sdd" / "current-spec"
    if not path.exists():
        return 0
    lines = path.read_text(encoding="utf-8").splitlines()
    comments = [ln for ln in lines if ln.startswith("#")]
    path.write_text("\n".join(comments) + "\n", encoding="utf-8")
    print("SDD: .sdd/current-spec limpiado — declarar nueva spec antes de editar src/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
