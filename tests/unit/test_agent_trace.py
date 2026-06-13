"""Tests del modelo de traza del agente (SPEC-007 SC-002/SC-004)."""

from __future__ import annotations

import pytest

from src.domain.agent_trace import TRACE_STEP_STATUSES, AgentTrace, TraceStep


def _step(**overrides: object) -> TraceStep:
    base: dict[str, object] = {
        "step_id": "step-1",
        "agent_name": "FI Evaluador Integridad",
        "status": "completed",
    }
    base.update(overrides)
    return TraceStep(**base)  # type: ignore[arg-type]


def test_trace_step_valido_se_construye() -> None:
    step = _step(
        input_summary="entrada",
        output_summary="salida",
        started_at="2026-05-27T10:00:00",
        completed_at="2026-05-27T10:00:05",
        duration_ms=4920,
    )
    assert step.agent_name == "FI Evaluador Integridad"
    assert step.status == "completed"
    assert step.duration_ms == 4920
    assert step.to_dict()["step_id"] == "step-1"
    assert step.to_dict()["duration_ms"] == 4920


@pytest.mark.parametrize("status", list(TRACE_STEP_STATUSES))
def test_trace_step_acepta_todos_los_status_validos(status: str) -> None:
    assert _step(status=status).status == status


def test_trace_step_status_invalido_lanza_value_error() -> None:
    with pytest.raises(ValueError, match="status invalido"):
        _step(status="interrupted")


def test_trace_step_step_id_vacio_lanza_value_error() -> None:
    with pytest.raises(ValueError, match="step_id"):
        _step(step_id="")


def test_trace_step_agent_name_vacio_lanza_value_error() -> None:
    with pytest.raises(ValueError, match="agent_name"):
        _step(agent_name="")


def test_agent_trace_con_pasos_se_construye() -> None:
    trace = AgentTrace(
        thread_id="th-1",
        flow_id="flow-9",
        overall_status="completed",
        steps=(_step(), _step(step_id="step-2", agent_name="Validador")),
    )
    assert len(trace.steps) == 2
    assert trace.to_dict()["flow_id"] == "flow-9"


def test_agent_trace_sin_pasos_es_valido() -> None:
    trace = AgentTrace(thread_id="th-1", flow_id=None, overall_status="unknown")
    assert trace.steps == ()
    assert trace.to_dict()["steps"] == []


def test_trace_step_child_flow_id_se_serializa() -> None:
    step = _step(child_flow_id="inner-flow-uuid-123")
    d = step.to_dict()
    assert d["child_flow_id"] == "inner-flow-uuid-123"


def test_trace_step_child_flow_id_none_por_defecto() -> None:
    step = _step()
    assert step.child_flow_id is None
    assert step.to_dict()["child_flow_id"] is None


def test_trace_step_round_trip_to_from_dict() -> None:
    step = _step(
        input_summary="entrada",
        output_summary="salida",
        duration_ms=4920,
        child_flow_id="inner-123",
    )
    assert TraceStep.from_dict(step.to_dict()) == step


def test_agent_trace_round_trip_to_from_dict() -> None:
    trace = AgentTrace(
        thread_id="th-1",
        flow_id="flow-9",
        overall_status="completed",
        steps=(_step(), _step(step_id="step-2", agent_name="Validador", status="in_progress")),
    )
    assert AgentTrace.from_dict(trace.to_dict()) == trace


def test_agent_trace_round_trip_sin_pasos_ni_flow_id() -> None:
    trace = AgentTrace(thread_id="th-1", flow_id=None, overall_status="unknown")
    assert AgentTrace.from_dict(trace.to_dict()) == trace
