"""Resultados de evaluacion del dominio.

Modelos inmutables y serializables que produce el ClassificationEvaluator
para cada caso evaluado. Sin dependencias externas.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from src.domain.agent_trace import AgentTrace


@dataclass(frozen=True, slots=True)
class TestResult:
    """Resultado de evaluar un caso contra la respuesta del agente."""

    __test__ = False  # evita coleccion como clase de test por pytest

    case_id: str
    expected: str
    actual_response: str
    extracted_classification: str | None
    passed: bool | None
    conversation_id: str | None = None
    notes: str = ""
    trace: AgentTrace | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "expected": self.expected,
            "actual_response": self.actual_response,
            "extracted_classification": self.extracted_classification,
            "passed": self.passed,
            "verdict": self.verdict,
            "conversation_id": self.conversation_id,
            "notes": self.notes,
            "trace": self.trace.to_dict() if self.trace is not None else None,
        }

    @property
    def flow_id(self) -> str | None:
        """Identificador del flow para localizar la ejecución en la plataforma."""
        return self.trace.flow_id if self.trace is not None else None

    @property
    def verdict(self) -> str:
        """Etiqueta legible: 'pass', 'fail' o 'indeterminado'."""
        if self.passed is True:
            return "pass"
        if self.passed is False:
            return "fail"
        return "indeterminado"


@dataclass(frozen=True, slots=True)
class SuiteResult:
    """Agregado de una corrida: uno o mas TestResult con metadata.

    En modo unitario (SPEC-005) envuelve un unico TestResult; en batch
    (SPEC-006) envuelve N. Expone los totales por veredicto. Ver ADR-004.
    """

    run_id: str
    timestamp: str
    agent_id: str
    results: tuple[TestResult, ...]
    endpoint_url: str = ""

    @classmethod
    def create(
        cls,
        results: tuple[TestResult, ...],
        agent_id: str,
        moment: datetime | None = None,
        token: str | None = None,
        endpoint_url: str = "",
    ) -> SuiteResult:
        """Construye una corrida derivando run_id/timestamp del instante dado.

        El instante es un dato puro (no I/O): por defecto el ahora en UTC.
        run_id sigue el patron de ADR-004: 'run-YYYYMMDDTHHMMSS-<token>'. El
        token es un sufijo unico corto que evita la colision de dos corridas
        que terminan en el mismo segundo (p. ej. dos sesiones simultaneas
        escribiendo en runs/): el prefijo de timestamp preserva el orden por
        recencia y el token garantiza unicidad. Por defecto se genera; se
        puede inyectar para obtener un run_id determinista en los tests, igual
        que `moment`.
        """
        when = moment or datetime.now(UTC)
        unique = token if token is not None else uuid4().hex[:8]
        run_id = "run-" + when.strftime("%Y%m%dT%H%M%S") + "-" + unique
        return cls(
            run_id=run_id,
            timestamp=when.isoformat(),
            agent_id=agent_id,
            results=tuple(results),
            endpoint_url=endpoint_url,
        )

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.verdict == "pass")

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.verdict == "fail")

    @property
    def indeterminate_count(self) -> int:
        return sum(1 for r in self.results if r.verdict == "indeterminado")

    @property
    def summary(self) -> dict[str, int]:
        return {
            "total": self.total,
            "pass": self.passed_count,
            "fail": self.failed_count,
            "indeterminado": self.indeterminate_count,
        }

    @property
    def accuracy_bruta(self) -> float | None:
        """pass / total. None si la corrida no tiene casos (SPEC-006 FR-007)."""
        if self.total == 0:
            return None
        return self.passed_count / self.total

    @property
    def accuracy_efectiva(self) -> float | None:
        """pass / (total - indeterminado). None si el denominador es cero (FR-008)."""
        evaluables = self.total - self.indeterminate_count
        if evaluables == 0:
            return None
        return self.passed_count / evaluables

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
            "endpoint_url": self.endpoint_url,
            "cases": [r.to_dict() for r in self.results],
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SuiteResult:
        """Reconstruye una corrida desde su forma serializada (round-trip)."""
        cases = tuple(
            TestResult(
                case_id=c["case_id"],
                expected=c["expected"],
                actual_response=c["actual_response"],
                extracted_classification=c["extracted_classification"],
                passed=c["passed"],
                conversation_id=c.get("conversation_id"),
                notes=c.get("notes", ""),
                trace=AgentTrace.from_dict(c["trace"]) if c.get("trace") is not None else None,
            )
            for c in data["cases"]
        )
        return cls(
            run_id=data["run_id"],
            timestamp=data["timestamp"],
            agent_id=data["agent_id"],
            results=cases,
            # Retrocompat (SPEC-013 FR-US2-002): corridas previas al campo no
            # traen la clave; se leen con endpoint_url vacio sin romper el round-trip.
            endpoint_url=data.get("endpoint_url", ""),
        )


@dataclass(frozen=True, slots=True)
class OverallStats:
    """Totales agregados sobre todos los casos de varias corridas (SPEC-006).

    Suma los casos de N corridas y computa el accuracy global como si todos
    los `TestResult` pertenecieran a una sola población.
    """

    total: int
    passed: int
    failed: int
    indeterminate: int

    @property
    def accuracy_bruta(self) -> float | None:
        if self.total == 0:
            return None
        return self.passed / self.total

    @property
    def accuracy_efectiva(self) -> float | None:
        evaluables = self.total - self.indeterminate
        if evaluables == 0:
            return None
        return self.passed / evaluables


def aggregate_runs(runs: Iterable[SuiteResult]) -> OverallStats:
    """Suma los casos de todas las corridas en un único total global."""
    materialized = tuple(runs)
    return OverallStats(
        total=sum(r.total for r in materialized),
        passed=sum(r.passed_count for r in materialized),
        failed=sum(r.failed_count for r in materialized),
        indeterminate=sum(r.indeterminate_count for r in materialized),
    )
