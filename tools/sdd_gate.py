"""Interlock de autoria spec-first (Constitucion, Principio V).

Gate de enforcement *anterior* a que el codigo exista: bloquea la edicion/commit
de `src/` si no hay una spec vigente declarada en `.sdd/current-spec` (y editada
despues de declararla). La logica de decision (`decide`) es agnostica de
asistente; el modulo acepta tres transportes de entrada para ser invocable desde
cualquier wrapper, no solo Claude Code:

1. **argv**: `python tools/sdd_gate.py src/a.py src/b.py` — usado por `pre-commit`
   (capa git, tool-agnostica) y por cualquier hook que pase rutas como argumentos.
2. **env**: `SDD_GATE_FILE=src/a.py python tools/sdd_gate.py`.
3. **stdin JSON**: protocolo `PreToolUse` de Claude Code (retro-compatible) —
   lee el JSON del tool call por stdin.

Contrato de salida (comun a los tres): exit 0 = permitir, exit 2 = bloquear
(stderr lleva el motivo). El exit 2 sirve tanto a Claude (bloquea y devuelve el
motivo al asistente) como a `pre-commit`/git (cualquier exit != 0 aborta el
commit). Backstop a posteriori: `tools/check_traceability.py` en el pipeline.
Detalle del metodo en docs/SDD-ENFORCEMENT.md.

Wiring: hook `PreToolUse` en `.claude/settings.json` (stdin) y hook local en
`.pre-commit-config.yaml` (argv).
"""

from __future__ import annotations

import json
import os
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


def _payloads_from_paths(paths: list[str], cwd: str) -> list[dict[str, object]]:
    """Construye un payload por ruta (transporte argv/env)."""
    return [{"tool_input": {"file_path": p}, "cwd": cwd} for p in paths]


def _payloads_from_stdin() -> list[dict[str, object]]:
    """Lee el payload JSON del tool call de Claude Code por stdin."""
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}
    return [payload] if isinstance(payload, dict) else [{}]


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    cwd = os.getcwd()

    env_file = os.environ.get("SDD_GATE_FILE")
    if args:
        payloads = _payloads_from_paths(args, cwd)
    elif env_file:
        payloads = _payloads_from_paths([env_file], cwd)
    elif sys.stdin.isatty():
        # Sin rutas ni payload por stdin: nada que evaluar.
        return 0
    else:
        payloads = _payloads_from_stdin()

    reasons: list[str] = []
    for payload in payloads:
        allow, reason = decide(payload, _find_repo_root(payload))
        if not allow and reason:
            reasons.append(reason)
    if reasons:
        print("\n".join(reasons), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
