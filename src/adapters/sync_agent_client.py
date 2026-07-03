"""Cliente sincrono del agente bajo test (SPEC-013).

Implementa el puerto AgentClient del dominio contra una plataforma
alternativa REST que responde en una sola llamada (sin thread nativo).
Encapsula la diferencia sync/async del transporte (FR-012): simula el
ciclo conversacional con un conversation_id sintetico y cache local,
de forma transparente para run_one, el dashboard y el runner.
"""

from __future__ import annotations

import uuid
from typing import Any

import requests

from src.adapters.platform_config import PlatformConfig
from src.domain.agent_trace import AgentTrace
from src.domain.ports import AgentResponse, CredentialProvider

# Bloque de clasificacion final del pipeline de la plataforma
# (output_integridad -> output_impacto -> output_factibilidad -> bloque final).
# Conocimiento del contrato del proveedor confinado al adapter (ADR-001,
# SPEC-013 FR-011); clave verificada contra el endpoint real el 2026-07-03.
_FINAL_BLOCK_KEY = "output_fastgate"
_FINAL_COLOR_KEY = "clasificacion"

# Veredicto de negocio cuando un gate previo corto-circuita el pipeline
# (bloque final en null). Valor de PALETA_CLASIFICACION (FR-011).
_SHORT_CIRCUIT_VERDICT = "Rechazado"

_SYNTHETIC_ID_PREFIX = "sync-"


def _collapse(data: Any) -> str | None:
    """Colapsa la respuesta multi-etapa a un color unico (FR-011).

    - Bloque final presente con color legible -> pass-through del color, sin
      enumerar la paleta (la canonizacion es del ClassificationEvaluator).
    - Bloque final en null (corto-circuito de un gate previo) -> Rechazado.
    - Clave ausente o bloque sin color legible -> None: forma inesperada, se
      trata como fallo tecnico (FR-013), nunca como veredicto de negocio.
    """
    if not isinstance(data, dict) or _FINAL_BLOCK_KEY not in data:
        return None
    final_block = data[_FINAL_BLOCK_KEY]
    if final_block is None:
        return _SHORT_CIRCUIT_VERDICT
    if isinstance(final_block, dict):
        color = final_block.get(_FINAL_COLOR_KEY)
        if isinstance(color, str) and color.strip():
            return color.strip()
    return None


class SyncHttpAgentClient:
    """Adaptador sincrono REST con auth por header de llave (x-api-key)."""

    def __init__(
        self,
        config: PlatformConfig,
        credentials: CredentialProvider,
        *,
        session: requests.Session | None = None,
        timeout_seconds: int = 120,
    ) -> None:
        self._url = config.alt_client_url
        self._credentials = credentials
        self._session = session or requests.Session()
        self._timeout = timeout_seconds
        # Cache de veredictos colapsados por conversation_id sintetico (FR-012).
        self._verdicts: dict[str, str] = {}

    def send(self, form: dict[str, Any], conversation_id: str | None = None) -> AgentResponse:
        """Invocacion completa en una llamada: postea el form plano (FR-010),
        colapsa la respuesta (FR-011) y la cachea bajo un id sintetico (FR-012).

        Un fallo tecnico (red, no-200, forma inesperada) devuelve
        conversation_id=None para que run_one produzca Indeterminado (FR-013).
        """
        inner = form.get("form")
        if not isinstance(inner, dict):
            return AgentResponse(
                content="Payload sin clave 'form' esperada por MessageBuilder",
                conversation_id=None,
            )
        # Body plano en la raiz, sin envoltorio 'form' ni 'id' del caso (FR-010).
        body = {key: value for key, value in inner.items() if key != "id"}

        headers = {
            "x-api-key": self._credentials.get(),
            "Content-Type": "application/json",
        }
        try:
            response = self._session.post(
                self._url,
                json=body,
                headers=headers,
                timeout=self._timeout,
            )
        except requests.RequestException as err:
            return AgentResponse(content=f"Error conexion: {err}", conversation_id=None)

        if response.status_code != 200:
            return AgentResponse(
                content=f"Error API: {response.status_code}",
                conversation_id=None,
            )

        try:
            data = response.json()
        except ValueError as err:
            return AgentResponse(
                content=f"Respuesta sin formato esperado: {err}",
                conversation_id=None,
            )

        verdict = _collapse(data)
        if verdict is None:
            return AgentResponse(
                content="Respuesta sin formato esperado: falta el bloque de clasificacion",
                conversation_id=None,
            )

        synthetic_id = f"{_SYNTHETIC_ID_PREFIX}{uuid.uuid4().hex}"
        self._verdicts[synthetic_id] = verdict
        return AgentResponse(content=verdict, conversation_id=synthetic_id)

    def wait_for_completion(self, thread_id: str, timeout_seconds: int = 300) -> bool:
        """El transporte es sincrono: al volver de send el flow ya completo (FR-012)."""
        return True

    def get_thread_messages(self, thread_id: str) -> list[dict[str, Any]]:
        """La plataforma no tiene historial de thread nativo (FR-002)."""
        return []

    def get_final_response(self, thread_id: str, fallback_content: str) -> AgentResponse:
        """Devuelve el veredicto cacheado en send para ese id sintetico (FR-012)."""
        content = self._verdicts.get(thread_id, fallback_content)
        return AgentResponse(content=content, conversation_id=thread_id)

    def get_trace(self, thread_id: str) -> AgentTrace:
        """La plataforma no expone traza de sub-agentes: traza vacia (FR-002)."""
        return AgentTrace(thread_id=thread_id, flow_id=None, overall_status="unknown", steps=())
