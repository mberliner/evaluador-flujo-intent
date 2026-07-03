"""Tests de los modelos de resultado (SPEC-005): TestResult.verdict y SuiteResult."""

from __future__ import annotations

from datetime import UTC, datetime

from src.domain.agent_trace import AgentTrace, TraceStep
from src.domain.result import SuiteResult, TestResult, aggregate_runs


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


def test_verdict_serialized_in_to_dict() -> None:
    assert _result(passed=True).to_dict()["verdict"] == "pass"
    assert _result(passed=False).to_dict()["verdict"] == "fail"
    assert _result(passed=None, extracted=None).to_dict()["verdict"] == "indeterminado"


def test_suite_summary_counts_by_verdict() -> None:
    run = SuiteResult.create(
        (
            _result("TC-1", passed=True),
            _result("TC-2", passed=False),
            _result("TC-3", passed=None, extracted=None),
        ),
        agent_id="agent-x",
    )
    assert run.summary == {"total": 3, "pass": 1, "fail": 1, "indeterminado": 1}


def test_create_derives_run_id_from_moment() -> None:
    moment = datetime(2026, 5, 26, 14, 30, 0, tzinfo=UTC)
    run = SuiteResult.create((_result(),), agent_id="agent-x", moment=moment, token="abc12345")
    assert run.run_id == "run-20260526T143000-abc12345"
    assert run.timestamp == moment.isoformat()
    assert run.agent_id == "agent-x"


def test_create_genera_run_id_unico_en_el_mismo_segundo() -> None:
    # Dos corridas en el mismo instante (mismo segundo) no deben colisionar:
    # el token único las distingue, evitando que una pise a la otra en runs/.
    moment = datetime(2026, 5, 26, 14, 30, 0, tzinfo=UTC)
    run_a = SuiteResult.create((_result(),), agent_id="agent-x", moment=moment)
    run_b = SuiteResult.create((_result(),), agent_id="agent-x", moment=moment)
    assert run_a.run_id != run_b.run_id
    # El prefijo de timestamp se conserva (orden por recencia intacto).
    assert run_a.run_id.startswith("run-20260526T143000-")
    assert run_b.run_id.startswith("run-20260526T143000-")


def test_suite_round_trip_to_from_dict() -> None:
    run = SuiteResult.create(
        (_result("TC-1", passed=True), _result("TC-2", passed=None, extracted=None)),
        agent_id="agent-x",
    )
    restored = SuiteResult.from_dict(run.to_dict())
    assert restored == run


def test_suite_round_trip_preserves_trace() -> None:
    trace = AgentTrace(
        thread_id="th-1",
        flow_id="flow-9",
        overall_status="completed",
        steps=(TraceStep(step_id="s1", agent_name="Validador", status="completed"),),
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
    restored = SuiteResult.from_dict(run.to_dict())
    assert restored == run
    assert restored.results[0].trace == trace
    assert restored.results[0].flow_id == "flow-9"


def test_endpoint_url_serialized_and_round_trips() -> None:
    """SPEC-013 FR-US2-002: endpoint_url viaja en to_dict/from_dict sin pérdida."""
    run = SuiteResult.create(
        (_result(),), agent_id="agent-x", endpoint_url="https://alt.example/intents"
    )
    assert run.to_dict()["endpoint_url"] == "https://alt.example/intents"
    restored = SuiteResult.from_dict(run.to_dict())
    assert restored == run
    assert restored.endpoint_url == "https://alt.example/intents"


def test_endpoint_url_default_and_backward_compatible() -> None:
    """SPEC-013 FR-US2-002: default vacío; runs previos sin la clave se leen igual."""
    run = SuiteResult.create((_result(),), agent_id="agent-x")
    assert run.endpoint_url == ""
    legacy = run.to_dict()
    del legacy["endpoint_url"]  # corrida persistida antes del campo
    restored = SuiteResult.from_dict(legacy)
    assert restored.endpoint_url == ""
    assert restored == run


def test_result_without_trace_serializes_none() -> None:
    d = _result().to_dict()
    assert d["trace"] is None
    # round-trip de runs sin traza (anteriores a la capacidad) sigue funcionando
    run = SuiteResult.create((_result(),), agent_id="agent-x")
    assert SuiteResult.from_dict(run.to_dict()) == run


def test_accuracy_bruta_and_efectiva() -> None:
    run = SuiteResult.create(
        (
            _result("TC-1", passed=True),
            _result("TC-2", passed=False),
            _result("TC-3", passed=None, extracted=None),
        ),
        agent_id="agent-x",
    )
    # bruta = 1 pass / 3 total
    assert run.accuracy_bruta == 1 / 3
    # efectiva = 1 pass / 2 evaluables (excluye 1 indeterminado)
    assert run.accuracy_efectiva == 1 / 2


def test_accuracy_efectiva_null_when_all_indeterminate() -> None:
    run = SuiteResult.create(
        (
            _result("TC-1", passed=None, extracted=None),
            _result("TC-2", passed=None, extracted=None),
        ),
        agent_id="agent-x",
    )
    assert run.accuracy_bruta == 0.0
    assert run.accuracy_efectiva is None


def test_accuracy_none_when_empty() -> None:
    run = SuiteResult.create((), agent_id="agent-x")
    assert run.accuracy_bruta is None
    assert run.accuracy_efectiva is None


def test_aggregate_runs_sums_all_cases() -> None:
    run_a = SuiteResult.create(
        (_result("TC-1", passed=True), _result("TC-2", passed=False)),
        agent_id="agent-x",
    )
    run_b = SuiteResult.create(
        (
            _result("TC-3", passed=True),
            _result("TC-4", passed=True),
            _result("TC-5", passed=None, extracted=None),
        ),
        agent_id="agent-x",
    )
    overall = aggregate_runs((run_a, run_b))
    assert (overall.total, overall.passed, overall.failed, overall.indeterminate) == (5, 3, 1, 1)
    assert overall.accuracy_bruta == 3 / 5
    assert overall.accuracy_efectiva == 3 / 4  # excluye 1 indeterminado


def test_aggregate_runs_empty_is_none() -> None:
    overall = aggregate_runs(())
    assert overall.total == 0
    assert overall.accuracy_bruta is None
    assert overall.accuracy_efectiva is None
