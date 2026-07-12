"""Orquestador headless de la suite (SPEC-006 US1).

Compone build + adapters + domain + persistencia para ejecutar una o más
casos contra el agente sin interfaz gráfica. No es importado por `domain/`
y no depende del framework de UI.

Uso:
    python -m src.runner --in casos.csv --out runs/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.adapters.file_run_repository import FileRunRepository, RunPersistenceError
from src.adapters.platform_config import PlatformConfig
from src.adapters.remote_agent_client import RemoteAgentClient
from src.adapters.token_provider import TokenProvider
from src.application.generate_metrics_report import generate_metrics_report, total_metrics_title
from src.application.run_suite import build_suite, execution_failure, run_batch, run_one
from src.build.batch_loader import BatchLoadError, load_batch
from src.domain.classification_evaluator import ClassificationEvaluator
from src.domain.metrics import SIN_CLASIFICACION, SuiteMetrics, aggregate_suite_metrics
from src.domain.result import TestResult
from src.domain.test_case import PALETA_CLASIFICACION

# Los use-cases de orquestación viven en src/application/run_suite.py (ADR-005); el
# runner es composition root y entrypoint headless. Se re-exportan por compatibilidad.
__all__ = ["build_suite", "execution_failure", "main", "run_batch", "run_one"]


def _md_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    """Tabla Markdown alineada (col 0 a la izquierda, resto a la derecha)."""
    widths = [max(len(headers[i]), *(len(r[i]) for r in rows)) for i in range(len(headers))]

    def cells(values: list[str]) -> str:
        padded = [
            v.ljust(widths[i]) if i == 0 else v.rjust(widths[i]) for i, v in enumerate(values)
        ]
        return "| " + " | ".join(padded) + " |"

    sep = (
        "| "
        + " | ".join(
            (":" + "-" * (widths[i] - 1)) if i == 0 else ("-" * (widths[i] - 1) + ":")
            for i in range(len(headers))
        )
        + " |"
    )
    return [cells(headers), sep, *(cells(r) for r in rows)]


def format_metrics_markdown(metrics: SuiteMetrics, title: str) -> str:
    """Reporte en Markdown (tablas legibles a simple vista) de la matriz de
    confusión más el resumen de estadística. Función pura, sin I/O."""
    cols = (*PALETA_CLASIFICACION, SIN_CLASIFICACION)

    def num(value: float | None) -> str:
        return "N/A" if value is None else f"{value:.4f}"

    lines = [f"## {title}", ""]
    matrix_rows = [
        [esperado, *(str(metrics.confusion[esperado][c]) for c in cols)]
        for esperado in PALETA_CLASIFICACION
    ]
    lines += _md_table(["esperado \\ detectado", *cols], matrix_rows)

    lines += ["", "### Resumen de estadística", ""]
    lines += _md_table(
        ["métrica", "valor"],
        [
            ["total_casos", str(metrics.total)],
            ["accuracy_global", num(metrics.accuracy_global)],
            ["sin_clasificacion_casos", str(metrics.sin_clasificacion_count)],
            ["sin_clasificacion_ratio", num(metrics.sin_clasificacion_ratio)],
        ],
    )

    lines += ["", "### Accuracy por clase", ""]
    lines += _md_table(
        ["clase", "accuracy"],
        [[c, num(metrics.accuracy_por_clase[c])] for c in PALETA_CLASIFICACION],
    )

    return "\n".join(lines)


def _report_total_metrics(out_dir: str) -> int:
    """Modo exclusivo --estadistica: matriz total + resumen sobre todas las
    corridas guardadas. A pantalla en Markdown legible; a runs/stats/ en CSV.
    No ejecuta el batch."""
    repo = FileRunRepository(out_dir)
    try:
        runs = repo.load_all()
    except RunPersistenceError as exc:
        print(f"No se pudieron leer las corridas: {exc}", file=sys.stderr)
        return 1
    if not runs:
        print(f"No hay corridas guardadas en '{out_dir}'.", file=sys.stderr)
        return 1

    metrics = aggregate_suite_metrics(runs)
    title = total_metrics_title(runs)
    print(format_metrics_markdown(metrics, title))
    try:
        path = generate_metrics_report(repo, title)
        print(f"\nReporte CSV guardado en: {path}")
    except RunPersistenceError as exc:
        print(f"Reporte mostrado pero NO se pudo guardar el CSV: {exc}", file=sys.stderr)
    return 0


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ejecuta la suite de casos contra el agente.")
    parser.add_argument(
        "--in",
        dest="input_path",
        default=None,
        help="Archivo batch de casos (obligatorio salvo en modo --estadistica).",
    )
    parser.add_argument(
        "--out", dest="out_dir", default="runs", help="Directorio de salida / lectura de corridas."
    )
    parser.add_argument(
        "--estadistica",
        action="store_true",
        help=(
            "Modo exclusivo: calcula la matriz total y la estadística sobre todas las "
            "corridas guardadas en --out, la muestra a pantalla y la escribe en "
            "runs/stats/estadistica-matriz.csv. No ejecuta el batch ni llama al agente."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)

    if args.estadistica:
        return _report_total_metrics(args.out_dir)

    if not args.input_path:
        print(
            "Falta --in (archivo batch). Use --estadistica para el reporte total "
            "sin ejecutar la suite.",
            file=sys.stderr,
        )
        return 2

    input_path = Path(args.input_path)
    try:
        raw = input_path.read_bytes()
    except OSError as exc:
        print(f"No se pudo leer el archivo '{input_path}': {exc}", file=sys.stderr)
        return 1

    try:
        loaded = load_batch(raw)
    except BatchLoadError as exc:
        print(f"Archivo batch inválido: {exc}", file=sys.stderr)
        return 1

    for err in loaded.errors:
        print(f"[fila {err.line}] inválida: {err.message}", file=sys.stderr)
    if not loaded.cases:
        print("No hay casos válidos para ejecutar.", file=sys.stderr)
        return 1

    config = PlatformConfig.from_env()
    credentials = TokenProvider(config)
    client = RemoteAgentClient(config, credentials, timeout_seconds=120)
    evaluator = ClassificationEvaluator()

    print(f"Ejecutando {len(loaded.cases)} caso(s) (secuencial)...", flush=True)

    def _print_progress(index: int, total: int, result: TestResult) -> None:
        print(f"  [{index}/{total}] {result.case_id} -> {result.verdict}", flush=True)

    suite = build_suite(
        loaded.cases, client, evaluator, agent_id=config.agent_id, on_result=_print_progress
    )

    requested = len(loaded.cases)
    if suite.total < requested:
        # Parada manual (FR-US3-002): la corrida se cierra con lo completado;
        # el caso en vuelo y los pendientes quedan fuera.
        print(
            f"\nFrenado manual: {suite.total} de {requested} caso(s) completado(s). "
            "El caso en vuelo y los restantes no forman parte de la corrida.",
            flush=True,
        )
    if suite.total == 0:
        print("No se completó ningún caso; no se persiste una corrida vacía.", file=sys.stderr)
        return 1

    saved_path = FileRunRepository(args.out_dir).save(suite)

    s = suite.summary
    print(f"Corrida {suite.run_id}: {s['pass']}/{s['total']} pass, ", end="")
    print(f"{s['fail']} fail, {s['indeterminado']} indeterminado")
    print(f"accuracy_bruta={suite.accuracy_bruta} accuracy_efectiva={suite.accuracy_efectiva}")
    print(f"Detalle guardado en: {saved_path}")
    if loaded.errors:
        print(f"Filas inválidas omitidas: {len(loaded.errors)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
