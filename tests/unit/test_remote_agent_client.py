"""Tests de RemoteAgentClient con stub de requests.Session."""

from __future__ import annotations

from typing import Any

from src.adapters.platform_config import PlatformConfig
from src.adapters.remote_agent_client import RemoteAgentClient


class _StubResponse:
    def __init__(self, status_code: int, payload: dict[str, Any] | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text or str(payload)

    def json(self) -> dict[str, Any]:
        return self._payload


class _StubSession:
    def __init__(self, responses: list[_StubResponse]):
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def post(self, url: str, **kwargs: Any) -> _StubResponse:
        self.calls.append({"method": "post", "url": url, **kwargs})
        return self._responses.pop(0)

    def get(self, url: str, **kwargs: Any) -> _StubResponse:
        self.calls.append({"method": "get", "url": url, **kwargs})
        return self._responses.pop(0)


class _StubCredentials:
    def get(self) -> str:
        return "token-stub"


def _config() -> PlatformConfig:
    return PlatformConfig(
        chat_url="https://example/chat/",
        token_url="https://example/token",
        agents_url="https://example/agents",
        flows_url="https://example/chat/flows",
        threads_url="https://example/chat/threads",
        api_key="apikey-xyz",
        agent_id="agent-1",
    )


_FORM = {"form": {"nombre_iniciativa": "Test"}}


def test_envio_sin_thread_id_no_incluye_thread() -> None:
    session = _StubSession(
        [
            _StubResponse(
                200,
                {
                    "choices": [{"message": {"content": "hola"}}],
                    "thread_id": "th-1",
                },
            )
        ]
    )
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    import json

    resp = client.send(_FORM)
    assert resp.content == "hola"
    assert resp.conversation_id == "th-1"
    payload = session.calls[0]["json"]
    assert "thread_id" not in payload
    assert payload["messages"][0]["content"][0]["text"] == json.dumps(_FORM, ensure_ascii=False)


def test_envio_con_thread_id_lo_incluye() -> None:
    session = _StubSession([_StubResponse(200, {"choices": [{"message": {"content": "ok"}}]})])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    client.send(_FORM, conversation_id="th-7")
    assert session.calls[0]["json"]["thread_id"] == "th-7"


def test_error_http_no_levanta_y_marca_content() -> None:
    session = _StubSession([_StubResponse(500, text="boom")])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    resp = client.send(_FORM)
    assert resp.content.startswith("Error API: 500")
    assert resp.conversation_id is None


def test_respuesta_malformada_devuelve_error_legible() -> None:
    session = _StubSession([_StubResponse(200, {"otra": "cosa"})])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    resp = client.send(_FORM)
    assert resp.content.startswith("Respuesta sin formato")


def test_url_compone_chat_y_agent_id() -> None:
    session = _StubSession([_StubResponse(200, {"choices": [{"message": {"content": "ok"}}]})])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    client.send(_FORM)
    assert session.calls[0]["url"] == "https://example/chat/agent-1/chat/completions"
    headers = session.calls[0]["headers"]
    assert headers["Authorization"] == "Bearer token-stub"


# ---------------------------------------------------------------------------
# wait_for_completion — polling de thread messages
# ---------------------------------------------------------------------------


def _tmsg(role: str, content: str | list) -> dict[str, Any]:
    return {"role": role, "content": content}


_CONTROL_MSG = _tmsg(
    "assistant",
    "A new flow has started. This chat session is currently dedicated to the flow.",
)
_FINAL_STR_MSG = _tmsg("assistant", "riesgo: VERDE\n\nFastGate Preguntas: 1. algo")
_FINAL_LIST_MSG = _tmsg("assistant", [{"response_type": "text", "text": "riesgo: NEGRO"}])


def test_wait_for_completion_retorna_true_cuando_hay_mensaje_final() -> None:
    msgs = [_CONTROL_MSG, _FINAL_STR_MSG]
    session = _StubSession([_StubResponse(200, msgs)])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    assert client.wait_for_completion("th-1", timeout_seconds=60, poll_interval=0) is True
    assert len(session.calls) == 1


def test_wait_for_completion_espera_hasta_que_llega_mensaje_final() -> None:
    session = _StubSession(
        [
            _StubResponse(200, [_CONTROL_MSG]),
            _StubResponse(200, [_CONTROL_MSG, _FINAL_STR_MSG]),
        ]
    )
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    assert client.wait_for_completion("th-1", timeout_seconds=60, poll_interval=0) is True
    assert len(session.calls) == 2


def test_wait_for_completion_acepta_content_como_lista() -> None:
    session = _StubSession([_StubResponse(200, [_FINAL_LIST_MSG])])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    assert client.wait_for_completion("th-1", timeout_seconds=60, poll_interval=0) is True


def test_wait_for_completion_ignora_mensajes_de_usuario() -> None:
    user_msg = _tmsg("user", "riesgo: VERDE")  # usuario — no cuenta
    session = _StubSession(
        [
            _StubResponse(200, [user_msg, _CONTROL_MSG]),
            _StubResponse(200, [user_msg, _CONTROL_MSG, _FINAL_STR_MSG]),
        ]
    )
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    assert client.wait_for_completion("th-1", timeout_seconds=60, poll_interval=0) is True
    assert len(session.calls) == 2


def test_wait_for_completion_retorna_false_si_agota_timeout() -> None:
    session = _StubSession([_StubResponse(200, [_CONTROL_MSG])])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    assert client.wait_for_completion("th-1", timeout_seconds=0, poll_interval=0) is False


# ---------------------------------------------------------------------------
# get_thread_messages
# ---------------------------------------------------------------------------


def test_get_thread_messages_devuelve_lista_cruda() -> None:
    msgs = [{"role": "user", "content": "hola"}, {"role": "assistant", "content": "riesgo: VERDE"}]
    session = _StubSession([_StubResponse(200, msgs)])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    result = client.get_thread_messages("th-1")
    assert result == msgs
    assert session.calls[0]["url"] == "https://example/chat/threads/th-1/messages"


def test_get_thread_messages_acepta_respuesta_envuelta_en_messages() -> None:
    msgs = [{"role": "assistant", "content": "riesgo: NEGRO"}]
    session = _StubSession([_StubResponse(200, {"messages": msgs})])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    assert client.get_thread_messages("th-1") == msgs


def test_get_thread_messages_devuelve_lista_vacia_en_error_http() -> None:
    session = _StubSession([_StubResponse(500, {})])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    assert client.get_thread_messages("th-1") == []


# ---------------------------------------------------------------------------
# get_final_response — selección de la respuesta final (SPEC-002, ADR-005)
# ---------------------------------------------------------------------------


def test_get_final_response_ignora_control_message() -> None:
    session = _StubSession([_StubResponse(200, [_CONTROL_MSG, _FINAL_STR_MSG])])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    response = client.get_final_response("th-1", "fallback")
    assert response.content == "riesgo: VERDE\n\nFastGate Preguntas: 1. algo"
    assert response.conversation_id == "th-1"


def test_get_final_response_normaliza_content_lista() -> None:
    session = _StubSession([_StubResponse(200, [_CONTROL_MSG, _FINAL_LIST_MSG])])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    assert client.get_final_response("th-1", "fallback").content == "riesgo: NEGRO"


def test_get_final_response_usa_fallback_si_solo_control() -> None:
    session = _StubSession([_StubResponse(200, [_CONTROL_MSG])])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    assert client.get_final_response("th-1", "fallback-content").content == "fallback-content"


# ---------------------------------------------------------------------------
# send — captura de run_id (SPEC-007 FR-007)
# ---------------------------------------------------------------------------


def test_send_captura_run_id_del_body() -> None:
    session = _StubSession(
        [
            _StubResponse(
                200,
                {
                    "choices": [{"message": {"content": "ok"}}],
                    "thread_id": "th-1",
                    "run_id": "9f942fe0-abc",
                },
            )
        ]
    )
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    resp = client.send(_FORM)
    assert resp.run_id == "9f942fe0-abc"


def test_send_sin_run_id_deja_none() -> None:
    session = _StubSession([_StubResponse(200, {"choices": [{"message": {"content": "ok"}}]})])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    assert client.send(_FORM).run_id is None


# ---------------------------------------------------------------------------
# get_trace — mapeo de /flows al dominio (SPEC-007 FR-006/008/009)
# ---------------------------------------------------------------------------


# Fixture con el shape REAL de /flows (verificado contra el agente 2026-05-27):
# estado en `state`, pasos en `tasks`, orden en `sequence.steps`, duracion en
# `trace_context.duration_ms`, id en `task_instance_id`, timestamps create/update.
def _task(name: str, state: str = "completed", dur_ms: int = 1000) -> dict[str, Any]:
    return {
        "task_instance_id": f"task-{name}",
        "name": name,
        "state": state,
        "input": {},
        "output": {"data": {"resultado": name}},
        "trace_context": {"duration_ms": dur_ms},
        "created_at": "2026-05-27T11:33:18.050Z",
        "updated_at": "2026-05-27T11:33:18.115Z",
    }


def _flow_with_steps() -> dict[str, Any]:
    return {
        "instance_id": "flow-instance-1",
        "trigger": "flow_async_chat",
        "agent_id": "agent-1",
        "state": "completed",
        "created_at": "2026-05-27T10:00:00.000Z",
        "sequence": {
            "steps": [
                ["cargar_iniciativa_v2"],
                ["FI - Agente validador de Intents"],
                ["__flow_end__"],
            ]
        },
        # `tasks` viene desordenado: get_trace lo ordena por sequence.steps.
        "tasks": [
            _task("__flow_end__", dur_ms=57),
            _task("FI - Agente validador de Intents", dur_ms=16011),
            _task("cargar_iniciativa_v2", dur_ms=2369),
            {"state": "completed"},  # sin nombre: se descarta
        ],
    }


def test_get_trace_mapea_flow_y_pasos() -> None:
    session = _StubSession([_StubResponse(200, {"flows": [_flow_with_steps()]})])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    trace = client.get_trace("th-1")
    assert trace.thread_id == "th-1"
    assert trace.flow_id == "flow-instance-1"
    assert trace.overall_status == "completed"
    # La tarea sin nombre se descarta; quedan 3 ordenadas por sequence.steps.
    assert [s.agent_name for s in trace.steps] == [
        "cargar_iniciativa_v2",
        "FI - Agente validador de Intents",
        "__flow_end__",
    ]
    first = trace.steps[0]
    assert first.status == "completed"  # `state` -> status (antes caia a in_progress)
    assert first.step_id == "task-cargar_iniciativa_v2"
    assert first.duration_ms == 2369
    assert first.output_summary  # resumido, no vacio


def test_get_trace_normaliza_estado_en_curso() -> None:
    flow = _flow_with_steps()
    flow["tasks"] = [_task("paso vivo", state="interrupted")]
    flow["sequence"] = {"steps": [["paso vivo"]]}
    session = _StubSession([_StubResponse(200, {"flows": [flow]})])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    assert client.get_trace("th-1").steps[0].status == "in_progress"


def test_get_trace_selecciona_flow_del_agente_mas_reciente() -> None:
    otro_agente = {**_flow_with_steps(), "agent_id": "agent-otro", "instance_id": "otro"}
    viejo = {**_flow_with_steps(), "instance_id": "viejo", "created_at": "2026-05-01T00:00:00.000Z"}
    nuevo = {**_flow_with_steps(), "instance_id": "nuevo", "created_at": "2026-05-27T23:59:59.000Z"}
    session = _StubSession([_StubResponse(200, {"flows": [otro_agente, viejo, nuevo]})])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    assert client.get_trace("th-1").flow_id == "nuevo"


def test_get_trace_sin_flows_devuelve_traza_vacia() -> None:
    session = _StubSession([_StubResponse(200, {"flows": []})])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    trace = client.get_trace("th-1")
    assert trace.steps == ()
    assert trace.thread_id == "th-1"


def test_get_trace_error_http_no_propaga() -> None:
    session = _StubSession([_StubResponse(500, {})])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    assert client.get_trace("th-1").steps == ()


def test_get_trace_mapea_child_flow_instance_id() -> None:
    flow = _flow_with_steps()
    for t in flow["tasks"]:
        if isinstance(t, dict) and t.get("name") == "FI - Agente validador de Intents":
            t["child_flow_instance_id"] = "inner-flow-uuid-123"
    session = _StubSession([_StubResponse(200, {"flows": [flow]})])
    client = RemoteAgentClient(
        _config(),
        _StubCredentials(),
        session=session,  # type: ignore[arg-type]
    )
    trace = client.get_trace("th-1")
    step_names = {s.agent_name: s for s in trace.steps}
    assert step_names["FI - Agente validador de Intents"].child_flow_id == "inner-flow-uuid-123"
    assert step_names["cargar_iniciativa_v2"].child_flow_id is None
    assert step_names["__flow_end__"].child_flow_id is None
