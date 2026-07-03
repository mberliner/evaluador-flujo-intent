"""Cliente sincrono del agente bajo test (SPEC-013).

Implementa el puerto AgentClient del dominio contra una plataforma
alternativa REST que responde en una sola llamada (sin thread nativo).
Encapsula la diferencia sync/async del transporte (FR-012): simula el
ciclo conversacional con un conversation_id sintetico y cache local,
de forma transparente para run_one, el dashboard y el runner.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import requests

from src.adapters.platform_config import PlatformConfig
from src.domain.agent_trace import AgentTrace, TraceStep
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

# Resumen de bloque acotado, consistente con SPEC-007 FR-010 (FR-US3-005).
_SUMMARY_MAX_CHARS = 800

# Orden fijo del pipeline (FR-US3-003), independiente del orden de claves del
# body. Cada tupla: (step_id agnostico y estable, clave del contrato del
# proveedor confinada al adapter, etiqueta legible agnostica). Los bloques
# reales llevan prefijo output_ (verificado 2026-07-03, FR-US1-011).
_PIPELINE_STAGES: tuple[tuple[str, str, str], ...] = (
    ("integridad", "output_integridad", "Integridad"),
    ("impacto", "output_impacto", "Impacto"),
    ("factibilidad", "output_factibilidad", "Factibilidad"),
    ("fastgate", "output_fastgate", "Clasificación"),
    ("redactor_mail", "output_redactor_mail", "Redacción de correo"),
)


def _has_content(value: Any) -> bool:
    """El bloque llego con contenido no vacio (FR-US3-004), decidido solo por
    presencia/contenido, sin leer campos internos (agnostico a la forma)."""
    if value is None:
        return False
    if isinstance(value, (dict, list, str, tuple, set)):
        return len(value) > 0
    return True


def _summarize(value: Any) -> str:
    """Serializa el bloque tal cual venga, acotado (FR-US3-005); sin asumir claves."""
    if value is None:
        return ""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    text = text.strip()
    if len(text) > _SUMMARY_MAX_CHARS:
        return text[:_SUMMARY_MAX_CHARS] + "…"
    return text


def _synthesize_steps(body: dict[str, Any]) -> tuple[TraceStep, ...]:
    """Un TraceStep por etapa del pipeline, en orden fijo (FR-US3-003/004/005).

    Estado por presencia/contenido: bloque con contenido -> completed; ausente,
    null o vacio -> skipped. Nunca failed (un false de negocio no es fallo
    tecnico, Principio III). Campos sin dato nativo (tiempos, child_flow) -> None.
    """
    steps: list[TraceStep] = []
    for step_id, block_key, agent_name in _PIPELINE_STAGES:
        block = body.get(block_key)
        present = _has_content(block)
        steps.append(
            TraceStep(
                step_id=step_id,
                agent_name=agent_name,
                status="completed" if present else "skipped",
                output_summary=_summarize(block) if present else "",
            )
        )
    return tuple(steps)


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
        # Cache del body crudo del pipeline para sintetizar la traza (FR-US3-001),
        # sin llamadas de red extra: get_trace opera sobre lo obtenido en send.
        self._bodies: dict[str, dict[str, Any]] = {}

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
        self._bodies[synthetic_id] = data
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
        """Sintetiza la traza desde el body cacheado en send (FR-US3-002).

        Revisa la conducta de FR-002 para el cliente sincrono: de traza vacia a
        traza sintetizada del pipeline. Sin llamadas de red: opera sobre lo
        obtenido en send. Fallo tecnico o thread_id sin cache -> steps vacios,
        sin excepcion (FR-US3-007, consistente con SPEC-007 FR-009).
        """
        body = self._bodies.get(thread_id)
        if body is None:
            return AgentTrace(thread_id=thread_id, flow_id=None, overall_status="unknown", steps=())
        return AgentTrace(
            thread_id=thread_id,
            flow_id=None,
            overall_status="completed",
            steps=_synthesize_steps(body),
        )
