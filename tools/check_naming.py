"""Linter de nomenclatura agnostica.

Implementa la verificacion automatica de specs/SPEC-000-naming.md:
ningun identificador de Python en src/ puede contener tokens prohibidos
que referencien proveedor, framework UI, formato de almacenamiento o
protocolo de autenticacion.

Uso:
    python tools/check_naming.py src

Exit code 0 si todo OK, 1 si hay violaciones.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

PROHIBITED_TOKENS: tuple[str, ...] = (
    # proveedor / plataforma
    "watson",
    "orchestrate",
    "ibm",
    "azure",
    "aws",
    "openai",
    "anthropic",
    "bedrock",
    # framework UI
    "streamlit",
    "flask",
    "fastapi",
    "django",
    "gradio",
    # formato de almacenamiento / serializacion
    "csv",
    "json",
    "xml",
    "yaml",
    "parquet",
    # protocolo / herramienta de auth
    "oauth",
    "iam",
    "jwt",
    "apikey",
)

# Identificadores explicitamente permitidos. Sincronizar con la seccion
# "Identificadores permitidos" en specs/SPEC-000-naming.md.
ALLOWED_IDENTIFIERS: frozenset[str] = frozenset(
    {
        "json",  # contrato de requests.Response.json()
    }
)


class _NameCollector(ast.NodeVisitor):
    """Recolecta nombres de clases, funciones, variables top-level y atributos."""

    def __init__(self) -> None:
        self.names: list[tuple[str, int]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.names.append((node.name, node.lineno))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.names.append((node.name, node.lineno))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.names.append((node.name, node.lineno))
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.names.append((target.id, node.lineno))
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name):
            self.names.append((node.target.id, node.lineno))
        self.generic_visit(node)


def _violations_in_file(path: Path) -> list[tuple[Path, int, str, str]]:
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    collector = _NameCollector()
    collector.visit(tree)

    violations: list[tuple[Path, int, str, str]] = []
    for name, lineno in collector.names:
        if name in ALLOWED_IDENTIFIERS:
            continue
        lowered = name.lower()
        for token in PROHIBITED_TOKENS:
            if token in lowered:
                violations.append((path, lineno, name, token))
                break

    # Tambien revisamos el stem del archivo.
    stem_lowered = path.stem.lower()
    for token in PROHIBITED_TOKENS:
        if token in stem_lowered:
            violations.append((path, 0, path.name, token))
            break

    return violations


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Uso: check_naming.py <root>", file=sys.stderr)
        return 2

    root = Path(argv[1])
    if not root.exists():
        print(f"No existe: {root}", file=sys.stderr)
        return 2

    all_violations: list[tuple[Path, int, str, str]] = []
    for path in root.rglob("*.py"):
        all_violations.extend(_violations_in_file(path))

    if not all_violations:
        return 0

    print("Violaciones de nomenclatura agnostica (SPEC-000-naming):", file=sys.stderr)
    for path, lineno, name, token in all_violations:
        loc = f"{path}:{lineno}" if lineno else str(path)
        msg = f"  {loc}  identificador '{name}' contiene token prohibido '{token}'"
        print(msg, file=sys.stderr)
    print(
        f"\nTotal: {len(all_violations)} violacion(es). "
        f"Ver specs/SPEC-000-naming.md para la lista de tokens y excepciones.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
