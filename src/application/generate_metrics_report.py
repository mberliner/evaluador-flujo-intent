"""Caso de uso: generar y persistir el reporte de métricas (SPEC-008 FR-010).

Orquesta domain (aggregate_suite_metrics, format_metrics_report) con el
repositorio (puerto RunRepository) para producir y guardar estadistica-matriz.csv.
Usado tanto por el runner headless (--estadistica) como por el dashboard.
Sin I/O propio ni dependencias de UI, CLI ni adaptadores concretos.
"""

from __future__ import annotations

from src.domain.metrics import aggregate_suite_metrics, format_metrics_report
from src.domain.ports import RunRepository


def generate_metrics_report(repo: RunRepository, title: str) -> str:
    """Agrega métricas de todas las corridas guardadas y persiste el CSV.

    Devuelve la ruta del archivo escrito. Lanza ValueError si no hay corridas.
    """
    runs = repo.load_all()
    if not runs:
        raise ValueError("No hay corridas guardadas para generar el reporte.")
    metrics = aggregate_suite_metrics(runs)
    content = format_metrics_report(metrics, title)
    return repo.save_metrics_report(content)
