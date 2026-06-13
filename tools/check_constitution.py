"""Verificador de integridad de la constitucion.

Implementa el Constitution Check de CONSTITUTION.md: confirma que cada
principio referencia SSOTs que existen, que su enforcement automatico esta
cableado en el pipeline, y que la linea de version esta bien formada.
Imprime los principios para darles visibilidad en cada corrida.

Uso:
    python tools/check_constitution.py CONSTITUTION.md

Exit code 0 si todo OK, 1 si hay referencia rota o version malformada.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Herramientas cuyo enforcement debe estar cableado en el pipeline local.
# Si un principio declara una de estas como Enforcement, debe aparecer en
# tools/pipeline_local.sh. El resto del enforcement (tests puntuales, review,
# .gitignore) no se exige como paso del pipeline.
PIPELINE_TOOLS: frozenset[str] = frozenset(
    {
        "check_naming.py",
        "check_traceability.py",
        "lint-imports",
    }
)

_BACKTICK = re.compile(r"`([^`]+)`")
_SEMVER = re.compile(r"\b\d+\.\d+\.\d+\b")
_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


class _Principle:
    def __init__(self, title: str) -> None:
        self.title = title
        self.enforcement: list[str] = []
        self.detalle: list[str] = []


def _parse(text: str) -> tuple[str | None, list[_Principle]]:
    """Devuelve (linea_version, principios)."""
    version_line: str | None = None
    principles: list[_Principle] = []
    section: str | None = None
    current: _Principle | None = None

    for raw in text.splitlines():
        line = raw.strip()

        if version_line is None and line.startswith("**Versión:**"):
            version_line = line

        if line.startswith("## "):
            section = line[3:].strip().lower()
            current = None
            continue

        if section == "principios":
            if line.startswith("### "):
                current = _Principle(line[4:].strip())
                principles.append(current)
            elif current is not None and line.startswith("- **Enforcement:**"):
                current.enforcement.extend(_BACKTICK.findall(line))
            elif current is not None and line.startswith("- **Detalle:**"):
                current.detalle.extend(_BACKTICK.findall(line))

    return version_line, principles


def _is_path(token: str) -> bool:
    """Un token es ruta si tiene separador o empieza con punto (.gitignore)."""
    return "/" in token or token.startswith(".")


def _check_version(version_line: str | None, errors: list[str]) -> None:
    if version_line is None:
        errors.append("Falta la linea de version (**Versión:** X.Y.Z | ...).")
        return
    if not _SEMVER.search(version_line):
        errors.append(f"Version sin semver valido: {version_line!r}")
    if len(_ISO_DATE.findall(version_line)) < 2:
        errors.append(
            f"Version debe incluir Ratificada y Última enmienda (YYYY-MM-DD): {version_line!r}"
        )


def _check_references(
    principles: list[_Principle],
    repo_root: Path,
    pipeline_text: str,
    errors: list[str],
) -> None:
    for p in principles:
        tokens = [(t, "Detalle") for t in p.detalle]
        tokens += [(t, "Enforcement") for t in p.enforcement]

        if not p.detalle:
            errors.append(f"Principio '{p.title}' sin linea Detalle.")
        if not p.enforcement:
            errors.append(f"Principio '{p.title}' sin linea Enforcement.")

        for token, field in tokens:
            if _is_path(token) and not (repo_root / token).exists():
                errors.append(f"Principio '{p.title}' {field}: referencia inexistente '{token}'.")

        for token in p.enforcement:
            name = token.rsplit("/", 1)[-1]
            if name in PIPELINE_TOOLS and name not in pipeline_text:
                errors.append(
                    f"Principio '{p.title}' Enforcement '{token}' no esta cableado "
                    f"en tools/pipeline_local.sh."
                )


def main(argv: list[str]) -> int:
    # Los titulos de principios usan caracteres no-ASCII (acentos, flechas).
    # En consolas Windows (cp1252) print() falla; forzamos UTF-8 en la salida.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")

    if len(argv) < 2:
        print("Uso: check_constitution.py <CONSTITUTION.md>", file=sys.stderr)
        return 2

    constitution = Path(argv[1])
    if not constitution.exists():
        print(f"No existe: {constitution}", file=sys.stderr)
        return 2

    repo_root = constitution.resolve().parent
    text = constitution.read_text(encoding="utf-8")
    version_line, principles = _parse(text)

    pipeline_path = repo_root / "tools" / "pipeline_local.sh"
    pipeline_text = pipeline_path.read_text(encoding="utf-8") if pipeline_path.exists() else ""

    errors: list[str] = []
    _check_version(version_line, errors)
    if not principles:
        errors.append("No se encontraron principios bajo '## Principios'.")
    _check_references(principles, repo_root, pipeline_text, errors)

    # Visibilidad: imprime los principios siempre.
    print(f"Constitucion: {len(principles)} principio(s) activo(s)")
    for p in principles:
        print(f"  - {p.title}")

    if errors:
        print("\nViolaciones de integridad de la constitucion:", file=sys.stderr)
        for e in errors:
            print(f"  x {e}", file=sys.stderr)
        print(
            f"\nTotal: {len(errors)} problema(s). Ver CONSTITUTION.md (seccion Governance).",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
