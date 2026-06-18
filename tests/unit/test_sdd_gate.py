"""Tests del interlock de autoría (tools/sdd_gate.py, Principio V).

Verifican la decisión del gate sobre un repo temporal: bloquea edición de src/
sin spec declarada o con declaración inválida, permite con declaración válida y
permite siempre fuera de src/. Incluye chequeo de mtime: la spec debe haber
sido editada después de declararla en current-spec.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from tools.sdd_gate import decide


def _repo(tmp_path: Path, declared: str | None, *, spec_touched: bool = True) -> Path:
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
        if spec_touched:
            # spec editada después de current-spec: avanzar mtime de la spec
            future = time.time() + 2
            spec_file = tmp_path / "specs" / "SPEC-001-x.md"
            if spec_file.exists():
                os.utime(spec_file, (future, future))
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


def test_block_src_when_spec_not_touched(tmp_path: Path) -> None:
    repo = _repo(tmp_path, declared="SPEC-001-x\n", spec_touched=False)
    allow, reason = decide(_payload(repo, "src/x.py"), repo)
    assert allow is False
    assert "no fueron editadas" in reason


def test_allow_src_when_spec_touched(tmp_path: Path) -> None:
    repo = _repo(tmp_path, declared="SPEC-001-x\n", spec_touched=True)
    allow, _ = decide(_payload(repo, "src/x.py"), repo)
    assert allow is True
