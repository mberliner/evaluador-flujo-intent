"""Tests del ClassificationEvaluator (SPEC-003)."""

from __future__ import annotations

import pytest

from src.domain.classification_evaluator import ClassificationEvaluator, extract_classification
from src.domain.ports import AgentResponse
from src.domain.test_case import PALETA_CLASIFICACION, TestCase


def _case(clasificacion: str = "Verde", case_id: str = "TC-V-01") -> TestCase:
    return TestCase(
        id=case_id,
        nombre_iniciativa="Iniciativa X",
        intent_negocio=True,
        intent_operativo=False,
        intent_capacidad_equipos=False,
        intent_tecnico_arquitectural=False,
        declaracion_intent="x",
        area_proponente="x",
        flujo_de_valor="x",
        metricas_de_exito="x",
        impacto_personas="x",
        datos_ninguno=True,
        datos_publicos=False,
        datos_operativos=False,
        datos_personales=False,
        datos_confidenciales=False,
        datos_otros=False,
        datos_otros_mensaje="N/A",
        supuesto_riesgo="x",
        restricciones="x",
        sponsor="x",
        mail_contacto="x@x",
        clasificacion_esperada=clasificacion,
    )


@pytest.fixture
def evaluator() -> ClassificationEvaluator:
    return ClassificationEvaluator()


@pytest.mark.parametrize("color", list(PALETA_CLASIFICACION))
def test_extract_paleta_completa(evaluator: ClassificationEvaluator, color: str) -> None:
    assert evaluator.extract(f"La clasificacion es {color}.") == color


@pytest.mark.parametrize(
    "lowered",
    ["verde", "VERDE", "VeRdE", "amarillo", "rojo", "negro"],
)
def test_extract_es_case_insensitive_y_canoniza(
    evaluator: ClassificationEvaluator, lowered: str
) -> None:
    result = evaluator.extract(f"resultado: {lowered}")
    assert result in PALETA_CLASIFICACION
    assert result is not None
    assert result.lower() == lowered.lower()


def test_extract_devuelve_primer_match(evaluator: ClassificationEvaluator) -> None:
    text = "Despues de analizar, el resultado es Amarillo, no Rojo."
    assert evaluator.extract(text) == "Amarillo"


def test_extract_respeta_bordes_de_palabra(evaluator: ClassificationEvaluator) -> None:
    # "Rojizo" contiene "Rojo" pero no debe matchear (\b cubre solo palabras enteras).
    assert evaluator.extract("El color es rojizo y no concluyente.") is None
    # "Verdadero" contiene "Verda" no "Verde", asi que tampoco.
    assert evaluator.extract("Es verdaderamente complejo.") is None


def test_extract_sin_match_devuelve_none(evaluator: ClassificationEvaluator) -> None:
    assert evaluator.extract("") is None
    assert evaluator.extract("Sin clasificacion evidente.") is None
    assert (
        evaluator.extract(
            "A new flow has started. This chat session is currently dedicated to the flow."
        )
        is None
    )


def test_evaluate_pass(evaluator: ClassificationEvaluator) -> None:
    case = _case("Verde")
    response = AgentResponse(content="Resultado: Verde", conversation_id="th-1")
    result = evaluator.evaluate(case, response)
    assert result.passed is True
    assert result.verdict == "pass"
    assert result.extracted_classification == "Verde"
    assert result.expected == "Verde"
    assert result.conversation_id == "th-1"
    assert result.notes == ""


def test_evaluate_fail(evaluator: ClassificationEvaluator) -> None:
    case = _case("Verde")
    response = AgentResponse(content="Resultado: Amarillo")
    result = evaluator.evaluate(case, response)
    assert result.passed is False
    assert result.verdict == "fail"
    assert result.extracted_classification == "Amarillo"
    assert "no coincide" in result.notes


def test_evaluate_indeterminado(evaluator: ClassificationEvaluator) -> None:
    case = _case("Verde")
    response = AgentResponse(content="A new flow has started.")
    result = evaluator.evaluate(case, response)
    assert result.passed is None
    assert result.verdict == "indeterminado"
    assert result.extracted_classification is None
    assert "sin clasificacion" in result.notes


def test_to_dict_es_serializable(evaluator: ClassificationEvaluator) -> None:
    case = _case("Rojo", case_id="TC-R-09")
    response = AgentResponse(content="Esto es Rojo.", conversation_id="th-9")
    result = evaluator.evaluate(case, response)
    data = result.to_dict()
    assert data["case_id"] == "TC-R-09"
    assert data["expected"] == "Rojo"
    assert data["passed"] is True
    assert data["conversation_id"] == "th-9"


# ---------------------------------------------------------------------------
# extract_classification (funcion de dominio sobre mensajes del thread)
# ---------------------------------------------------------------------------


def _msg(role: str, content: str) -> dict:
    return {"role": role, "content": content}


_PALETA_RIESGO = [c for c in PALETA_CLASIFICACION if c != "Rechazado"]


@pytest.mark.parametrize("color", _PALETA_RIESGO)
def test_extract_classification_paleta_completa(color: str) -> None:
    msgs = [_msg("assistant", f"riesgo: {color.upper()}\n\nFastGate Preguntas:\n1. algo")]
    assert extract_classification(msgs) == color


def test_extract_classification_ignora_mensaje_flow_started() -> None:
    msgs = [
        _msg("assistant", "A new flow has started. This chat session..."),
        _msg("assistant", "riesgo: VERDE\n\nFastGate Preguntas:"),
    ]
    assert extract_classification(msgs) == "Verde"


def test_extract_classification_ignora_mensajes_user() -> None:
    msgs = [_msg("user", "riesgo: VERDE"), _msg("assistant", "sin riesgo aqui")]
    assert extract_classification(msgs) is None


def test_extract_classification_devuelve_none_si_no_hay_patron() -> None:
    msgs = [_msg("assistant", "El flujo se ejecuto correctamente.")]
    assert extract_classification(msgs) is None


def test_extract_classification_lista_vacia_devuelve_none() -> None:
    assert extract_classification([]) is None


def test_extract_classification_case_insensitive_en_prefijo() -> None:
    msgs = [_msg("assistant", "Riesgo: AMARILLO\n\ndetalles")]
    assert extract_classification(msgs) == "Amarillo"


# ---------------------------------------------------------------------------
# SPEC-003b — deteccion y evaluacion de RECHAZADO
# ---------------------------------------------------------------------------


def test_extract_detecta_rechazado(evaluator: ClassificationEvaluator) -> None:
    assert evaluator.extract("El caso fue RECHAZADO por falta de campo") == "Rechazado"


def test_extract_rechazado_case_insensitive(evaluator: ClassificationEvaluator) -> None:
    assert evaluator.extract("rechazado: input incompleto") == "Rechazado"


def test_extract_rechazado_no_matchea_substring(evaluator: ClassificationEvaluator) -> None:
    assert evaluator.extract("no fue rechazada la solicitud") is None


def test_evaluate_rechazado_esperado_y_recibido_es_pass(
    evaluator: ClassificationEvaluator,
) -> None:
    case = _case("Rechazado")
    result = evaluator.evaluate(case, AgentResponse(content="RECHAZADO por inconsistencia"))
    assert result.passed is True
    assert result.extracted_classification == "Rechazado"


def test_evaluate_rechazado_recibido_pero_no_esperado_es_fail(
    evaluator: ClassificationEvaluator,
) -> None:
    case = _case("Verde")
    result = evaluator.evaluate(case, AgentResponse(content="RECHAZADO por falta de datos"))
    assert result.passed is False
    assert result.extracted_classification == "Rechazado"


def test_evaluate_esperaba_rechazado_pero_recibio_clasificacion_es_fail(
    evaluator: ClassificationEvaluator,
) -> None:
    case = _case("Rechazado")
    result = evaluator.evaluate(case, AgentResponse(content="riesgo: VERDE"))
    assert result.passed is False
    assert result.extracted_classification == "Verde"
