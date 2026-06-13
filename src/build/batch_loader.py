"""Carga múltiples casos desde un archivo tabular plano (SPEC-006 US1).

Una fila por caso, encabezado con los nombres planos de TestCase. El
separador se autodetecta (';' o ','). Las filas inválidas se reportan
aparte y no abortan la carga; las columnas desconocidas se ignoran.

El formato de archivo queda confinado aquí; los identificadores no lo
nombran (ver specs/SPEC-000-naming.md).
"""

from __future__ import annotations

import csv
import io
import uuid
from dataclasses import dataclass, field

from src.domain.test_case import TestCase

_TRUE_TOKENS: frozenset[str] = frozenset({"true", "1", "si", "sí", "yes", "x", "verdadero", "v"})
_MARKER_SEPARATOR = "|"


@dataclass(frozen=True, slots=True)
class RowError:
    """Una fila que no pudo construir un TestCase válido."""

    line: int
    message: str


@dataclass(frozen=True, slots=True)
class BatchLoadResult:
    """Resultado de cargar un archivo batch: casos válidos + filas inválidas."""

    cases: tuple[TestCase, ...] = field(default_factory=tuple)
    errors: tuple[RowError, ...] = field(default_factory=tuple)


class BatchLoadError(Exception):
    """El archivo completo no se pudo interpretar (no es texto tabular usable)."""


def _detect_delimiter(header_line: str) -> str:
    return ";" if header_line.count(";") > header_line.count(",") else ","


def _to_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in _TRUE_TOKENS


def _parse_markers(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(m.strip() for m in value.split(_MARKER_SEPARATOR) if m.strip())


def _resolve_id(value: str | None) -> str:
    resolved = (value or "").strip()
    return resolved or f"TC-{uuid.uuid4().hex[:8].upper()}"


def _row_to_case(row: dict[str, str]) -> TestCase:
    clean = {(k or "").strip().lower(): (v if v is not None else "") for k, v in row.items()}
    return TestCase(
        id=_resolve_id(clean.get("id")),
        nombre_iniciativa=clean.get("nombre_iniciativa", ""),
        intent_negocio=_to_bool(clean.get("intent_negocio")),
        intent_operativo=_to_bool(clean.get("intent_operativo")),
        intent_capacidad_equipos=_to_bool(clean.get("intent_capacidad_equipos")),
        intent_tecnico_arquitectural=_to_bool(clean.get("intent_tecnico_arquitectural")),
        declaracion_intent=clean.get("declaracion_intent", ""),
        area_proponente=clean.get("area_proponente", ""),
        flujo_de_valor=clean.get("flujo_de_valor", ""),
        metricas_de_exito=clean.get("metricas_de_exito", ""),
        impacto_personas=clean.get("impacto_personas", ""),
        datos_ninguno=_to_bool(clean.get("datos_ninguno")),
        datos_publicos=_to_bool(clean.get("datos_publicos")),
        datos_operativos=_to_bool(clean.get("datos_operativos")),
        datos_personales=_to_bool(clean.get("datos_personales")),
        datos_confidenciales=_to_bool(clean.get("datos_confidenciales")),
        datos_otros=_to_bool(clean.get("datos_otros")),
        datos_otros_mensaje=clean.get("datos_otros_mensaje", "N/A") or "N/A",
        supuesto_riesgo=clean.get("supuesto_riesgo", ""),
        restricciones=clean.get("restricciones", ""),
        sponsor=clean.get("sponsor", ""),
        mail_contacto=clean.get("mail_contacto", ""),
        clasificacion_esperada=clean.get("clasificacion_esperada", ""),
        marcadores=_parse_markers(clean.get("marcadores")),
    )


def load_batch(content: str | bytes) -> BatchLoadResult:
    """Parsea un archivo tabular y construye los casos, separando las filas inválidas.

    Raises:
        BatchLoadError: el contenido no es texto tabular interpretable o está vacío.
    """
    if isinstance(content, bytes):
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise BatchLoadError(f"El archivo no es texto UTF-8 válido: {exc}") from exc
    else:
        text = content

    stripped = text.strip()
    if not stripped:
        raise BatchLoadError("El archivo está vacío.")

    first_line = stripped.splitlines()[0]
    delimiter = _detect_delimiter(first_line)
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if reader.fieldnames is None:
        raise BatchLoadError("El archivo no tiene encabezado.")

    cases: list[TestCase] = []
    errors: list[RowError] = []
    for offset, row in enumerate(reader, start=2):  # fila 1 = encabezado
        if not any((v or "").strip() for v in row.values()):
            continue  # fila completamente vacía
        try:
            cases.append(_row_to_case(row))
        except ValueError as exc:
            errors.append(RowError(line=offset, message=str(exc)))

    return BatchLoadResult(cases=tuple(cases), errors=tuple(errors))
