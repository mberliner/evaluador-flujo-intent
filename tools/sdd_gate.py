"""Interlock de autoria spec-first (Constitucion, Principio V).

Hook `PreToolUse` de Claude Code: se invoca ANTES de un Edit/Write y bloquea la
edicion de `src/` si no hay una spec vigente declarada en `.sdd/current-spec`.
Es la unica capa de enforcement *anterior* a que el codigo exista (el repo no
usa git, asi que no hay pre-commit). Solo gobierna la ruta del asistente; el
backstop para edicion por fuera es `tools/check_traceability.py` en el pipeline.

Protocolo: lee el JSON del tool call por stdin; exit 0 = permitir, exit 2 =
bloquear (stderr se devuelve al asistente como motivo). Detalle del metodo en
docs/SDD-ENFORCEMENT.md.

Uso (configurado como hook en .claude/settings.json):
    python tools/sdd_gate.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _find_repo_root(payload: dict[str, object]) -> Path:
    cwd = payload.get("cwd")
    start = Path(str(cwd)) if isinstance(cwd, str) and cwd else Path.cwd()
    for directory in (start, *start.parents):
        if (directory / "CONSTITUTION.md").exists() or (
            directory / "specs" / "SPECS_REGISTRY.md"
        ).exists():
            return directory
    return start


def _is_src_path(file_path: str, repo_root: Path) -> bool:
    candidate = Path(file_path)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    try:
        rel = candidate.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return False
    return len(rel.parts) > 0 and rel.parts[0] == "src"


def _declared_specs(repo_root: Path) -> list[str]:
    path = repo_root / ".sdd" / "current-spec"
    if not path.exists():
        return []
    specs: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            specs.append(line)
    return specs


def _spec_is_valid(spec_id: str, repo_root: Path) -> bool:
    spec_file = repo_root / "specs" / f"{spec_id}.md"
    if not spec_file.exists():
        return False
    registry = repo_root / "specs" / "SPECS_REGISTRY.md"
    if not registry.exists():
        return False
    return spec_id in registry.read_text(encoding="utf-8")


def _any_spec_touched_after_declaration(declared: list[str], repo_root: Path) -> bool:
    """True si al menos una spec declarada fue editada después de .sdd/current-spec."""
    decl_path = repo_root / ".sdd" / "current-spec"
    if not decl_path.exists():
        return False
    decl_mtime = decl_path.stat().st_mtime
    for spec_id in declared:
        spec_file = repo_root / "specs" / f"{spec_id}.md"
        if spec_file.exists() and spec_file.stat().st_mtime > decl_mtime:
            return True
    return False


def decide(payload: dict[str, object], repo_root: Path) -> tuple[bool, str]:
    """Devuelve (permitir, motivo). Motivo solo es relevante cuando se bloquea."""
    tool_input = payload.get("tool_input")
    tinput = tool_input if isinstance(tool_input, dict) else {}
    raw_path = tinput.get("file_path") or tinput.get("path") or ""
    file_path = str(raw_path)
    if not file_path or not _is_src_path(file_path, repo_root):
        return True, ""

    declared = _declared_specs(repo_root)
    if not declared:
        return False, (
            "Edicion de src/ bloqueada (Principio V): no hay spec vigente declarada. "
            "Declara la SPEC-NNN en .sdd/current-spec (o creala primero). "
            "Ver docs/SDD-ENFORCEMENT.md."
        )
    invalid = [s for s in declared if not _spec_is_valid(s, repo_root)]
    if invalid:
        return False, (
            "Edicion de src/ bloqueada (Principio V): spec(s) declarada(s) invalida(s): "
            f"{', '.join(invalid)}. Deben existir en specs/ y estar registradas en "
            "SPECS_REGISTRY.md."
        )

    if not _any_spec_touched_after_declaration(declared, repo_root):
        return False, (
            "Edicion de src/ bloqueada (Principio V): la(s) spec(s) declarada(s) "
            f"({', '.join(declared)}) no fueron editadas despues de declararlas en "
            ".sdd/current-spec. Edita la spec primero (agrega/actualiza el FR) y "
            "luego edita src/."
        )
    return True, ""


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    allow, reason = decide(payload, _find_repo_root(payload))
    if allow:
        return 0
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
