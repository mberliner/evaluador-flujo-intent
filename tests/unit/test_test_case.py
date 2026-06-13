"""Tests unitarios de domain.TestCase (SPEC-001-single-case-input)."""

from __future__ import annotations

import pytest

from src.domain.test_case import PALETA_CLASIFICACION, TestCase


def _valid_kwargs(**overrides: object) -> dict[str, object]:
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
    return base


def test_construye_caso_valido() -> None:
    case = TestCase(**_valid_kwargs())  # type: ignore[arg-type]
    assert case.id == "TC-V-01"
    assert case.clasificacion_esperada == "Verde"
    assert case.datos_otros_mensaje == "N/A"
    assert case.expected() == {"clasificacion": "Verde", "marcadores": []}


def test_strip_normaliza_strings() -> None:
    case = TestCase(**_valid_kwargs(id="  TC-V-01  "))  # type: ignore[arg-type]
    assert case.id == "TC-V-01"


def test_id_vacio_falla() -> None:
    with pytest.raises(ValueError, match="id"):
        TestCase(**_valid_kwargs(id="   "))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field_name",
    [
        "nombre_iniciativa",
        "declaracion_intent",
        "area_proponente",
        "flujo_de_valor",
        "metricas_de_exito",
        "impacto_personas",
        "supuesto_riesgo",
        "restricciones",
        "sponsor",
        "mail_contacto",
    ],
)
def test_string_requerido_vacio_falla(field_name: str) -> None:
    with pytest.raises(ValueError, match=field_name):
        TestCase(**_valid_kwargs(**{field_name: ""}))  # type: ignore[arg-type]


def test_sin_intent_falla() -> None:
    with pytest.raises(ValueError, match="intent"):
        TestCase(
            **_valid_kwargs(  # type: ignore[arg-type]
                intent_negocio=False,
                intent_operativo=False,
                intent_capacidad_equipos=False,
                intent_tecnico_arquitectural=False,
            )
        )


def test_sin_datos_falla() -> None:
    with pytest.raises(ValueError, match="datos"):
        TestCase(
            **_valid_kwargs(  # type: ignore[arg-type]
                datos_ninguno=False,
                datos_publicos=False,
                datos_operativos=False,
                datos_personales=False,
                datos_confidenciales=False,
                datos_otros=False,
            )
        )


@pytest.mark.parametrize("invalida", ["verde", "GREEN", "Verde ", "Gris", ""])
def test_clasificacion_invalida_falla(invalida: str) -> None:
    with pytest.raises(ValueError, match="clasificacion_esperada"):
        TestCase(**_valid_kwargs(clasificacion_esperada=invalida))  # type: ignore[arg-type]


@pytest.mark.parametrize("valida", list(PALETA_CLASIFICACION))
def test_paleta_completa_admitida(valida: str) -> None:
    case = TestCase(**_valid_kwargs(clasificacion_esperada=valida))  # type: ignore[arg-type]
    assert case.clasificacion_esperada == valida


def test_marcadores_se_convierten_a_tupla() -> None:
    case = TestCase(
        **_valid_kwargs(marcadores=["riesgo-alto", "datos-personales"])  # type: ignore[arg-type]
    )
    assert case.marcadores == ("riesgo-alto", "datos-personales")
    assert isinstance(case.marcadores, tuple)


def test_caso_es_inmutable() -> None:
    from dataclasses import FrozenInstanceError

    case = TestCase(**_valid_kwargs())  # type: ignore[arg-type]
    with pytest.raises(FrozenInstanceError):
        case.id = "otro"  # type: ignore[misc]


def test_datos_otros_false_fuerza_mensaje_na() -> None:
    case = TestCase(**_valid_kwargs(datos_otros=False, datos_otros_mensaje="ignorado"))  # type: ignore[arg-type]
    assert case.datos_otros_mensaje == "N/A"


def test_datos_otros_true_con_mensaje_valido() -> None:
    case = TestCase(  # type: ignore[arg-type]
        **_valid_kwargs(
            datos_ninguno=False,
            datos_otros=True,
            datos_otros_mensaje="historial clinico",
        )
    )
    assert case.datos_otros_mensaje == "historial clinico"


def test_datos_otros_true_con_mensaje_vacio_falla() -> None:
    with pytest.raises(ValueError, match="datos_otros_mensaje"):
        TestCase(  # type: ignore[arg-type]
            **_valid_kwargs(
                datos_ninguno=False,
                datos_otros=True,
                datos_otros_mensaje="   ",
            )
        )
