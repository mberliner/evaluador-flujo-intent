"""Helpers de carga por archivo del dashboard (SPEC-004 FR-007, MUST).

FR-007: cuando el archivo no incluye `clasificacion_esperada`, el dashboard la
solicita y la inyecta antes de construir el `TestCase`. Estos tests ejercitan las
funciones reales `_file_needs_clasificacion` (deteccion) e `_inject_clasificacion`
(inyeccion) — no copias — para que una regresion en cualquiera rompa la suite.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.build.case_loader import load
from src.dashboard.app import _file_needs_clasificacion, _inject_clasificacion
from src.domain.test_case import TestCase

_FIXTURES = Path(__file__).parent.parent / "fixtures"


def _bytes(data: object) -> bytes:
    return json.dumps(data).encode()


# ---------------------------------------------------------------------------
# _file_needs_clasificacion: deteccion de ausencia
# ---------------------------------------------------------------------------


def test_con_clasificacion_no_la_necesita() -> None:
    assert _file_needs_clasificacion(_bytes({"clasificacion_esperada": "Verde"})) is False


def test_sin_clave_la_necesita() -> None:
    assert _file_needs_clasificacion(_bytes({"nombre_iniciativa": "x"})) is True


def test_clasificacion_vacia_la_necesita() -> None:
    assert _file_needs_clasificacion(_bytes({"clasificacion_esperada": ""})) is True


def test_json_malformado_no_la_necesita() -> None:
    """JSON ilegible: el dashboard no pide clasificacion; el loader surfacea el error de formato."""
    assert _file_needs_clasificacion(b"{esto no es json") is False


def test_raiz_no_objeto_no_la_necesita() -> None:
    """Lista o escalar en la raiz: no se pide clasificacion (lo maneja el loader)."""
    assert _file_needs_clasificacion(_bytes([{"clasificacion_esperada": ""}])) is False
    assert _file_needs_clasificacion(_bytes(42)) is False


def test_fixture_formato_agente_necesita_clasificacion() -> None:
    """Los archivos en formato puro del agente no traen ground truth → se pide."""
    raw = (_FIXTURES / "casoTC-V-01.json").read_bytes()
    assert _file_needs_clasificacion(raw) is True


# ---------------------------------------------------------------------------
# _inject_clasificacion: inyeccion antes de construir el TestCase
# ---------------------------------------------------------------------------


def test_inyecta_en_objeto() -> None:
    injected = _inject_clasificacion(_bytes({"nombre_iniciativa": "x"}), "Rojo")
    assert json.loads(injected)["clasificacion_esperada"] == "Rojo"


def test_inyeccion_satisface_la_deteccion() -> None:
    """Round-trip FR-007: tras inyectar, el archivo ya no necesita clasificacion."""
    raw = _bytes({"nombre_iniciativa": "x"})
    assert _file_needs_clasificacion(raw) is True
    injected = _inject_clasificacion(raw, "Amarillo")
    assert _file_needs_clasificacion(injected) is False


def test_inyeccion_no_toca_raiz_no_objeto() -> None:
    """Si la raiz no es objeto, se devuelve sin inyectar (lo rechaza el loader)."""
    injected = _inject_clasificacion(_bytes([1, 2]), "Verde")
    assert json.loads(injected) == [1, 2]


def test_flujo_completo_fixture_construye_testcase() -> None:
    """FR-007 end to end: detectar ausencia → inyectar → construir TestCase con la clasificacion."""
    raw = (_FIXTURES / "casoTC-V-01.json").read_bytes()
    assert _file_needs_clasificacion(raw) is True
    case = load(_inject_clasificacion(raw, "Verde"))
    assert isinstance(case, TestCase)
    assert case.clasificacion_esperada == "Verde"
