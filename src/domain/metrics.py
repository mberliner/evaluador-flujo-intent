"""Métricas de suite: matriz de confusión y accuracy por clase (SPEC-008).

Funciones puras sobre los TestResult de una o varias corridas: sin I/O ni
dependencias externas. La matriz cruza la clasificación esperada (filas) contra
la detectada (columnas); los casos sin clasificación extraíble caen en una
columna aparte, de modo que cada caso ocupa exactamente una celda y la suma de
la matriz es el total.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from src.domain.result import SuiteResult, TestResult, aggregate_runs
from src.domain.test_case import PALETA_CLASIFICACION

# Columna de la matriz para casos cuya respuesta no produjo clasificación.
SIN_CLASIFICACION = "Sin clasificación"

_REPORT_SEPARATOR = ";"


def format_metrics_report(metrics: SuiteMetrics, title: str) -> str:
    """Genera el reporte CSV (delimitado por ';') de la matriz de confusión.

    Función pura: no imprime ni hace I/O. Usada por el caso de uso
    generate_metrics_report (application) tanto desde el dashboard como el CLI.
    """
    cols = (*PALETA_CLASIFICACION, SIN_CLASIFICACION)
    sep = _REPORT_SEPARATOR

    def num(value: float | None) -> str:
        return "N/A" if value is None else f"{value:.4f}"

    lines = [f"# {title}"]
    lines.append(sep.join(["esperado", *cols]))
    for esperado in PALETA_CLASIFICACION:
        lines.append(sep.join([esperado, *(str(metrics.confusion[esperado][c]) for c in cols)]))

    lines.append("")
    lines.append("# Resumen de estadística")
    lines.append(sep.join(["metrica", "valor"]))
    lines.append(sep.join(["total_casos", str(metrics.total)]))
    lines.append(sep.join(["accuracy_global", num(metrics.accuracy_global)]))
    lines.append(sep.join(["sin_clasificacion_casos", str(metrics.sin_clasificacion_count)]))
    lines.append(sep.join(["sin_clasificacion_ratio", num(metrics.sin_clasificacion_ratio)]))

    lines.append("")
    lines.append("# Accuracy por clase")
    lines.append(sep.join(["clase", "accuracy"]))
    for c in PALETA_CLASIFICACION:
        lines.append(sep.join([c, num(metrics.accuracy_por_clase[c])]))

    return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class SuiteMetrics:
    """Métricas analíticas sobre un conjunto de casos. Pura y serializable.

    - confusion[esperado][detectado]: conteo. Filas = PALETA_CLASIFICACION;
      columnas = PALETA_CLASIFICACION + SIN_CLASIFICACION.
    - accuracy_global: pass / total (None si total == 0).
    - accuracy_por_clase[color]: aciertos / casos de la clase (None = N/A: clase sin casos).
    - sin_clasificacion_count / _ratio: casos sin clasificación extraíble (% de PRODUCT.md).
    """

    confusion: dict[str, dict[str, int]]
    accuracy_global: float | None
    accuracy_por_clase: dict[str, float | None]
    sin_clasificacion_count: int
    sin_clasificacion_ratio: float | None
    total: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "confusion": {exp: dict(row) for exp, row in self.confusion.items()},
            "accuracy_global": self.accuracy_global,
            "accuracy_por_clase": dict(self.accuracy_por_clase),
            "sin_clasificacion_count": self.sin_clasificacion_count,
            "sin_clasificacion_ratio": self.sin_clasificacion_ratio,
            "total": self.total,
        }


def _build_metrics(results: Sequence[TestResult], accuracy_global: float | None) -> SuiteMetrics:
    """Arma la matriz, el accuracy por clase y el % sin clasificación.

    El accuracy global llega ya calculado por quien define la población (una
    corrida o el agregado de varias), para no duplicar la fórmula pass/total.
    """
    columnas: tuple[str, ...] = (*PALETA_CLASIFICACION, SIN_CLASIFICACION)
    confusion: dict[str, dict[str, int]] = {
        esperado: {col: 0 for col in columnas} for esperado in PALETA_CLASIFICACION
    }
    aciertos_por_clase: dict[str, int] = {c: 0 for c in PALETA_CLASIFICACION}
    casos_por_clase: dict[str, int] = {c: 0 for c in PALETA_CLASIFICACION}

    for r in results:
        detectado = r.extracted_classification or SIN_CLASIFICACION
        confusion[r.expected][detectado] += 1
        casos_por_clase[r.expected] += 1
        if r.passed is True:
            aciertos_por_clase[r.expected] += 1

    accuracy_por_clase: dict[str, float | None] = {
        c: (aciertos_por_clase[c] / casos_por_clase[c] if casos_por_clase[c] else None)
        for c in PALETA_CLASIFICACION
    }

    total = len(results)
    sin_clasificacion_count = sum(1 for r in results if r.extracted_classification is None)
    sin_clasificacion_ratio = sin_clasificacion_count / total if total else None

    return SuiteMetrics(
        confusion=confusion,
        accuracy_global=accuracy_global,
        accuracy_por_clase=accuracy_por_clase,
        sin_clasificacion_count=sin_clasificacion_count,
        sin_clasificacion_ratio=sin_clasificacion_ratio,
        total=total,
    )


def compute_suite_metrics(run: SuiteResult) -> SuiteMetrics:
    """Métricas de una sola corrida (matriz, accuracy por clase, % sin clasificación)."""
    return _build_metrics(run.results, run.accuracy_bruta)


def aggregate_suite_metrics(runs: Iterable[SuiteResult]) -> SuiteMetrics:
    """Métricas agregadas sobre todos los casos de varias corridas.

    Trata los TestResult de todas las corridas como una sola población. El
    accuracy global se toma de aggregate_runs (mismo cómputo que la fila TOTAL
    de estadistica-corridas.csv), sin duplicar la fórmula.
    """
    materialized = tuple(runs)
    all_results = tuple(r for run in materialized for r in run.results)
    return _build_metrics(all_results, aggregate_runs(materialized).accuracy_bruta)
