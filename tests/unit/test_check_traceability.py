"""Tests del gate de trazabilidad (tools/check_traceability.py, Principio V).

Construyen un directorio de specs temporal (registro + archivos) y verifican que
el check detecta: spec sin sección obligatoria, spec en disco no registrada,
entrada de registro colgada, FR sin cobertura y test referenciado inexistente;
y que las specs draft no se evalúan por cobertura.
"""

from __future__ import annotations

from pathlib import Path

from tools.check_traceability import main

_VALID_SPEC = """# SPEC-100-demo

## User Story (Priority: P1)
Como usuario quiero algo.

## Functional Requirements
- **FR-001**: MUST hacer algo.

## Success Criteria
- **SC-001**: medible.

## Coverage mapping
| Requisito | Cubierto por |
|---|---|
| FR-001 | test x |
"""


def _registry(rows: list[tuple[str, str, str, str]]) -> str:
    lines = [
        "# SPECS_REGISTRY",
        "",
        "| ID | Título | Estado | Iter | Formato | Archivo |",
        "|---|---|---|---|---|---|",
    ]
    for spec_id, estado, formato, archivo in rows:
        lines.append(f"| {spec_id} | t | {estado} | 1 | {formato} | [{archivo}]({archivo}) |")
    return "\n".join(lines) + "\n"


def _setup(tmp_path: Path, rows: list[tuple[str, str, str, str]], files: dict[str, str]) -> Path:
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "SPECS_REGISTRY.md").write_text(_registry(rows), encoding="utf-8")
    for name, content in files.items():
        (specs / name).write_text(content, encoding="utf-8")
    return specs


def test_clean_passes(tmp_path: Path) -> None:
    specs = _setup(
        tmp_path,
        [("SPEC-100-demo", "active", "híbrido", "SPEC-100-demo.md")],
        {"SPEC-100-demo.md": _VALID_SPEC},
    )
    assert main(["x", str(specs)]) == 0


def test_missing_fr_section_fails(tmp_path: Path) -> None:
    sin_fr = _VALID_SPEC.replace("## Functional Requirements\n- **FR-001**: MUST hacer algo.\n", "")
    specs = _setup(
        tmp_path,
        [("SPEC-100-demo", "active", "híbrido", "SPEC-100-demo.md")],
        {"SPEC-100-demo.md": sin_fr},
    )
    assert main(["x", str(specs)]) == 1


def test_unregistered_spec_file_fails(tmp_path: Path) -> None:
    specs = _setup(
        tmp_path,
        [],  # registro vacío: el archivo en disco no está registrado
        {"SPEC-100-demo.md": _VALID_SPEC},
    )
    assert main(["x", str(specs)]) == 1


def test_dangling_registry_entry_fails(tmp_path: Path) -> None:
    specs = _setup(
        tmp_path,
        [("SPEC-404-ghost", "active", "híbrido", "SPEC-404-ghost.md")],
        {},  # la entrada apunta a un archivo que no existe
    )
    assert main(["x", str(specs)]) == 1


def test_fr_not_in_coverage_fails(tmp_path: Path) -> None:
    con_fr_huerfano = _VALID_SPEC.replace(
        "- **FR-001**: MUST hacer algo.",
        "- **FR-001**: MUST hacer algo.\n- **FR-002**: MUST hacer otra cosa.",
    )
    specs = _setup(
        tmp_path,
        [("SPEC-100-demo", "active", "híbrido", "SPEC-100-demo.md")],
        {"SPEC-100-demo.md": con_fr_huerfano},
    )
    assert main(["x", str(specs)]) == 1


def test_dangling_test_ref_fails(tmp_path: Path) -> None:
    con_test_inexistente = _VALID_SPEC.replace(
        "| FR-001 | test x |",
        "| FR-001 | `tests/unit/test_nope.py` |",
    )
    specs = _setup(
        tmp_path,
        [("SPEC-100-demo", "active", "híbrido", "SPEC-100-demo.md")],
        {"SPEC-100-demo.md": con_test_inexistente},
    )
    assert main(["x", str(specs)]) == 1


def test_draft_skips_coverage(tmp_path: Path) -> None:
    # FR-002 declarado pero ausente del coverage: en draft NO se evalúa cobertura.
    con_fr_huerfano = _VALID_SPEC.replace(
        "- **FR-001**: MUST hacer algo.",
        "- **FR-001**: MUST hacer algo.\n- **FR-002**: MUST hacer otra cosa.",
    )
    specs = _setup(
        tmp_path,
        [("SPEC-100-demo", "draft", "híbrido", "SPEC-100-demo.md")],
        {"SPEC-100-demo.md": con_fr_huerfano},
    )
    assert main(["x", str(specs)]) == 0


def test_casero_spec_skips_structure(tmp_path: Path) -> None:
    # Una spec casero (SPEC-000..003) no se evalúa por estructura híbrida.
    specs = _setup(
        tmp_path,
        [("SPEC-001-x", "active", "casero", "SPEC-001-x.md")],
        {"SPEC-001-x.md": "# SPEC-001-x\n\nFormato libre, sin secciones híbridas.\n"},
    )
    assert main(["x", str(specs)]) == 0
