"""Tests unitarios de build.case_loader (SPEC-004)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.build.case_loader import CaseLoadError, load, with_expected_classification
from src.domain.test_case import TestCase

_FIXTURES = Path(__file__).parent.parent / "fixtures"

# El flujo cuando el archivo no trae clasificacion_esperada (FR-007) se ejercita
# con la funcion real del loader, no con una copia: una regresion en la inyeccion
# rompe estos tests. La deteccion (needs_expected_classification) se cubre en
# test_expected_classification.py.


# ---------------------------------------------------------------------------
# fixture base
# ---------------------------------------------------------------------------

_VALID: dict[str, object] = {
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
    "marcadores": [],
}


def _json(data: dict[str, object] | None = None) -> str:
    return json.dumps(data if data is not None else _VALID)


# ---------------------------------------------------------------------------
# caso valido
# ---------------------------------------------------------------------------


def test_caso_valido_devuelve_testcase() -> None:
    case = load(_json())
    assert isinstance(case, TestCase)
    assert case.nombre_iniciativa == "Asistente de redaccion"
    assert case.clasificacion_esperada == "Verde"


def test_caso_valido_bytes() -> None:
    case = load(_json().encode())
    assert isinstance(case, TestCase)


def test_mismo_testcase_que_construccion_directa() -> None:
    """SC-002: cargar por archivo produce el mismo TestCase que construirlo directamente.

    Igualdad completa: TestCase es frozen dataclass, asi que `==` compara todos
    los campos. _VALID trae id no vacio, asi que no interviene la auto-generacion.
    """
    from src.domain.test_case import TestCase as TC

    case_file = load(_json())
    case_direct = TC(**{k: v for k, v in _VALID.items() if k != "marcadores"}, marcadores=())  # type: ignore[arg-type]
    assert case_file == case_direct


# ---------------------------------------------------------------------------
# id opcional
# ---------------------------------------------------------------------------


def test_id_presente_se_respeta() -> None:
    case = load(_json())
    assert case.id == "TC-V-01"


def test_id_ausente_se_autogenera() -> None:
    data = {k: v for k, v in _VALID.items() if k != "id"}
    case = load(_json(data))
    assert case.id.startswith("TC-")
    assert len(case.id) > 3


def test_id_vacio_se_autogenera() -> None:
    data = {**_VALID, "id": ""}
    case = load(_json(data))
    assert case.id.startswith("TC-")


# ---------------------------------------------------------------------------
# campos extra e ignorados
# ---------------------------------------------------------------------------


def test_formato_plano_se_carga() -> None:
    """Campos de TestCase directamente en el nivel raiz."""
    case = load(_json())
    assert case.nombre_iniciativa == "Asistente de redaccion"


def test_formato_payload_agente_anidado() -> None:
    """Formato real: id+clasificacion en raiz, campos en form con tipo_intent y datos_requeridos."""
    payload = {
        "id": "TC-V-01",
        "clasificacion_esperada": "Verde",
        "marcadores": [],
        "form": {
            "nombre_iniciativa": "Asistente de redaccion",
            "tipo_intent": {
                "negocio": False,
                "operativo": False,
                "capacidad_equipos": True,
                "tecnico_arquitectural": False,
            },
            "declaracion_intent": "Apoya la redaccion de comunicados internos.",
            "area_proponente": "Comunicaciones",
            "flujo_de_valor": "Reduce tiempo de elaboracion",
            "metricas_de_exito": "Horas ahorradas por semana",
            "impacto_personas": "Equipo de comunicaciones",
            "datos_requeridos": {
                "ninguno": True,
                "datos_publicos": False,
                "datos_operativos": False,
                "datos_personales": False,
                "datos_confidenciales": False,
                "otros": {"estado": False, "message": "N/A"},
            },
            "supuesto_riesgo": "Baja exposicion",
            "restricciones": "Ninguna",
            "sponsor": "Direccion de comunicaciones",
            "mail_contacto": "sponsor@example.com",
        },
    }
    case = load(json.dumps(payload))
    assert isinstance(case, TestCase)
    assert case.id == "TC-V-01"
    assert case.nombre_iniciativa == "Asistente de redaccion"
    assert case.intent_capacidad_equipos is True
    assert case.intent_negocio is False
    assert case.datos_ninguno is True
    assert case.clasificacion_esperada == "Verde"


def test_campos_extra_se_ignoran() -> None:
    data = {**_VALID, "campo_inexistente": "valor_cualquiera", "otro": 42}
    case = load(_json(data))
    assert isinstance(case, TestCase)


# ---------------------------------------------------------------------------
# lista de casos: toma el primero
# ---------------------------------------------------------------------------


def test_lista_con_un_caso_carga_correctamente() -> None:
    case = load(json.dumps([_VALID]))
    assert isinstance(case, TestCase)
    assert case.nombre_iniciativa == "Asistente de redaccion"


def test_lista_con_varios_casos_toma_el_primero() -> None:
    segundo = {**_VALID, "nombre_iniciativa": "Segundo caso"}
    case = load(json.dumps([_VALID, segundo]))
    assert case.nombre_iniciativa == "Asistente de redaccion"


def test_lista_vacia_levanta_case_load_error() -> None:
    with pytest.raises(CaseLoadError, match="vacio"):
        load(json.dumps([]))


# ---------------------------------------------------------------------------
# errores de formato
# ---------------------------------------------------------------------------


def test_json_mal_formado_levanta_case_load_error() -> None:
    with pytest.raises(CaseLoadError, match="JSON valido"):
        load("{esto no es json")


def test_json_con_tipo_incorrecto_levanta_case_load_error() -> None:
    with pytest.raises(CaseLoadError, match="objeto JSON"):
        load(json.dumps("solo un string"))


def test_numero_levanta_case_load_error() -> None:
    with pytest.raises(CaseLoadError, match="objeto JSON"):
        load(json.dumps(42))


# ---------------------------------------------------------------------------
# errores de validacion de TestCase (mismos que el formulario)
# ---------------------------------------------------------------------------


def test_campo_requerido_vacio_levanta_value_error() -> None:
    data = {**_VALID, "nombre_iniciativa": ""}
    with pytest.raises(ValueError, match="nombre_iniciativa"):
        load(_json(data))


def test_sin_intent_levanta_value_error() -> None:
    data = {
        **_VALID,
        "intent_negocio": False,
        "intent_operativo": False,
        "intent_capacidad_equipos": False,
        "intent_tecnico_arquitectural": False,
    }
    with pytest.raises(ValueError, match="intent"):
        load(_json(data))


def test_sin_datos_levanta_value_error() -> None:
    """SC-002: la regla 'al menos un datos_* en True' aplica igual por archivo."""
    data = {
        **_VALID,
        "datos_ninguno": False,
        "datos_publicos": False,
        "datos_operativos": False,
        "datos_personales": False,
        "datos_confidenciales": False,
        "datos_otros": False,
    }
    with pytest.raises(ValueError, match="categoria de datos"):
        load(_json(data))


def test_clasificacion_invalida_levanta_value_error() -> None:
    data = {**_VALID, "clasificacion_esperada": "Morado"}
    with pytest.raises(ValueError, match="clasificacion_esperada"):
        load(_json(data))


def test_datos_otros_true_sin_mensaje_levanta_value_error() -> None:
    data = {
        **_VALID,
        "datos_ninguno": False,
        "datos_otros": True,
        "datos_otros_mensaje": "",
    }
    with pytest.raises(ValueError, match="datos_otros_mensaje"):
        load(_json(data))


# ---------------------------------------------------------------------------
# archivos reales de fixtures (casoTC-V-01*.json)
# ---------------------------------------------------------------------------


def test_fixture_tc_v01_con_id_carga_correctamente() -> None:
    """casoTC-V-01.json: payload del agente con id en raiz, sin clasificacion_esperada."""
    raw = (_FIXTURES / "casoTC-V-01.json").read_bytes()
    case = load(with_expected_classification(raw, "Verde"))
    assert isinstance(case, TestCase)
    assert case.id == "TC-V-01"
    assert case.nombre_iniciativa == "Asistente de Redacción de Comunicados"
    assert case.intent_capacidad_equipos is True
    assert case.intent_negocio is False
    assert case.datos_ninguno is True
    assert case.clasificacion_esperada == "Verde"
    assert case.mail_contacto == "mrios@trix.com"


def test_fixture_tc_v01_f1_sin_id_autogenera() -> None:
    """casoTC-V-01-f1.json: payload sin id ni clasificacion_esperada — id se autogenera."""
    raw = (_FIXTURES / "casoTC-V-01-f1.json").read_bytes()
    case = load(with_expected_classification(raw, "Verde"))
    assert isinstance(case, TestCase)
    assert case.id.startswith("TC-")
    assert case.nombre_iniciativa == "Asistente de Redacción de Comunicados"
    assert case.intent_capacidad_equipos is True
    assert case.datos_ninguno is True
    assert case.clasificacion_esperada == "Verde"


def test_fixture_tc_v01f2_json_malformado_levanta_case_load_error() -> None:
    """casoTC-V-01f2.json: JSON invalido debe levantar CaseLoadError."""
    raw = (_FIXTURES / "casoTC-V-01f2.json").read_bytes()
    with pytest.raises(CaseLoadError, match="JSON valido"):
        load(raw)
