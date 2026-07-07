"""Deteccion e inyeccion de `clasificacion_esperada` (SPEC-004 FR-007, MUST).

FR-007: cuando el archivo no incluye `clasificacion_esperada`, el dashboard la
solicita y la inyecta antes de construir el `TestCase`. La deteccion
(`needs_expected_classification`) y la inyeccion (`with_expected_classification`)
viven en `build/case_loader` (conocimiento del formato del archivo, misma capa
que el parseo); estos tests ejercitan las funciones reales — no copias — para
que una regresion en cualquiera rompa la suite.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.build.case_loader import (
    load,
    needs_expected_classification,
    with_expected_classification,
)
from src.domain.test_case import TestCase

_FIXTURES = Path(__file__).parent.parent / "fixtures"


def _bytes(data: object) -> bytes:
    return json.dumps(data).encode()


# ---------------------------------------------------------------------------
# needs_expected_classification: deteccion de ausencia
# ---------------------------------------------------------------------------


def test_con_clasificacion_no_la_necesita() -> None:
    assert needs_expected_classification(_bytes({"clasificacion_esperada": "Verde"})) is False


def test_sin_clave_la_necesita() -> None:
    assert needs_expected_classification(_bytes({"nombre_iniciativa": "x"})) is True


def test_clasificacion_vacia_la_necesita() -> None:
    assert needs_expected_classification(_bytes({"clasificacion_esperada": ""})) is True


def test_json_malformado_no_la_necesita() -> None:
    """Contenido ilegible: no se pide clasificacion; el loader surfacea el error de formato."""
    assert needs_expected_classification(b"{esto no es json") is False


def test_raiz_no_objeto_no_la_necesita() -> None:
    """Lista o escalar en la raiz: no se pide clasificacion (lo maneja el loader)."""
    assert needs_expected_classification(_bytes([{"clasificacion_esperada": ""}])) is False
    assert needs_expected_classification(_bytes(42)) is False


def test_fixture_formato_agente_necesita_clasificacion() -> None:
    """Los archivos en formato puro del agente no traen ground truth → se pide."""
    raw = (_FIXTURES / "casoTC-V-01.json").read_bytes()
    assert needs_expected_classification(raw) is True


# ---------------------------------------------------------------------------
# with_expected_classification: inyeccion antes de construir el TestCase
# ---------------------------------------------------------------------------


def test_inyecta_en_objeto() -> None:
    injected = with_expected_classification(_bytes({"nombre_iniciativa": "x"}), "Rojo")
    assert json.loads(injected)["clasificacion_esperada"] == "Rojo"


def test_inyeccion_satisface_la_deteccion() -> None:
    """Round-trip FR-007: tras inyectar, el archivo ya no necesita clasificacion."""
    raw = _bytes({"nombre_iniciativa": "x"})
    assert needs_expected_classification(raw) is True
    injected = with_expected_classification(raw, "Amarillo")
    assert needs_expected_classification(injected) is False


def test_inyeccion_no_toca_raiz_no_objeto() -> None:
    """Si la raiz no es objeto, se devuelve sin inyectar (lo rechaza el loader)."""
    injected = with_expected_classification(_bytes([1, 2]), "Verde")
    assert json.loads(injected) == [1, 2]


def test_flujo_completo_fixture_construye_testcase() -> None:
    """FR-007 end to end: detectar ausencia → inyectar → construir TestCase con la clasificacion."""
    raw = (_FIXTURES / "casoTC-V-01.json").read_bytes()
    assert needs_expected_classification(raw) is True
    case = load(with_expected_classification(raw, "Verde"))
    assert isinstance(case, TestCase)
    assert case.clasificacion_esperada == "Verde"
