"""Instala los hooks git de pre-commit si faltan (idempotente).

La capa git del enforcement (gate sdd, linters en commit, sdd-reset post-commit)
requiere `pre-commit install --hook-type pre-commit --hook-type post-commit`,
que git no puede auto-ejecutar al clonar (por diseno, seguridad). Este script
es el paso 0 de `tools/pipeline_local.sh`: verifica primero si los hooks ya
estan instalados y solo instala los que faltan — nunca toca los existentes.

Casos borde:
- Sin repositorio git: no-op con aviso (el gate SDD funciona sin git por diseno).
- `pre_commit` no importable: falla con instruccion accionable (es dependencia
  de desarrollo declarada; sin ella la capa git queda caida en silencio).

Usa `sys.executable -m pre_commit` (no el binario `pre-commit`), que funciona
aunque los scripts de pip --user no esten en el PATH.
Ver docs/SDD-ENFORCEMENT.md.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_HOOK_TYPES = ("pre-commit", "post-commit")


def _find_repo_root() -> Path:
    start = Path.cwd()
    for directory in (start, *start.parents):
        if (directory / "CONSTITUTION.md").exists() or (
            directory / "specs" / "SPECS_REGISTRY.md"
        ).exists():
            return directory
    return start


def _hooks_dir(repo_root: Path) -> Path | None:
    """Directorio de hooks resuelto por git (cubre worktrees y core.hooksPath)."""
    result = subprocess.run(
        ["git", "rev-parse", "--git-path", "hooks"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    path = Path(result.stdout.strip())
    return path if path.is_absolute() else repo_root / path


def main() -> int:
    repo_root = _find_repo_root()
    if not (repo_root / ".git").exists():
        print("bootstrap-hooks: sin repositorio git — nada que instalar (no-op).")
        return 0

    hooks_dir = _hooks_dir(repo_root)
    if hooks_dir is None:
        print("bootstrap-hooks: git no pudo resolver el directorio de hooks.")
        return 1

    missing = [hook for hook in _HOOK_TYPES if not (hooks_dir / hook).exists()]
    if not missing:
        print("bootstrap-hooks: hooks ya instalados (pre-commit, post-commit) — sin cambios.")
        return 0

    try:
        import pre_commit  # noqa: F401  # solo verifica disponibilidad
    except ImportError:
        print(
            "bootstrap-hooks: falta el paquete 'pre-commit' — instalalo con "
            "`pip install pre-commit` y reintentá.",
            file=sys.stderr,
        )
        return 1

    command = [sys.executable, "-m", "pre_commit", "install"]
    for hook_type in _HOOK_TYPES:
        command += ["--hook-type", hook_type]
    print(f"bootstrap-hooks: faltan {', '.join(missing)} — instalando...", flush=True)
    return subprocess.run(command, cwd=repo_root).returncode


if __name__ == "__main__":
    sys.exit(main())
