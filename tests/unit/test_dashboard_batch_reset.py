"""Reset del display batch al subir un archivo distinto (SPEC-006 FR-US1, MUST).

Verifica el helper puro `_clear_batch_run_state`: al detectar un archivo nuevo, el
dashboard descarta tanto el resultado batch en pantalla como cualquier corrida en curso
del archivo anterior, sin tocar estado ajeno al batch ni la clave del archivo nuevo.
"""

from __future__ import annotations

from src.dashboard.app import _BATCH_RUN_KEYS, _clear_batch_run_state


def test_clear_descarta_resultado_y_corrida_en_curso() -> None:
    state: dict[str, object] = {
        "batch_result": {"run": object()},
        "batch_phase": "running",
        "batch_pending": [1, 2],
        "batch_done": [],
        "batch_total": 2,
        "batch_agent_id": "agent-x",
        "batch_traces": True,
        "batch_client": object(),
        "batch_evaluator": object(),
        "batch_file_key": "hash-viejo",
        "case_validated": "no-tocar",
    }

    _clear_batch_run_state(state)

    assert "batch_result" not in state
    for key in _BATCH_RUN_KEYS:
        assert key not in state, f"{key} debió limpiarse"
    # No toca la clave del archivo (la fija el caller) ni estado ajeno al batch.
    assert state["batch_file_key"] == "hash-viejo"
    assert state["case_validated"] == "no-tocar"


def test_clear_es_idempotente_sin_estado() -> None:
    state: dict[str, object] = {}

    _clear_batch_run_state(state)  # no debe lanzar aunque no haya nada que limpiar

    assert state == {}
