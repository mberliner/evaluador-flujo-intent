"""Use-cases de ejecución de corridas (SPEC-005 unitario, SPEC-006 batch, SPEC-010 traza).

Orquesta build + puertos del dominio para ejecutar y evaluar casos contra el
agente. Sin I/O directo, sin framework de UI, sin parsing de CLI: recibe los
puertos por parámetro y reporta progreso por callback. Lo comparten el runner
headless y el dashboard (ver docs/ARCHITECTURE.md §ADR-005). El conocimiento del
control message del agente vive detrás del puerto (`AgentClient.get_final_response`,
SPEC-002), no acá.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from src.build import message_builder
from src.domain.agent_trace import AgentTrace
from src.domain.classification_evaluator import ClassificationEvaluator
from src.domain.ports import AgentClient
from src.domain.result import SuiteResult, TestResult
from src.domain.test_case import TestCase

# Callback de progreso: (índice 1-based, total, resultado del caso).
ProgressCallback = Callable[[int, int, TestResult], None]


def run_one(
    case: TestCase,
    client: AgentClient,
    evaluator: ClassificationEvaluator,
    *,
    completion_timeout: int = 300,
    capture_trace: bool = False,
) -> TestResult:
    """Ejecuta y evalúa un caso. Un fallo de ejecución produce un resultado
    Indeterminado anotado, nunca una excepción que aborte la corrida (FR-006)."""
    form = message_builder.build(case)
    trigger = client.send(form)
    thread_id = trigger.conversation_id
    if not thread_id:
        return execution_failure(case, f"El agente no devolvió thread_id: {trigger.content}")

    if not client.wait_for_completion(thread_id, timeout_seconds=completion_timeout):
        return execution_failure(case, "El agente no completó el flow en el tiempo esperado.")

    response = client.get_final_response(thread_id, trigger.content)
    result = evaluator.evaluate(case, response)
    trace = _capture_trace(client, thread_id) if capture_trace else None
    return replace(result, trace=trace)


def _capture_trace(client: AgentClient, thread_id: str) -> AgentTrace | None:
    """Captura única de la traza en vivo (SPEC-010 FR-US2-007).

    Un solo get_trace, sin poll ni segundo fetch: el flow puede quedar en estado
    no terminal (la cola final cierra después de depositar la clasificación, ver
    SPEC-007 FR-012) y se persiste tal cual. El flow_id es el ancla para abrir el
    flow en la plataforma. Un fallo al capturar no aborta el caso (FR-US2-005)."""
    try:
        return client.get_trace(thread_id)
    except Exception:
        return None


def execution_failure(case: TestCase, reason: str) -> TestResult:
    return TestResult(
        case_id=case.id,
        expected=case.clasificacion_esperada,
        actual_response=reason,
        extracted_classification=None,
        passed=None,
        notes=f"Error de ejecución: {reason}",
    )


def run_batch(
    cases: tuple[TestCase, ...],
    client: AgentClient,
    evaluator: ClassificationEvaluator,
    *,
    completion_timeout: int = 300,
    capture_traces: bool = False,
    on_result: ProgressCallback | None = None,
) -> tuple[TestResult, ...]:
    """Ejecuta los casos en orden; el fallo de uno no aborta los demás (FR-006).

    Si se pasa `on_result`, se invoca tras cada caso con (índice 1-based,
    total, resultado) para reportar progreso en vivo (FR-005b).
    """
    total = len(cases)
    results: list[TestResult] = []
    for index, case in enumerate(cases, start=1):
        try:
            result = run_one(
                case,
                client,
                evaluator,
                completion_timeout=completion_timeout,
                capture_trace=capture_traces,
            )
        except KeyboardInterrupt:
            # Parada manual (Ctrl+C, SPEC-006 FR-US3-001): el caso en vuelo no
            # completó, se descarta sin resultado y se cortan los pendientes. Se
            # devuelve lo acumulado para que el llamador cierre y persista la
            # corrida parcial por la misma ruta que una corrida normal.
            break
        except Exception as exc:
            result = execution_failure(case, f"excepción inesperada: {exc}")
        results.append(result)
        if on_result is not None:
            on_result(index, total, result)
    return tuple(results)


def build_suite(
    cases: tuple[TestCase, ...],
    client: AgentClient,
    evaluator: ClassificationEvaluator,
    agent_id: str,
    *,
    completion_timeout: int = 300,
    capture_traces: bool = False,
    on_result: ProgressCallback | None = None,
    endpoint_url: str = "",
) -> SuiteResult:
    results = run_batch(
        cases,
        client,
        evaluator,
        completion_timeout=completion_timeout,
        capture_traces=capture_traces,
        on_result=on_result,
    )
    return SuiteResult.create(results, agent_id=agent_id, endpoint_url=endpoint_url)
