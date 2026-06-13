"""Carga un TestCase desde contenido JSON estructurado (SPEC-004).

Acepta dos formatos:
- Plano: campos de TestCase directamente en el nivel raiz.
- Payload del agente: {"id": ..., "clasificacion_esperada": ..., "form": {campos anidados}}.

Si el contenido es una lista, se toma el primer elemento (modo simple).
Campos extra se ignoran; campos faltantes producen error de validacion
mediante las reglas de TestCase.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from src.domain.test_case import TestCase


class CaseLoadError(Exception):
    """Error de formato o estructura al cargar un caso desde archivo."""


def load(content: str | bytes) -> TestCase:
    """Parsea JSON y construye un TestCase.

    Raises:
        CaseLoadError: contenido no es JSON valido o estructura inesperada.
        ValueError: el caso no pasa la validacion de TestCase (mismo error que el formulario).
    """
    try:
        raw: Any = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CaseLoadError(f"El archivo no es JSON valido: {exc}") from exc

    if isinstance(raw, list):
        if not raw:
            raise CaseLoadError("El archivo esta vacio (lista sin casos).")
        raw = raw[0]

    if not isinstance(raw, dict):
        raise CaseLoadError("El archivo debe contener un objeto JSON con los campos del caso.")

    return _build(raw)


def _resolve_id(value: Any) -> str:
    resolved = str(value).strip() if value is not None else ""
    return resolved or f"TC-{uuid.uuid4().hex[:8].upper()}"


def _build(data: dict[str, Any]) -> TestCase:
    """Construye TestCase desde formato plano o desde formato payload del agente.

    Formato plano: campos de TestCase directamente en el dict raiz.
    Formato payload: {"id": ..., "clasificacion_esperada": ..., "form": {campos anidados}}.
    Los campos de ground truth (id, clasificacion_esperada, marcadores) siempre
    se leen del nivel raiz; los campos del agente se leen de "form" si existe.
    """
    form_raw = data.get("form", data)
    if not isinstance(form_raw, dict):
        raise CaseLoadError("El campo 'form' debe ser un objeto JSON.")
    form: dict[str, Any] = form_raw

    tipo_raw = form.get("tipo_intent", {})
    tipo: dict[str, Any] = tipo_raw if isinstance(tipo_raw, dict) else {}
    dr_raw = form.get("datos_requeridos", {})
    dr: dict[str, Any] = dr_raw if isinstance(dr_raw, dict) else {}
    otros_raw = dr.get("otros", {})
    otros: dict[str, Any] = otros_raw if isinstance(otros_raw, dict) else {}

    try:
        return TestCase(
            id=_resolve_id(data.get("id") or form.get("id")),
            nombre_iniciativa=str(form.get("nombre_iniciativa", "")),
            intent_negocio=bool(tipo.get("negocio", form.get("intent_negocio", False))),
            intent_operativo=bool(tipo.get("operativo", form.get("intent_operativo", False))),
            intent_capacidad_equipos=bool(
                tipo.get("capacidad_equipos", form.get("intent_capacidad_equipos", False))
            ),
            intent_tecnico_arquitectural=bool(
                tipo.get(
                    "tecnico_arquitectural",
                    form.get("intent_tecnico_arquitectural", False),
                )
            ),
            declaracion_intent=str(form.get("declaracion_intent", "")),
            area_proponente=str(form.get("area_proponente", "")),
            flujo_de_valor=str(form.get("flujo_de_valor", "")),
            metricas_de_exito=str(form.get("metricas_de_exito", "")),
            impacto_personas=str(form.get("impacto_personas", "")),
            datos_ninguno=bool(dr.get("ninguno", form.get("datos_ninguno", False))),
            datos_publicos=bool(dr.get("datos_publicos", form.get("datos_publicos", False))),
            datos_operativos=bool(dr.get("datos_operativos", form.get("datos_operativos", False))),
            datos_personales=bool(dr.get("datos_personales", form.get("datos_personales", False))),
            datos_confidenciales=bool(
                dr.get("datos_confidenciales", form.get("datos_confidenciales", False))
            ),
            datos_otros=bool(otros.get("estado", form.get("datos_otros", False))),
            datos_otros_mensaje=str(otros.get("message", form.get("datos_otros_mensaje", "N/A"))),
            supuesto_riesgo=str(form.get("supuesto_riesgo", "")),
            restricciones=str(form.get("restricciones", "")),
            sponsor=str(form.get("sponsor", "")),
            mail_contacto=str(form.get("mail_contacto", "")),
            clasificacion_esperada=str(data.get("clasificacion_esperada", "")),
            marcadores=tuple(data.get("marcadores", [])),
        )
    except (TypeError, AttributeError) as exc:
        raise CaseLoadError(f"Estructura de campos inesperada: {exc}") from exc
