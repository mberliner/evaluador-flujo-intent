"""Tests de FileRunRepository (SPEC-005): round-trip, append a estadistica, error de I/O."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.adapters.file_run_repository import FileRunRepository, RunPersistenceError
from src.domain.agent_trace import AgentTrace, TraceStep
from src.domain.result import SuiteResult, TestResult


def _result(
    case_id: str = "TC-V-01",
    passed: bool | None = True,
    extracted: str | None = "Verde",
) -> TestResult:
    return TestResult(
        case_id=case_id,
        expected="Verde",
        actual_response="La clasificacion es Verde",
        extracted_classification=extracted,
        passed=passed,
        conversation_id="conv-123",
    )


def _run(case_id: str = "TC-V-01", passed: bool | None = True) -> SuiteResult:
    return SuiteResult.create((_result(case_id, passed=passed),), agent_id="agent-x")


def test_save_writes_detail_under_detail_dir(tmp_path: Path) -> None:
    repo = FileRunRepository(tmp_path)
    saved_path = repo.save(_run())
    written = Path(saved_path)
    assert written.exists()
    assert written.parent == tmp_path / "detail"
    assert written.name.startswith("run-")
    assert written.name.endswith("-TC-V-01.json")


def test_round_trip_save_then_load(tmp_path: Path) -> None:
    repo = FileRunRepository(tmp_path)
    run = _run()
    repo.save(run)
    restored = repo.load(run.run_id)
    assert restored == run


def test_round_trip_preserves_trace_on_disk(tmp_path: Path) -> None:
    repo = FileRunRepository(tmp_path)
    trace = AgentTrace(
        thread_id="th-1",
        flow_id="flow-9",
        overall_status="interrupted",
        steps=(TraceStep(step_id="s1", agent_name="Validador", status="in_progress"),),
    )
    with_trace = TestResult(
        case_id="TC-1",
        expected="Verde",
        actual_response="...",
        extracted_classification="Verde",
        passed=True,
        conversation_id="conv-1",
        trace=trace,
    )
    run = SuiteResult.create((with_trace,), agent_id="agent-x")
    repo.save(run)
    restored = repo.load(run.run_id)
    assert restored.results[0].trace == trace
    assert restored.results[0].flow_id == "flow-9"


def test_batch_detail_filename_has_no_case_suffix(tmp_path: Path) -> None:
    repo = FileRunRepository(tmp_path)
    run = SuiteResult.create(
        (_result("TC-1", passed=True), _result("TC-2", passed=False)),
        agent_id="agent-x",
    )
    saved = Path(repo.save(run))
    # múltiples casos -> el archivo lleva sólo el run_id, sin sufijo de caso
    assert saved.name == f"{run.run_id}.json"
    assert repo.load(run.run_id) == run


def test_indeterminate_result_persists(tmp_path: Path) -> None:
    repo = FileRunRepository(tmp_path)
    run = SuiteResult.create((_result("TC-R-03", passed=None, extracted=None),), agent_id="agent-x")
    repo.save(run)
    restored = repo.load(run.run_id)
    assert restored.results[0].verdict == "indeterminado"
    assert restored.results[0].extracted_classification is None


def test_case_stats_csv_appends_without_duplicating_header(tmp_path: Path) -> None:
    repo = FileRunRepository(tmp_path)
    repo.save(_run("TC-1", passed=True))
    repo.save(_run("TC-2", passed=False))

    stats_path = tmp_path / "stats" / "estadistica-casos.csv"
    with stats_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=";"))

    assert rows[0] == [
        "run_id",
        "timestamp",
        "case_id",
        "expected",
        "extracted_classification",
        "verdict",
    ]
    data_rows = rows[1:]
    assert len(data_rows) == 2
    assert data_rows[0][2] == "TC-1"
    assert data_rows[0][5] == "pass"
    assert data_rows[1][2] == "TC-2"
    assert data_rows[1][5] == "fail"


def test_load_latest_returns_most_recent(tmp_path: Path) -> None:
    repo = FileRunRepository(tmp_path)
    assert repo.load_latest() is None
    older = SuiteResult(
        run_id="run-20260101T000000",
        timestamp="2026-01-01T00:00:00+00:00",
        agent_id="agent-x",
        results=(_result("TC-OLD"),),
    )
    newer = SuiteResult(
        run_id="run-20260526T143000",
        timestamp="2026-05-26T14:30:00+00:00",
        agent_id="agent-x",
        results=(_result("TC-NEW"),),
    )
    repo.save(older)
    repo.save(newer)
    latest = repo.load_latest()
    assert latest is not None
    assert latest.run_id == "run-20260526T143000"


def test_load_unknown_run_raises(tmp_path: Path) -> None:
    repo = FileRunRepository(tmp_path)
    with pytest.raises(RunPersistenceError):
        repo.load("run-99999999T999999")


def test_io_error_is_reported_explicitly(tmp_path: Path) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("soy un archivo, no un directorio", encoding="utf-8")
    repo = FileRunRepository(blocker)
    with pytest.raises(RunPersistenceError):
        repo.save(_run())


def test_regenerate_run_stats_rows_match_summary(tmp_path: Path) -> None:
    repo = FileRunRepository(tmp_path)
    run = SuiteResult(
        run_id="run-20260526T143000",
        timestamp="2026-05-26T14:30:00+00:00",
        agent_id="agent-x",
        results=(
            _result("TC-1", passed=True),
            _result("TC-2", passed=False),
            _result("TC-3", passed=None, extracted=None),
        ),
    )
    repo.save(run)
    repo.regenerate_run_stats()

    stats_path = tmp_path / "stats" / "estadistica-corridas.csv"
    with stats_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))

    assert len(rows) == 2  # 1 corrida + fila TOTAL
    row = rows[0]
    assert row["run_id"] == "run-20260526T143000"
    assert row["total"] == "3"
    assert row["pass"] == "1"
    assert row["indeterminado"] == "1"
    assert row["accuracy_bruta"] == "0.3333"  # 1/3
    assert row["accuracy_efectiva"] == "0.5000"  # 1/2
    assert rows[-1]["run_id"] == "TOTAL"


def test_regenerate_run_stats_appends_total_row(tmp_path: Path) -> None:
    repo = FileRunRepository(tmp_path)
    repo.save(
        SuiteResult(
            run_id="run-20260526T143000",
            timestamp="2026-05-26T14:30:00+00:00",
            agent_id="agent-x",
            results=(_result("TC-1", passed=True), _result("TC-2", passed=False)),
        )
    )
    repo.save(
        SuiteResult(
            run_id="run-20260526T150000",
            timestamp="2026-05-26T15:00:00+00:00",
            agent_id="agent-x",
            results=(_result("TC-3", passed=True), _result("TC-4", passed=None, extracted=None)),
        )
    )
    repo.regenerate_run_stats()

    stats_path = tmp_path / "stats" / "estadistica-corridas.csv"
    with stats_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))

    assert len(rows) == 3  # 2 corridas + fila TOTAL
    total = rows[-1]
    assert total["run_id"] == "TOTAL"
    assert total["total"] == "4"
    assert total["pass"] == "2"
    assert total["fail"] == "1"
    assert total["indeterminado"] == "1"
    assert total["accuracy_bruta"] == "0.5000"  # 2/4
    assert total["accuracy_efectiva"] == "0.6667"  # 2/3 (excluye indeterminado)


def test_regenerate_run_stats_includes_endpoint_url(tmp_path: Path) -> None:
    """SPEC-013 FR-US2-003: la columna endpoint_url se puebla por corrida y queda
    vacía en la fila TOTAL (agregado multi-corrida)."""
    repo = FileRunRepository(tmp_path)
    repo.save(
        SuiteResult(
            run_id="run-20260703T160000",
            timestamp="2026-07-03T16:00:00+00:00",
            agent_id="sync_http",
            results=(_result("TC-1", passed=True),),
            endpoint_url="https://alt.example/intents",
        )
    )
    repo.regenerate_run_stats()

    stats_path = tmp_path / "stats" / "estadistica-corridas.csv"
    with stats_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))

    assert rows[0]["endpoint_url"] == "https://alt.example/intents"
    assert rows[-1]["run_id"] == "TOTAL"
    assert rows[-1]["endpoint_url"] == ""


def test_regenerate_run_stats_endpoint_url_empty_for_legacy_run(tmp_path: Path) -> None:
    """SPEC-013 FR-US2-002/003: una corrida sin el campo (default '') no rompe el CSV."""
    repo = FileRunRepository(tmp_path)
    repo.save(_run("TC-1", passed=True))  # sin endpoint_url -> ""
    repo.regenerate_run_stats()

    stats_path = tmp_path / "stats" / "estadistica-corridas.csv"
    with stats_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
    assert rows[0]["endpoint_url"] == ""


def test_regenerate_run_stats_is_idempotent(tmp_path: Path) -> None:
    repo = FileRunRepository(tmp_path)
    repo.save(_run("TC-1", passed=True))
    repo.save(
        SuiteResult(
            run_id="run-20260526T150000",
            timestamp="2026-05-26T15:00:00+00:00",
            agent_id="agent-x",
            results=(_result("TC-2", passed=False),),
        )
    )
    first = repo.regenerate_run_stats()
    content_1 = Path(first).read_text(encoding="utf-8")
    content_2 = Path(repo.regenerate_run_stats()).read_text(encoding="utf-8")
    assert content_1 == content_2  # sin duplicados al regenerar

    with Path(first).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
    assert len(rows) == 3  # 2 corridas + fila TOTAL


def test_regenerate_run_stats_empty_when_no_runs(tmp_path: Path) -> None:
    repo = FileRunRepository(tmp_path)
    path = repo.regenerate_run_stats()
    with Path(path).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
    assert rows == []
