"""Tests de SyncHttpAgentClient (SPEC-013) con stub de requests.Session."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import requests

from src.adapters.platform_config import PlatformConfig
from src.adapters.sync_agent_client import SyncHttpAgentClient
from src.build import message_builder
from src.domain.test_case import TestCase

_SCHEMA_PATH = Path(__file__).parents[2] / "schemas" / "FI_Orquestador_Input.schema.json"
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


class _StubResponse:
    def __init__(self, status_code: int, payload: Any = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload
        self.text = text or str(payload)

    def json(self) -> Any:
        if self._payload is None:
            raise ValueError("sin body")
        return self._payload


class _StubSession:
    def __init__(self, responses: list[_StubResponse]):
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def post(self, url: str, **kwargs: Any) -> _StubResponse:
        self.calls.append({"method": "post", "url": url, **kwargs})
        return self._responses.pop(0)


class _TimeoutSession:
    def post(self, url: str, **kwargs: Any) -> _StubResponse:
        raise requests.Timeout("se agotó el tiempo")


class _StubCredentials:
    def get(self) -> str:
        return "llave-stub"


def _config() -> PlatformConfig:
    return PlatformConfig(
        chat_url="",
        token_url="",
        agents_url="",
        flows_url="",
        threads_url="",
        api_key="",
        agent_id="sync_http",
        client_type="sync_http",
        alt_client_url="https://alt.example/intents",
        alt_client_api_key="llave-alt",
    )


def _client(session: Any) -> SyncHttpAgentClient:
    return SyncHttpAgentClient(_config(), _StubCredentials(), session=session)


def _valid_case() -> TestCase:
    return TestCase(
        id="TC-V-01",
        nombre_iniciativa="Asistente de redaccion",
        intent_negocio=False,
        intent_operativo=False,
        intent_capacidad_equipos=True,
        intent_tecnico_arquitectural=False,
        declaracion_intent="Apoya la redaccion de comunicados internos.",
        area_proponente="Comunicaciones",
        flujo_de_valor="Reduce tiempo de elaboracion",
        metricas_de_exito="Horas ahorradas por semana",
        impacto_personas="Equipo de comunicaciones",
        datos_ninguno=True,
        datos_publicos=False,
        datos_operativos=False,
        datos_personales=False,
        datos_confidenciales=False,
        datos_otros=False,
        datos_otros_mensaje="N/A",
        supuesto_riesgo="Baja exposicion",
        restricciones="Ninguna",
        sponsor="Direccion de comunicaciones",
        mail_contacto="sponsor@example.com",
        clasificacion_esperada="Verde",
    )


# Respuesta 200 del pipeline con el bloque de clasificación final presente.
def _ok_body(color: str = "Verde") -> dict[str, Any]:
    return {
        "output_integridad": {"resultado": True},
        "output_impacto": {"resultado": True},
        "output_factibilidad": {"resultado": True},
        "output_fastgate": {"clasificacion": color, "preguntas": []},
        "output_redactor_mail": {"enviado": True},
    }


# Corto-circuito: un gate previo dio false y el bloque final viene null.
_SHORT_CIRCUIT_BODY: dict[str, Any] = {
    "output_integridad": {"resultado": False},
    "output_impacto": None,
    "output_factibilidad": None,
    "output_fastgate": None,
    "output_redactor_mail": {"enviado": True},
}

_FORM = message_builder.build(_valid_case())


# ---------------------------------------------------------------------------
# FR-010 — body plano en la raíz, sin envoltorio 'form' ni 'id'
# ---------------------------------------------------------------------------


def test_envia_form_plano_en_la_raiz_del_body() -> None:
    session = _StubSession([_StubResponse(200, _ok_body())])
    _client(session).send(_FORM)
    body = session.calls[0]["json"]
    assert "form" not in body
    assert "id" not in body
    assert body == _FORM["form"]


def test_body_cumple_el_schema_de_entrada() -> None:
    """Identidad de campos contra schemas/FI_Orquestador_Input.schema.json."""
    session = _StubSession([_StubResponse(200, _ok_body())])
    _client(session).send(_FORM)
    jsonschema.validate(session.calls[0]["json"], _SCHEMA)


def test_descarta_id_si_viene_en_el_form() -> None:
    session = _StubSession([_StubResponse(200, _ok_body())])
    form_con_id = {"form": {**_FORM["form"], "id": "TC-V-01"}}
    _client(session).send(form_con_id)
    assert "id" not in session.calls[0]["json"]


def test_postea_al_endpoint_configurado_con_llave_por_header() -> None:
    session = _StubSession([_StubResponse(200, _ok_body())])
    _client(session).send(_FORM)
    call = session.calls[0]
    assert call["url"] == "https://alt.example/intents"
    assert call["headers"]["x-api-key"] == "llave-stub"


def test_payload_sin_clave_form_es_fallo_tecnico() -> None:
    session = _StubSession([_StubResponse(200, _ok_body())])
    resp = _client(session).send({"otra": "cosa"})
    assert resp.conversation_id is None
    assert session.calls == []  # no llegó a la red


# ---------------------------------------------------------------------------
# FR-011 — colapso de la respuesta multi-etapa a la paleta
# ---------------------------------------------------------------------------


def test_bloque_final_presente_hace_pass_through_del_color() -> None:
    session = _StubSession([_StubResponse(200, _ok_body("Amarillo"))])
    resp = _client(session).send(_FORM)
    assert resp.content == "Amarillo"
    assert resp.conversation_id is not None


def test_pass_through_generico_sin_enumerar_paleta() -> None:
    """Un color nuevo de la plataforma pasa tal cual: la canonización es del evaluador."""
    session = _StubSession([_StubResponse(200, _ok_body("Violeta"))])
    assert _client(session).send(_FORM).content == "Violeta"


def test_corto_circuito_de_gate_emite_rechazado() -> None:
    session = _StubSession([_StubResponse(200, _SHORT_CIRCUIT_BODY)])
    resp = _client(session).send(_FORM)
    assert resp.content == "Rechazado"
    assert resp.conversation_id is not None


def test_body_sin_bloque_final_es_forma_inesperada_no_rechazado() -> None:
    session = _StubSession([_StubResponse(200, {"error": "algo raro"})])
    resp = _client(session).send(_FORM)
    assert resp.conversation_id is None
    assert resp.content != "Rechazado"


def test_bloque_final_sin_color_legible_es_forma_inesperada() -> None:
    session = _StubSession([_StubResponse(200, {"output_fastgate": {"otra": "cosa"}})])
    assert _client(session).send(_FORM).conversation_id is None


# ---------------------------------------------------------------------------
# FR-012 — contrato conversacional transparente (sync detrás del puerto)
# ---------------------------------------------------------------------------


def test_send_devuelve_conversation_id_sintetico_y_cachea() -> None:
    session = _StubSession([_StubResponse(200, _ok_body("Rojo"))])
    client = _client(session)
    resp = client.send(_FORM)
    assert resp.conversation_id
    assert client.wait_for_completion(resp.conversation_id, timeout_seconds=1) is True
    final = client.get_final_response(resp.conversation_id, "fallback")
    assert final.content == "Rojo"
    assert final.conversation_id == resp.conversation_id


def test_cada_send_genera_un_id_distinto() -> None:
    session = _StubSession(
        [_StubResponse(200, _ok_body("Verde")), _StubResponse(200, _ok_body("Negro"))]
    )
    client = _client(session)
    first = client.send(_FORM)
    second = client.send(_FORM)
    assert first.conversation_id != second.conversation_id
    assert client.get_final_response(first.conversation_id or "", "fb").content == "Verde"
    assert client.get_final_response(second.conversation_id or "", "fb").content == "Negro"


def test_get_final_response_sin_cache_usa_fallback() -> None:
    client = _client(_StubSession([]))
    assert client.get_final_response("sync-desconocido", "fallback").content == "fallback"


def test_get_thread_messages_devuelve_vacio() -> None:
    assert _client(_StubSession([])).get_thread_messages("sync-1") == []


def test_get_trace_devuelve_traza_vacia() -> None:
    trace = _client(_StubSession([])).get_trace("sync-1")
    assert trace.thread_id == "sync-1"
    assert trace.steps == ()


# ---------------------------------------------------------------------------
# FR-013 — fallos técnicos → conversation_id=None, nunca Rechazado
# ---------------------------------------------------------------------------


def test_422_es_fallo_tecnico_no_rechazado() -> None:
    session = _StubSession([_StubResponse(422, {"detail": "payload inválido"})])
    resp = _client(session).send(_FORM)
    assert resp.conversation_id is None
    assert "Rechazado" not in resp.content
    assert "422" in resp.content


def test_5xx_es_fallo_tecnico() -> None:
    session = _StubSession([_StubResponse(500, text="boom")])
    resp = _client(session).send(_FORM)
    assert resp.conversation_id is None
    assert "Rechazado" not in resp.content


def test_timeout_de_red_es_fallo_tecnico() -> None:
    resp = _client(_TimeoutSession()).send(_FORM)
    assert resp.conversation_id is None
    assert "Rechazado" not in resp.content


def test_body_no_parseable_es_fallo_tecnico() -> None:
    session = _StubSession([_StubResponse(200, payload=None, text="<html>")])
    resp = _client(session).send(_FORM)
    assert resp.conversation_id is None


def test_body_que_no_es_objeto_es_fallo_tecnico() -> None:
    session = _StubSession([_StubResponse(200, ["lista", "inesperada"])])
    assert _client(session).send(_FORM).conversation_id is None
