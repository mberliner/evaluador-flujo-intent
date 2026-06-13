"""Render de la traza de ejecucion del agente (SPEC-007 FR-010).

Se invoca dentro de la seccion "Traza de ejecucion" (un expander en app.py).
Por eso no abre expanders propios (Streamlit no permite anidarlos): muestra
cada paso inline con icono de estado, nombre, duracion y resumen de I/O.
"""

from __future__ import annotations

from datetime import datetime

import streamlit as ui  # alias agnostico

from src.domain.agent_trace import AgentTrace, TraceStep

_STATUS_ICON: dict[str, str] = {
    "completed": "✅",
    "failed": "❌",
    "in_progress": "⏳",
    "skipped": "⏭️",
}


def _format_duration(step: TraceStep) -> str:
    if step.duration_ms is not None and step.duration_ms >= 0:
        return f"{step.duration_ms / 1000:.1f}s"
    if not step.started_at or not step.completed_at:
        return ""
    try:
        seconds = (
            datetime.fromisoformat(step.completed_at) - datetime.fromisoformat(step.started_at)
        ).total_seconds()
    except ValueError:
        return ""
    return f"{seconds:.1f}s" if seconds >= 0 else ""


def _render_step(step: TraceStep) -> None:
    icon = _STATUS_ICON.get(step.status, "•")
    duration = _format_duration(step)
    suffix = f" · {duration}" if duration else ""
    ui.markdown(f"{icon} **{step.agent_name}** — {step.status}{suffix}")
    ui.caption(f"flow interno: `{step.child_flow_id or 'no'}`")
    if step.input_summary:
        ui.caption("Input")
        ui.code(step.input_summary)
    if step.output_summary:
        ui.caption("Output")
        ui.code(step.output_summary)
    ui.divider()


def render_trace(trace: AgentTrace) -> None:
    """Dibuja la traza. Si no hay pasos, muestra 'Traza no disponible'."""
    if not trace.steps:
        ui.caption("Traza no disponible")
        return

    ui.markdown(f"**Estado general:** {trace.overall_status}")
    ui.caption(f"thread_id: `{trace.thread_id}` · flow_id: `{trace.flow_id or '—'}`")
    for step in trace.steps:
        _render_step(step)
