"""Cliente remoto del agente bajo test.

Implementa el puerto AgentClient del dominio.
"""

from __future__ import annotations

import json
import time
from typing import Any

import requests

from src.adapters.platform_config import PlatformConfig
from src.domain.agent_trace import TRACE_STEP_STATUSES, AgentTrace, TraceStep
from src.domain.message_text import extract_message_text
from src.domain.ports import AgentResponse, CredentialProvider

# Trigger del flow externo que dispara una conversacion (ver docs/AGENT-INVOCATION.md).
_OUTER_FLOW_TRIGGER = "flow_async_chat"

# Control message inmediato del proveedor: senala que el flow arranco, no es la
# clasificacion. Conocimiento del proveedor confinado al adapter (ADR-001, SPEC-002).
_CONTROL_MARKER = "a new flow has started"

# Mapeo de estados del proveedor a los estados de dominio (TRACE_STEP_STATUSES).
_STATUS_ALIASES: dict[str, str] = {
    "complete": "completed",
    "completed": "completed",
    "success": "completed",
    "succeeded": "completed",
    "done": "completed",
    "failed": "failed",
    "error": "failed",
    "fail": "failed",
    "in_progress": "in_progress",
    "running": "in_progress",
    "interrupted": "in_progress",
    "pending": "in_progress",
    "skipped": "skipped",
    "skip": "skipped",
}

_SUMMARY_MAX_CHARS = 800


def _normalize_status(raw: Any) -> str:
    """Traduce un estado del proveedor a un valor de TRACE_STEP_STATUSES."""
    key = str(raw).lower().strip()
    if key in TRACE_STEP_STATUSES:
        return key
    return _STATUS_ALIASES.get(key, "in_progress")


def _summarize(value: Any) -> str:
    """Resume un input/output (str/dict/list) a texto plano acotado."""
    if value is None:
        return ""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    text = text.strip()
    if len(text) > _SUMMARY_MAX_CHARS:
        return text[:_SUMMARY_MAX_CHARS] + "…"
    return text


def _flow_sort_key(flow: dict[str, Any]) -> str:
    """Marca temporal del flow para ordenar por recencia (ISO ordena lexicograficamente)."""
    for key in ("started_at", "created_at", "completed_at", "updated_at"):
        value = flow.get(key)
        if isinstance(value, str):
            return value
    return ""


def _sequence_order(flow: dict[str, Any]) -> list[str]:
    """Orden de ejecucion por nombre, desde sequence.steps (lista de grupos de nombres)."""
    sequence = flow.get("sequence")
    if not isinstance(sequence, dict):
        return []
    groups = sequence.get("steps")
    if not isinstance(groups, list):
        return []
    order: list[str] = []
    for group in groups:
        names = group if isinstance(group, list) else [group]
        order.extend(str(n) for n in names)
    return order


def _flow_steps(flow: dict[str, Any]) -> list[dict[str, Any]]:
    """Pasos del flow (clave `tasks`), ordenados segun `sequence.steps`."""
    raw = flow.get("tasks")
    tasks = [t for t in raw if isinstance(t, dict)] if isinstance(raw, list) else []
    order = _sequence_order(flow)
    if not order:
        return tasks
    rank = {name: i for i, name in enumerate(order)}
    return sorted(tasks, key=lambda t: rank.get(str(t.get("name")), len(rank)))


def _duration_ms(raw: dict[str, Any]) -> int | None:
    trace_context = raw.get("trace_context")
    if isinstance(trace_context, dict):
        value = trace_context.get("duration_ms")
        if isinstance(value, int):
            return value
    return None


def _map_step(index: int, raw: dict[str, Any]) -> TraceStep | None:
    """Mapea un paso del proveedor a TraceStep; None si no se puede construir."""
    agent_name = str(raw.get("name") or raw.get("agent_name") or raw.get("title") or "").strip()
    if not agent_name:
        return None
    step_id = str(
        raw.get("task_instance_id") or raw.get("id") or raw.get("step_id") or f"step-{index + 1}"
    )
    raw_child = raw.get("child_flow_instance_id")
    child_flow_id = str(raw_child) if raw_child else None
    try:
        return TraceStep(
            step_id=step_id,
            agent_name=agent_name,
            status=_normalize_status(raw.get("state") or raw.get("status")),
            input_summary=_summarize(raw.get("input")),
            output_summary=_summarize(raw.get("output")),
            started_at=raw.get("created_at") or raw.get("started_at"),
            completed_at=raw.get("updated_at") or raw.get("completed_at"),
            duration_ms=_duration_ms(raw),
            child_flow_id=child_flow_id,
        )
    except ValueError:
        return None


class RemoteAgentClient:
    def __init__(
        self,
        config: PlatformConfig,
        credentials: CredentialProvider,
        *,
        session: requests.Session | None = None,
        timeout_seconds: int = 200,
    ) -> None:
        self._config = config
        self._credentials = credentials
        self._session = session or requests.Session()
        self._timeout = timeout_seconds

    def send(self, form: dict[str, Any], conversation_id: str | None = None) -> AgentResponse:
        text = json.dumps(form, ensure_ascii=False)
        messages_block = [
            {
                "role": "user",
                "content": [
                    {"response_type": "text", "text": text},
                ],
            }
        ]
        payload: dict[str, object] = {}
        if conversation_id:
            payload["thread_id"] = conversation_id
        payload["messages"] = messages_block
        payload["stream"] = "false"

        url = f"{self._config.chat_url}{self._config.agent_id}/chat/completions"
        token = self._credentials.get()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            response = self._session.post(
                url,
                json=payload,
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

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as err:
            return AgentResponse(
                content=f"Respuesta sin formato esperado: {err}",
                conversation_id=None,
            )

        returned_conversation = data.get("thread_id") if isinstance(data, dict) else None
        returned_run = data.get("run_id") if isinstance(data, dict) else None
        return AgentResponse(
            content=str(content),
            conversation_id=returned_conversation,
            run_id=returned_run,
        )

    def wait_for_completion(
        self, thread_id: str, timeout_seconds: int = 300, poll_interval: int = 10
    ) -> bool:
        """Polling en /threads/{thread_id}/messages hasta que aparece la respuesta final.

        El agente emite un control message inmediato ("A new flow has started...")
        y luego, cuando el flow termina, agrega el mensaje de clasificacion al thread.
        Retorna True cuando aparece un mensaje assistant que no es el control message.
        """
        deadline = time.monotonic() + timeout_seconds

        while time.monotonic() < deadline:
            messages = self.get_thread_messages(thread_id)
            for msg in messages:
                if msg.get("role") != "assistant":
                    continue
                text = extract_message_text(msg.get("content", ""))
                if _CONTROL_MARKER not in text.lower():
                    return True
            time.sleep(poll_interval)

        return False

    def get_thread_messages(self, thread_id: str) -> list[dict[str, Any]]:
        """GET /threads/{thread_id}/messages. Devuelve lista cruda sin transformar."""
        url = f"{self._config.threads_url}/{thread_id}/messages"
        token = self._credentials.get()
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = self._session.get(url, headers=headers, timeout=self._timeout)
        except requests.RequestException:
            return []

        if response.status_code != 200:
            return []

        data: Any = response.json()
        if isinstance(data, list):
            return list(data)
        return list(data.get("messages", []))

    def get_final_response(self, thread_id: str, fallback_content: str) -> AgentResponse:
        """Respuesta final del agente: primer assistant que no es el control message.

        Encapsula el conocimiento del control message del proveedor (ADR-001,
        SPEC-002): los callers (`application.run_one`, dashboard) no lo conocen.
        Si ningún mensaje califica, devuelve `fallback_content`.
        """
        for msg in self.get_thread_messages(thread_id):
            if msg.get("role") != "assistant":
                continue
            text = extract_message_text(msg.get("content", ""))
            if _CONTROL_MARKER not in text.lower():
                return AgentResponse(content=text, conversation_id=thread_id)
        return AgentResponse(content=fallback_content, conversation_id=thread_id)

    def get_trace(self, thread_id: str) -> AgentTrace:
        """Mapea GET /flows al modelo de dominio (SPEC-007 FR-006/008/009).

        Correlacion simple: toma el flow externo (trigger flow_async_chat del
        agente bajo prueba) mas reciente. La correlacion exacta por run_id queda
        pendiente de verificacion empirica; nunca propaga errores (FR-009).
        """
        empty = AgentTrace(thread_id=thread_id, flow_id=None, overall_status="unknown", steps=())
        try:
            flow = self._select_flow(self._fetch_flows())
        except (requests.RequestException, ValueError, KeyError, TypeError):
            return empty
        if flow is None:
            return empty

        steps = tuple(
            step
            for step in (_map_step(i, raw) for i, raw in enumerate(_flow_steps(flow)))
            if step is not None
        )
        flow_id = flow.get("instance_id") or flow.get("id")
        overall = flow.get("state") or flow.get("status") or "unknown"
        return AgentTrace(
            thread_id=thread_id,
            flow_id=str(flow_id) if flow_id else None,
            overall_status=str(overall),
            steps=steps,
        )

    def _fetch_flows(self) -> list[dict[str, Any]]:
        token = self._credentials.get()
        headers = {"Authorization": f"Bearer {token}"}
        response = self._session.get(
            self._config.flows_url,
            headers=headers,
            params={"limit": 50},
            timeout=self._timeout,
        )
        if response.status_code != 200:
            return []
        data: Any = response.json()
        if isinstance(data, list):
            return [f for f in data if isinstance(f, dict)]
        if isinstance(data, dict):
            flows = data.get("flows", [])
            return [f for f in flows if isinstance(f, dict)] if isinstance(flows, list) else []
        return []

    def _select_flow(self, flows: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not flows:
            return None
        agent_id = self._config.agent_id
        candidates = [
            f
            for f in flows
            if f.get("trigger") == _OUTER_FLOW_TRIGGER and f.get("agent_id") == agent_id
        ]
        pool = candidates or flows
        return max(pool, key=_flow_sort_key)
