"""Persistencia de corridas en filesystem (SPEC-005, ADR-004).

Implementacion concreta del puerto RunRepository. Separa el detalle de
cada corrida (un archivo estructurado por corrida en runs/detail/) de la
estadistica por caso (runs/stats/estadistica-casos.csv, append).

El formato de serializacion queda confinado aqui; el identificador de la
clase no lo nombra (ver specs/SPEC-000-naming.md).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from src.domain.result import SuiteResult, aggregate_runs

_DEFAULT_ROOT = Path("runs")
_DETAIL_SUBDIR = "detail"
_STATS_SUBDIR = "stats"
_STATS_DELIMITER = ";"
_CASE_STATS_FILENAME = "estadistica-casos.csv"
_CASE_STATS_COLUMNS: tuple[str, ...] = (
    "run_id",
    "timestamp",
    "case_id",
    "expected",
    "extracted_classification",
    "verdict",
)
_MATRIX_STATS_FILENAME = "estadistica-matriz.csv"
_RUN_STATS_FILENAME = "estadistica-corridas.csv"
_RUN_STATS_COLUMNS: tuple[str, ...] = (
    "run_id",
    "timestamp",
    "agent_id",
    "endpoint_url",
    "total",
    "pass",
    "fail",
    "indeterminado",
    "accuracy_bruta",
    "accuracy_efectiva",
)


def _fmt(value: float | None) -> str:
    """Serializa un accuracy para la planilla: vacío si es None (denominador cero)."""
    return "" if value is None else f"{value:.4f}"


class RunPersistenceError(RuntimeError):
    """Fallo al persistir o recuperar una corrida."""


class FileRunRepository:
    """Persiste corridas en disco bajo un directorio raiz (por defecto runs/)."""

    def __init__(self, root: Path | str = _DEFAULT_ROOT) -> None:
        self._root = Path(root)

    @property
    def _detail_dir(self) -> Path:
        return self._root / _DETAIL_SUBDIR

    @property
    def _stats_dir(self) -> Path:
        return self._root / _STATS_SUBDIR

    def save(self, run: SuiteResult) -> str:
        try:
            self._detail_dir.mkdir(parents=True, exist_ok=True)
            self._stats_dir.mkdir(parents=True, exist_ok=True)
            detail_path = self._detail_path(run)
            detail_path.write_text(
                json.dumps(run.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self._append_case_stats(run)
        except OSError as exc:
            raise RunPersistenceError(
                f"No se pudo persistir la corrida {run.run_id}: {exc}"
            ) from exc
        return str(detail_path)

    def save_metrics_report(self, content: str) -> str:
        """Escribe el reporte de métricas total (matriz + resumen) en runs/stats/.

        Sobrescribe el archivo en cada llamada y devuelve su ruta. El formato
        del contenido lo decide el llamador; aquí solo se persiste."""
        try:
            self._stats_dir.mkdir(parents=True, exist_ok=True)
            path = self._stats_dir / _MATRIX_STATS_FILENAME
            path.write_text(content, encoding="utf-8")
        except OSError as exc:
            raise RunPersistenceError(f"No se pudo escribir el reporte de métricas: {exc}") from exc
        return str(path)

    def load(self, run_id: str) -> SuiteResult:
        # Acepta tanto el detalle batch ('run-<ts>.json') como el unitario
        # ('run-<ts>-<case_id>.json').
        matches = sorted(self._detail_dir.glob(f"{run_id}.json")) + sorted(
            self._detail_dir.glob(f"{run_id}-*.json")
        )
        if not matches:
            raise RunPersistenceError(f"No se encontro corrida con run_id '{run_id}'.")
        try:
            data = json.loads(matches[0].read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RunPersistenceError(f"No se pudo leer la corrida {run_id}: {exc}") from exc
        return SuiteResult.from_dict(data)

    def load_latest(self) -> SuiteResult | None:
        """Devuelve la corrida persistida mas reciente, o None si no hay (FR-007)."""
        if not self._detail_dir.exists():
            return None
        matches = sorted(self._detail_dir.glob("run-*.json"))
        if not matches:
            return None
        try:
            data = json.loads(matches[-1].read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RunPersistenceError(f"No se pudo leer la corrida mas reciente: {exc}") from exc
        return SuiteResult.from_dict(data)

    def load_all(self) -> list[SuiteResult]:
        """Reconstruye todas las corridas persistidas, ordenadas por run_id."""
        if not self._detail_dir.exists():
            return []
        runs: list[SuiteResult] = []
        for path in sorted(self._detail_dir.glob("run-*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise RunPersistenceError(f"No se pudo leer {path.name}: {exc}") from exc
            runs.append(SuiteResult.from_dict(data))
        return runs

    def regenerate_run_stats(self) -> str:
        """Regenera por completo estadistica-corridas.csv desde runs/detail/ (FR-009b).

        Idempotente: relee todas las corridas y reescribe el archivo entero, sin
        invocar al agente. Devuelve la ruta del archivo escrito.
        """
        runs = self.load_all()
        try:
            self._stats_dir.mkdir(parents=True, exist_ok=True)
            stats_path = self._stats_dir / _RUN_STATS_FILENAME
            with stats_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle, delimiter=_STATS_DELIMITER)
                writer.writerow(_RUN_STATS_COLUMNS)
                for run in runs:
                    s = run.summary
                    writer.writerow(
                        [
                            run.run_id,
                            run.timestamp,
                            run.agent_id,
                            run.endpoint_url,
                            s["total"],
                            s["pass"],
                            s["fail"],
                            s["indeterminado"],
                            _fmt(run.accuracy_bruta),
                            _fmt(run.accuracy_efectiva),
                        ]
                    )
                if runs:
                    overall = aggregate_runs(runs)
                    writer.writerow(
                        [
                            "TOTAL",
                            "",
                            "",
                            # endpoint_url: vacio en el agregado, puede mezclar
                            # endpoints distintos (SPEC-013 FR-US2-003/005).
                            "",
                            overall.total,
                            overall.passed,
                            overall.failed,
                            overall.indeterminate,
                            _fmt(overall.accuracy_bruta),
                            _fmt(overall.accuracy_efectiva),
                        ]
                    )
        except OSError as exc:
            msg = f"No se pudo regenerar la estadística de corridas: {exc}"
            raise RunPersistenceError(msg) from exc
        return str(stats_path)

    def _detail_path(self, run: SuiteResult) -> Path:
        # El sufijo de case_id sólo se usa cuando la corrida identifica un único
        # caso (modo unitario). En batch (N≠1) el archivo lleva sólo el run_id,
        # porque la corrida representa muchos casos, no uno.
        if len(run.results) == 1:
            return self._detail_dir / f"{run.run_id}-{run.results[0].case_id}.json"
        return self._detail_dir / f"{run.run_id}.json"

    def _append_case_stats(self, run: SuiteResult) -> None:
        stats_path = self._stats_dir / _CASE_STATS_FILENAME
        write_header = not stats_path.exists()
        with stats_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter=_STATS_DELIMITER)
            if write_header:
                writer.writerow(_CASE_STATS_COLUMNS)
            for r in run.results:
                detected = (
                    r.extracted_classification if r.extracted_classification is not None else ""
                )
                writer.writerow(
                    [run.run_id, run.timestamp, r.case_id, r.expected, detected, r.verdict]
                )
