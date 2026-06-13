"""Tests unitarios de build.message_builder (SPEC-002b)."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from src.build import message_builder
from src.domain.test_case import TestCase

_SCHEMA_PATH = Path(__file__).parents[2] / "schemas" / "FI_Orquestador_Input.schema.json"
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def _valid_case(**overrides: object) -> TestCase:
    base: dict[str, object] = {
        "id": "TC-V-01",
        "nombre_iniciativa": "Asistente de redaccion",
        "intent_negocio": False,
        "intent_operativo": False,
        "intent_capacidad_equipos": True,
        "intent_tecnico_arquitectural": False,
        "declaracion_intent": "Apoya la redaccion de comunicados internos.",
        "area_proponente": "Comunicaciones",
        "flujo_de_valor": "Reduce tiempo de elaboracion",
        "metricas_de_exito": "Horas ahorradas por semana",
        "impacto_personas": "Equipo de comunicaciones",
        "datos_ninguno": True,
        "datos_publicos": False,
        "datos_operativos": False,
        "datos_personales": False,
        "datos_confidenciales": False,
        "datos_otros": False,
        "datos_otros_mensaje": "N/A",
        "supuesto_riesgo": "Baja exposicion",
        "restricciones": "Ninguna",
        "sponsor": "Direccion de comunicaciones",
        "mail_contacto": "sponsor@example.com",
        "clasificacion_esperada": "Verde",
        "marcadores": (),
    }
    base.update(overrides)
    return TestCase(**base)  # type: ignore[arg-type]


def test_payload_envuelto_en_form() -> None:
    payload = message_builder.build(_valid_case())
    assert "form" in payload
    assert isinstance(payload["form"], dict)


def test_campos_excluidos_del_payload() -> None:
    payload = message_builder.build(_valid_case())
    form = payload["form"]
    assert "id" not in form
    assert "clasificacion_esperada" not in form
    assert "marcadores" not in form


def test_mapping_tipo_intent() -> None:
    case = _valid_case(intent_negocio=True, intent_capacidad_equipos=False)
    form = message_builder.build(case)["form"]
    assert form["tipo_intent"]["negocio"] is True
    assert form["tipo_intent"]["capacidad_equipos"] is False


def test_datos_otros_false_produce_estructura_correcta() -> None:
    form = message_builder.build(_valid_case(datos_otros=False))["form"]
    otros = form["datos_requeridos"]["otros"]
    assert otros == {"estado": False, "message": "N/A"}


def test_datos_otros_true_produce_estructura_correcta() -> None:
    case = _valid_case(
        datos_ninguno=False,
        datos_otros=True,
        datos_otros_mensaje="logs de auditoria",
    )
    form = message_builder.build(case)["form"]
    otros = form["datos_requeridos"]["otros"]
    assert otros == {"estado": True, "message": "logs de auditoria"}


def test_campos_datos_requeridos_usan_keys_del_schema() -> None:
    form = message_builder.build(_valid_case())["form"]
    dr = form["datos_requeridos"]
    assert "datos_publicos" in dr
    assert "datos_operativos" in dr
    assert "datos_personales" in dr
    assert "datos_confidenciales" in dr
    assert "ninguno" in dr


def test_payload_valida_contra_schema_oficial() -> None:
    payload = message_builder.build(_valid_case())
    jsonschema.validate(instance=payload, schema=_SCHEMA)


def test_payload_con_datos_otros_valida_contra_schema() -> None:
    case = _valid_case(
        datos_ninguno=False,
        datos_otros=True,
        datos_otros_mensaje="logs de auditoria",
    )
    jsonschema.validate(instance=message_builder.build(case), schema=_SCHEMA)
