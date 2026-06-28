"""Generador de adaptadores de skills multi-asistente.

SSOT: cada skill se escribe una sola vez en `.agents/skills/<name>/SKILL.md`.
Ese formato (carpeta + SKILL.md con frontmatter `name` + `description`) lo leen
directo Codex (`.agents/skills/`) y Antigravity (`.agents/skills/`), con
auto-descubrimiento por `description`.

Desde esa fuente este script genera los dos adaptadores que divergen:

  - `.claude/skills/<name>/SKILL.md`  (mismo formato, otra carpeta; Claude usa
    ademas el campo `allowed-tools`).
  - `.opencode/command/<name>.md`     (opencode no tiene skill-dir ni
    auto-descubrimiento; usa un command con invocacion explicita `/name`).

No se usan symlinks: se generan archivos reales committeados, identicos en
Windows y Linux. Las lineas se escriben siempre con `\\n` para que `--check` sea
determinista entre SO (ver `.gitattributes`).

Uso:
    python tools/gen_skill_adapters.py            # escribe los adaptadores
    python tools/gen_skill_adapters.py --check    # falla si hay drift (CI/pipeline)

Exit code 0 si todo OK; 1 si en modo --check algun adaptador esta desincronizado.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / ".agents" / "skills"
CLAUDE_DIR = REPO_ROOT / ".claude" / "skills"
OPENCODE_DIR = REPO_ROOT / ".opencode" / "command"
PLAYBOOK_TEMPLATE = "docs/playbooks/{name}.md"

GENERATED_MARKER = (
    "<!-- GENERADO por tools/gen_skill_adapters.py desde "
    ".agents/skills/{name}/SKILL.md — NO EDITAR A MANO -->"
)

# Campos de frontmatter que solo existen para alimentar al generador; no deben
# filtrarse al SKILL.md de Claude (que se mantiene minimo: name/description/tools).
GENERATOR_ONLY_KEYS: frozenset[str] = frozenset({"opencode-description", "opencode-constraint"})


@dataclass(frozen=True)
class Skill:
    """Una skill parseada desde su SKILL.md fuente en `.agents/skills/`."""

    name: str
    frontmatter: dict[str, str]
    body: str

    @property
    def description(self) -> str:
        return self.frontmatter.get("description", "").strip()

    @property
    def opencode_description(self) -> str:
        return self.frontmatter.get("opencode-description", self.description).strip()

    @property
    def opencode_constraint(self) -> str:
        return self.frontmatter.get("opencode-constraint", "").strip()


def parse_skill(source: Path) -> Skill:
    """Parsea un SKILL.md con frontmatter plano (`key: value` por linea)."""
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{source}: falta frontmatter (primera linea debe ser '---')")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError(f"{source}: frontmatter sin cierre '---'") from exc

    frontmatter: dict[str, str] = {}
    for raw in lines[1:end]:
        if not raw.strip():
            continue
        if ":" not in raw:
            raise ValueError(f"{source}: linea de frontmatter sin ':' -> {raw!r}")
        key, value = raw.split(":", 1)
        frontmatter[key.strip()] = _unquote(value.strip())

    body = "\n".join(lines[end + 1 :]).strip("\n")
    name = frontmatter.get("name", source.parent.name).strip()
    if "description" not in frontmatter:
        raise ValueError(f"{source}: frontmatter sin 'description' (obligatorio)")
    return Skill(name=name, frontmatter=frontmatter, body=body)


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _needs_quote(value: str) -> bool:
    return value.startswith((" ", '"', "'")) or value.endswith(" ")


def render_claude(skill: Skill) -> str:
    """SKILL.md para Claude: frontmatter minimo + marcador + cuerpo agnostico."""
    keys = [k for k in ("name", "description", "allowed-tools") if k in skill.frontmatter]
    fm = "\n".join(f"{k}: {skill.frontmatter[k]}" for k in keys)
    marker = GENERATED_MARKER.format(name=skill.name)
    return f"---\n{fm}\n---\n\n{marker}\n\n{skill.body}\n"


def render_opencode(skill: Skill) -> str:
    """Command para opencode: solo `description` + cuerpo con `$ARGUMENTS`."""
    desc = skill.opencode_description
    desc_line = f'description: "{desc}"' if _needs_quote(desc) else f"description: {desc}"
    marker = GENERATED_MARKER.format(name=skill.name)
    playbook = PLAYBOOK_TEMPLATE.format(name=skill.name)
    lines = [
        f"---\n{desc_line}\n---",
        "",
        marker,
        "",
        f"Leé y seguí el playbook `{playbook}` (SSOT del procedimiento).",
        "Spec objetivo: `$ARGUMENTS` (si está vacío, usá la primera de `.sdd/current-spec`).",
    ]
    if skill.opencode_constraint:
        lines.append(skill.opencode_constraint)
    return "\n".join(lines) + "\n"


def _validate(skill: Skill) -> list[str]:
    errors: list[str] = []
    playbook = REPO_ROOT / PLAYBOOK_TEMPLATE.format(name=skill.name)
    if not playbook.exists():
        errors.append(f"{skill.name}: falta el playbook SSOT {playbook.relative_to(REPO_ROOT)}")
    unknown = set(skill.frontmatter) - {
        "name",
        "description",
        "allowed-tools",
        *GENERATOR_ONLY_KEYS,
    }
    if unknown:
        errors.append(f"{skill.name}: claves de frontmatter no reconocidas: {sorted(unknown)}")
    return errors


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _check(path: Path, content: str) -> bool:
    if not path.exists():
        return False
    return path.read_text(encoding="utf-8") == content


def main(argv: list[str]) -> int:
    check_mode = "--check" in argv
    if not SOURCE_DIR.is_dir():
        print(f"No existe {SOURCE_DIR.relative_to(REPO_ROOT)}; nada que generar.")
        return 0

    sources = sorted(SOURCE_DIR.glob("*/SKILL.md"))
    if not sources:
        print(f"Sin skills en {SOURCE_DIR.relative_to(REPO_ROOT)}.")
        return 0

    drift: list[str] = []
    problems: list[str] = []

    for source in sources:
        skill = parse_skill(source)
        problems.extend(_validate(skill))

        targets = {
            CLAUDE_DIR / skill.name / "SKILL.md": render_claude(skill),
            OPENCODE_DIR / f"{skill.name}.md": render_opencode(skill),
        }
        for target, content in targets.items():
            rel = target.relative_to(REPO_ROOT)
            if check_mode:
                if not _check(target, content):
                    drift.append(str(rel))
            else:
                _write(target, content)
                print(f"  generado  {rel}")

    if problems:
        print("\nProblemas de validacion:")
        for p in problems:
            print(f"  x {p}")
        return 1

    if check_mode:
        if drift:
            print("Adaptadores desincronizados (corre: python tools/gen_skill_adapters.py):")
            for d in drift:
                print(f"  x {d}")
            return 1
        print(f"Adaptadores de skills: sincronizados ({len(sources)} skill(s)).")
        return 0

    print(f"Adaptadores generados para {len(sources)} skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
