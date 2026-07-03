"""Integración run_one + SyncHttpAgentClient (SPEC-013 FR-012, SC-002).

Verifica que el flujo conversacional de la capa de aplicación (send →
wait_for_completion → get_final_response → evaluate) funciona sin
modificación alguna con el adaptador síncrono, usando un stub de red.
"""

from __future__ import annotations

from typing import Any

from src.adapters.platform_config import PlatformConfig
from src.adapters.sync_agent_client import SyncHttpAgentClient
from src.application.run_suite import run_one
from src.domain.classification_evaluator import ClassificationEvaluator
from src.domain.test_case import TestCase


class _StubResponse:
    def __init__(self, status_code: int, payload: Any = None):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        return self._payload


class _StubSession:
    def __init__(self, responses: list[_StubResponse]):
        self._responses = list(responses)

    def post(self, url: str, **kwargs: Any) -> _StubResponse:
        return self._responses.pop(0)


def _case(esperado: str = "Verde") -> TestCase:
    return TestCase(
        id="TC-INT-01",
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
        clasificacion_esperada=esperado,
    )


class _StubCredentials:
    def get(self) -> str:
        return "llave-stub"


def _client(responses: list[_StubResponse]) -> SyncHttpAgentClient:
    config = PlatformConfig(
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
    return SyncHttpAgentClient(
        config,
        _StubCredentials(),
        session=_StubSession(responses),  # type: ignore[arg-type]
    )


def test_run_one_evalua_pass_con_el_adaptador_sincronico() -> None:
    client = _client([_StubResponse(200, {"output_fastgate": {"clasificacion": "Verde"}})])
    result = run_one(_case("Verde"), client, ClassificationEvaluator())
    assert result.passed is True
    assert result.extracted_classification == "Verde"
    assert result.conversation_id  # id sintético no nulo satisface la guarda


def test_run_one_evalua_fail_cuando_el_color_no_coincide() -> None:
    client = _client([_StubResponse(200, {"output_fastgate": {"clasificacion": "Rojo"}})])
    result = run_one(_case("Verde"), client, ClassificationEvaluator())
    assert result.passed is False


def test_run_one_corto_circuito_evalua_contra_rechazado() -> None:
    client = _client(
        [_StubResponse(200, {"output_integridad": {"resultado": False}, "output_fastgate": None})]
    )
    result = run_one(_case("Rechazado"), client, ClassificationEvaluator())
    assert result.passed is True
    assert result.extracted_classification == "Rechazado"


def test_run_one_fallo_tecnico_produce_indeterminado_sin_abortar() -> None:
    client = _client([_StubResponse(422, {"detail": "payload inválido"})])
    result = run_one(_case("Verde"), client, ClassificationEvaluator())
    assert result.passed is None  # Indeterminado (FR-013)
    assert "Error de ejecución" in (result.notes or "")


def test_run_one_captura_traza_vacia_sin_fallar() -> None:
    client = _client([_StubResponse(200, {"output_fastgate": {"clasificacion": "Verde"}})])
    result = run_one(_case("Verde"), client, ClassificationEvaluator(), capture_trace=True)
    assert result.passed is True
    assert result.trace is not None
    assert result.trace.steps == ()
