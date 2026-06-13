"""Tests del parser CSV batch (SPEC-006 US1, FR-001/001b/001c)."""

from __future__ import annotations

import pytest

from src.build.batch_loader import BatchLoadError, load_batch

_HEADER = (
    "id;nombre_iniciativa;intent_negocio;intent_operativo;intent_capacidad_equipos;"
    "intent_tecnico_arquitectural;declaracion_intent;area_proponente;flujo_de_valor;"
    "metricas_de_exito;impacto_personas;datos_ninguno;datos_publicos;datos_operativos;"
    "datos_personales;datos_confidenciales;datos_otros;supuesto_riesgo;restricciones;"
    "sponsor;mail_contacto;clasificacion_esperada;marcadores"
)


def _row(
    *,
    case_id: str = "TC-1",
    clasif: str = "Verde",
    intent: str = "true",
    datos: str = "true",
    marcadores: str = "",
    sep: str = ";",
) -> str:
    fields = [
        case_id,
        "Iniciativa X",
        intent,  # intent_negocio
        "false",
        "false",
        "false",
        "decl",
        "area",
        "flujo",
        "metricas",
        "impacto",
        datos,  # datos_ninguno
        "false",
        "false",
        "false",
        "false",
        "false",
        "riesgo",
        "restric",
        "sponsor",
        "a@b.com",
        clasif,
        marcadores,
    ]
    return sep.join(fields)


def _file(*rows: str, sep: str = ";", header: str = _HEADER) -> str:
    if sep != ";":
        header = header.replace(";", sep)
    return "\n".join([header, *rows])


def test_loads_valid_rows() -> None:
    result = load_batch(_file(_row(case_id="TC-1"), _row(case_id="TC-2")))
    assert len(result.cases) == 2
    assert result.errors == ()
    assert result.cases[0].id == "TC-1"
    assert result.cases[0].clasificacion_esperada == "Verde"


def test_invalid_rows_reported_apart_without_aborting() -> None:
    # segunda fila: sin intent marcado -> inválida; las demás se cargan igual
    good = _row(case_id="TC-1")
    bad = _row(case_id="TC-2", intent="false")  # ningún intent -> ValueError en TestCase
    result = load_batch(_file(good, bad, _row(case_id="TC-3")))
    assert len(result.cases) == 2
    assert {c.id for c in result.cases} == {"TC-1", "TC-3"}
    assert len(result.errors) == 1
    assert result.errors[0].line == 3


def test_autodetects_comma_separator() -> None:
    result = load_batch(_file(_row(case_id="TC-1", sep=","), sep=","))
    assert len(result.cases) == 1
    assert result.cases[0].id == "TC-1"


def test_boolean_accepts_si_no_variants() -> None:
    result = load_batch(_file(_row(case_id="TC-1", intent="si", datos="SI")))
    assert len(result.cases) == 1
    assert result.cases[0].intent_negocio is True
    assert result.cases[0].datos_ninguno is True


def test_unknown_columns_are_ignored() -> None:
    header = _HEADER + ";resultado_p1;resultado_p2;"
    row = _row(case_id="TC-1") + ";si;No;"
    result = load_batch(_file(row, header=header))
    assert len(result.cases) == 1
    assert result.errors == ()


def test_markers_split_by_pipe() -> None:
    result = load_batch(_file(_row(case_id="TC-1", marcadores="[LÍMITE]|[P1]")))
    assert result.cases[0].marcadores == ("[LÍMITE]", "[P1]")


def test_empty_file_raises() -> None:
    with pytest.raises(BatchLoadError):
        load_batch("   ")


def test_blank_rows_skipped() -> None:
    result = load_batch(_file(_row(case_id="TC-1"), ";;;;;;;;;;;;;;;;;;;;;;"))
    assert len(result.cases) == 1
    assert result.errors == ()
