"""Tests de métricas de suite (SPEC-008): matriz de confusión, accuracy por
clase y % sin clasificación. Funciones puras sobre SuiteResult, sin red ni FS."""

from __future__ import annotations

from src.domain.metrics import (
    SIN_CLASIFICACION,
    aggregate_suite_metrics,
    compute_suite_metrics,
)
from src.domain.result import SuiteResult, TestResult


def _r(case_id: str, expected: str, extracted: str | None) -> TestResult:
    """TestResult con passed derivado igual que el evaluador (exact match)."""
    passed = None if extracted is None else extracted == expected
    return TestResult(
        case_id=case_id,
        expected=expected,
        actual_response="...",
        extracted_classification=extracted,
        passed=passed,
    )


def _run(*results: TestResult) -> SuiteResult:
    return SuiteResult.create(results, agent_id="agent-x")


def test_confusion_matrix_counts_match_manual_count() -> None:
    # SC-001: conteo conocido. Verde→Verde (acierto), Verde→Rojo, Rojo→Rojo.
    metrics = compute_suite_metrics(
        _run(
            _r("c1", "Verde", "Verde"),
            _r("c2", "Verde", "Rojo"),
            _r("c3", "Rojo", "Rojo"),
        )
    )
    assert metrics.confusion["Verde"]["Verde"] == 1
    assert metrics.confusion["Verde"]["Rojo"] == 1
    assert metrics.confusion["Rojo"]["Rojo"] == 1
    assert metrics.confusion["Amarillo"]["Amarillo"] == 0


def test_matrix_axes_use_full_palette_including_rechazado() -> None:
    # Ejes 5x5: filas = paleta (5), columnas = paleta + sin clasificacion (6).
    metrics = compute_suite_metrics(_run(_r("c1", "Rechazado", "Rechazado")))
    assert set(metrics.confusion.keys()) == {
        "Verde",
        "Amarillo",
        "Rojo",
        "Negro",
        "Rechazado",
    }
    for row in metrics.confusion.values():
        assert set(row.keys()) == {
            "Verde",
            "Amarillo",
            "Rojo",
            "Negro",
            "Rechazado",
            SIN_CLASIFICACION,
        }
    assert metrics.confusion["Rechazado"]["Rechazado"] == 1


def test_indeterminate_falls_in_sin_clasificacion_column() -> None:
    # Decisión 2026-05-27: los indeterminados son columna extra, no se pierden.
    metrics = compute_suite_metrics(_run(_r("c1", "Verde", None), _r("c2", "Rojo", None)))
    assert metrics.confusion["Verde"][SIN_CLASIFICACION] == 1
    assert metrics.confusion["Rojo"][SIN_CLASIFICACION] == 1


def test_matrix_cells_sum_to_total() -> None:
    run = _run(
        _r("c1", "Verde", "Verde"),
        _r("c2", "Amarillo", "Rojo"),
        _r("c3", "Negro", None),
    )
    metrics = compute_suite_metrics(run)
    suma = sum(v for row in metrics.confusion.values() for v in row.values())
    assert suma == metrics.total == 3


def test_accuracy_por_clase() -> None:
    # SC-001: Verde con 2 casos, 1 acierto → 0.5; Rojo con 1 caso acertado → 1.0.
    metrics = compute_suite_metrics(
        _run(
            _r("c1", "Verde", "Verde"),
            _r("c2", "Verde", "Rojo"),
            _r("c3", "Rojo", "Rojo"),
        )
    )
    assert metrics.accuracy_por_clase["Verde"] == 0.5
    assert metrics.accuracy_por_clase["Rojo"] == 1.0


def test_accuracy_global_matches_pass_over_total() -> None:
    metrics = compute_suite_metrics(
        _run(
            _r("c1", "Verde", "Verde"),
            _r("c2", "Verde", "Rojo"),
            _r("c3", "Rojo", None),
        )
    )
    assert metrics.accuracy_global == 1 / 3


def test_empty_class_accuracy_is_none_not_zero_division() -> None:
    # Edge: clase esperada con 0 casos → N/A (None), sin división por cero.
    metrics = compute_suite_metrics(_run(_r("c1", "Verde", "Verde")))
    assert metrics.accuracy_por_clase["Verde"] == 1.0
    assert metrics.accuracy_por_clase["Amarillo"] is None
    assert metrics.accuracy_por_clase["Negro"] is None


def test_single_case_run_computes_without_error() -> None:
    # Edge: run de un solo caso, matriz mayormente vacía.
    metrics = compute_suite_metrics(_run(_r("c1", "Amarillo", "Amarillo")))
    assert metrics.total == 1
    assert metrics.confusion["Amarillo"]["Amarillo"] == 1


def test_sin_clasificacion_ratio_reported() -> None:
    # SC-002: % sin clasificación extraíble reportado aparte.
    metrics = compute_suite_metrics(
        _run(
            _r("c1", "Verde", "Verde"),
            _r("c2", "Rojo", None),
            _r("c3", "Negro", None),
            _r("c4", "Amarillo", "Amarillo"),
        )
    )
    assert metrics.sin_clasificacion_count == 2
    assert metrics.sin_clasificacion_ratio == 0.5


def test_empty_run_metrics_are_none() -> None:
    metrics = compute_suite_metrics(_run())
    assert metrics.total == 0
    assert metrics.accuracy_global is None
    assert metrics.sin_clasificacion_ratio is None
    assert all(v is None for v in metrics.accuracy_por_clase.values())


def test_metrics_computed_from_persisted_run_without_agent() -> None:
    # SC-003: se computan sobre un run persistido (round-trip), sin invocar al agente.
    original = _run(
        _r("c1", "Verde", "Verde"),
        _r("c2", "Rojo", "Negro"),
        _r("c3", "Negro", None),
    )
    restored = SuiteResult.from_dict(original.to_dict())
    metrics = compute_suite_metrics(restored)
    assert metrics.confusion["Verde"]["Verde"] == 1
    assert metrics.confusion["Rojo"]["Negro"] == 1
    assert metrics.confusion["Negro"][SIN_CLASIFICACION] == 1
    assert metrics.sin_clasificacion_count == 1


def test_aggregate_metrics_sums_cases_across_runs() -> None:
    # La matriz agregada trata todos los TestResult como una sola población.
    run_a = _run(_r("c1", "Verde", "Verde"), _r("c2", "Verde", "Rojo"))
    run_b = _run(_r("c3", "Verde", "Verde"), _r("c4", "Rojo", None))
    metrics = aggregate_suite_metrics((run_a, run_b))
    assert metrics.total == 4
    assert metrics.confusion["Verde"]["Verde"] == 2
    assert metrics.confusion["Verde"]["Rojo"] == 1
    assert metrics.confusion["Rojo"][SIN_CLASIFICACION] == 1
    # accuracy global agregado = 2 pass / 4 total
    assert metrics.accuracy_global == 0.5
    # accuracy por clase Verde = 2 aciertos / 3 casos
    assert metrics.accuracy_por_clase["Verde"] == 2 / 3
    assert metrics.sin_clasificacion_count == 1


def test_aggregate_metrics_empty_is_none() -> None:
    metrics = aggregate_suite_metrics(())
    assert metrics.total == 0
    assert metrics.accuracy_global is None
    assert metrics.sin_clasificacion_ratio is None
    assert all(v is None for v in metrics.accuracy_por_clase.values())


def test_metrics_to_dict_round_trips_structure() -> None:
    metrics = compute_suite_metrics(_run(_r("c1", "Verde", "Verde")))
    d = metrics.to_dict()
    assert d["confusion"]["Verde"]["Verde"] == 1
    assert d["accuracy_global"] == 1.0
    assert d["accuracy_por_clase"]["Verde"] == 1.0
    assert d["total"] == 1
