"""Puertos del dominio.

Definen los contratos que deben implementar los adapters. Permiten que el
dominio sea testeable sin red ni filesystem y desacoplan al sistema del
proveedor concreto (ver specs/SPEC-000-naming.md y docs/ARCHITECTURE.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from src.domain.agent_trace import AgentTrace
from src.domain.result import SuiteResult
from src.domain.test_case import TestCase


@dataclass(frozen=True, slots=True)
class AgentResponse:
    """Respuesta cruda del agente."""

    content: str
    conversation_id: str | None = None
    run_id: str | None = None


class AgentClient(Protocol):
    """Puerto para hablar con el agente bajo test."""

    def send(self, form: dict[str, Any], conversation_id: str | None = None) -> AgentResponse:
        """Envia el payload del agente (construido por MessageBuilder)."""
        ...

    def wait_for_completion(self, thread_id: str, timeout_seconds: int) -> bool:
        """Hace polling hasta que el flow completa. True=completado, False=fallo/timeout."""
        ...

    def get_thread_messages(self, thread_id: str) -> list[dict[str, Any]]:
        """Devuelve el historial crudo del thread sin transformar."""
        ...

    def get_final_response(self, thread_id: str, fallback_content: str) -> AgentResponse:
        """Devuelve la respuesta final del agente, descartando el control message.

        El conocimiento del control message del proveedor vive en el adapter
        (ver SPEC-002, ADR-001). Si ningún mensaje califica, usa fallback_content.
        """
        ...

    def get_trace(self, thread_id: str) -> AgentTrace:
        """Devuelve la traza interna de sub-agentes del run (SPEC-007)."""
        ...


class TestCaseRepository(Protocol):
    """Puerto para persistir y recuperar casos de prueba."""

    def load(self, case_id: str) -> TestCase:
        """Recupera un caso por id."""
        ...

    def save(self, case: TestCase) -> None:
        """Persiste un caso."""
        ...


class CredentialProvider(Protocol):
    """Puerto para obtener credenciales utilizables por el cliente del agente."""

    def get(self) -> str:
        """Devuelve un token valido (cacheado o refrescado segun corresponda)."""
        ...


class RunRepository(Protocol):
    """Puerto para persistir y recuperar corridas (ver SPEC-005, ADR-004)."""

    def save(self, run: SuiteResult) -> str:
        """Persiste la corrida y devuelve la ruta/id del detalle escrito."""
        ...

    def load(self, run_id: str) -> SuiteResult:
        """Reconstruye una corrida persistida por su run_id."""
        ...

    def load_all(self) -> list[SuiteResult]:
        """Devuelve todas las corridas persistidas."""
        ...

    def save_metrics_report(self, content: str) -> str:
        """Persiste el reporte CSV de métricas y devuelve la ruta escrita."""
        ...
