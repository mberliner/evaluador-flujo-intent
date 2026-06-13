"""Tests del interlock de autoría (tools/sdd_gate.py, Principio V).

Verifican la decisión del gate sobre un repo temporal: bloquea edición de src/
sin spec declarada o con declaración inválida, permite con declaración válida y
permite siempre fuera de src/.
"""

from __future__ import annotations

from pathlib import Path

from tools.sdd_gate import decide


def _repo(tmp_path: Path, declared: str | None) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "SPEC-001-x.md").write_text("# SPEC-001-x\n", encoding="utf-8")
    (tmp_path / "specs" / "SPECS_REGISTRY.md").write_text(
        "| SPEC-001-x | t | active | 1 | casero | [SPEC-001-x.md](SPEC-001-x.md) |\n",
        encoding="utf-8",
    )
    (tmp_path / "CONSTITUTION.md").write_text("c\n", encoding="utf-8")
    if declared is not None:
        (tmp_path / ".sdd").mkdir()
        (tmp_path / ".sdd" / "current-spec").write_text(declared, encoding="utf-8")
    return tmp_path


def _payload(repo: Path, rel: str) -> dict[str, object]:
    return {"tool_name": "Edit", "tool_input": {"file_path": str(repo / rel)}}


def test_block_src_without_declaration(tmp_path: Path) -> None:
    repo = _repo(tmp_path, declared=None)
    allow, reason = decide(_payload(repo, "src/x.py"), repo)
    assert allow is False
    assert "spec vigente declarada" in reason


def test_allow_src_with_valid_declaration(tmp_path: Path) -> None:
    repo = _repo(tmp_path, declared="SPEC-001-x\n")
    allow, _ = decide(_payload(repo, "src/x.py"), repo)
    assert allow is True


def test_block_src_with_invalid_declaration(tmp_path: Path) -> None:
    repo = _repo(tmp_path, declared="SPEC-999-ghost\n")
    allow, reason = decide(_payload(repo, "src/x.py"), repo)
    assert allow is False
    assert "invalida" in reason


def test_declaration_ignores_comments_and_blanks(tmp_path: Path) -> None:
    repo = _repo(tmp_path, declared="# comentario\n\n")
    allow, _ = decide(_payload(repo, "src/x.py"), repo)
    assert allow is False  # solo comentarios = sin declaración efectiva


def test_allow_non_src_path(tmp_path: Path) -> None:
    repo = _repo(tmp_path, declared=None)
    allow, _ = decide(_payload(repo, "docs/y.md"), repo)
    assert allow is True


def test_allow_when_no_file_path(tmp_path: Path) -> None:
    repo = _repo(tmp_path, declared=None)
    allow, _ = decide({"tool_name": "Bash", "tool_input": {}}, repo)
    assert allow is True
