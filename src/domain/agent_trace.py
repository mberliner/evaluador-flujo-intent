"""Modelo de la traza de ejecucion del agente (SPEC-007).

Describe que sub-agentes invoco el orquestador, en que orden y con que
resultado parcial. Es codigo puro: sin I/O, red ni conocimiento del shape
del proveedor (ese mapeo vive en el adapter, ver docs/ARCHITECTURE.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Valores validos de TraceStep.status (publico, FR-004).
TRACE_STEP_STATUSES: tuple[str, ...] = ("completed", "failed", "in_progress", "skipped")


@dataclass(frozen=True, slots=True)
class TraceStep:
    """Un paso de ejecucion de un sub-agente dentro del flow."""

    step_id: str
    agent_name: str
    status: str
    input_summary: str = ""
    output_summary: str = ""
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: int | None = None
    child_flow_id: str | None = None

    def __post_init__(self) -> None:
        if not self.step_id:
            raise ValueError("step_id no puede estar vacio")
        if not self.agent_name:
            raise ValueError("agent_name no puede estar vacio")
        if self.status not in TRACE_STEP_STATUSES:
            raise ValueError(f"status invalido: '{self.status}'. Validos: {TRACE_STEP_STATUSES}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "agent_name": self.agent_name,
            "status": self.status,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "child_flow_id": self.child_flow_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TraceStep:
        return cls(
            step_id=data["step_id"],
            agent_name=data["agent_name"],
            status=data["status"],
            input_summary=data.get("input_summary", ""),
            output_summary=data.get("output_summary", ""),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            duration_ms=data.get("duration_ms"),
            child_flow_id=data.get("child_flow_id"),
        )


@dataclass(frozen=True, slots=True)
class AgentTrace:
    """Traza completa de un run: estado general + pasos ordenados."""

    thread_id: str
    flow_id: str | None
    overall_status: str
    steps: tuple[TraceStep, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "thread_id": self.thread_id,
            "flow_id": self.flow_id,
            "overall_status": self.overall_status,
            "steps": [s.to_dict() for s in self.steps],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentTrace:
        return cls(
            thread_id=data["thread_id"],
            flow_id=data.get("flow_id"),
            overall_status=data["overall_status"],
            steps=tuple(TraceStep.from_dict(s) for s in data.get("steps", ())),
        )
