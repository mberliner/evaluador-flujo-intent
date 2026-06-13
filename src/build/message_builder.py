"""Construye el payload de envio al agente a partir de un TestCase.

El mapping TestCase -> schema esta definido en SPEC-002b-message-builder.
El schema de referencia vive en schemas/FI_Orquestador_Input.schema.json.
"""

from __future__ import annotations

from typing import Any

from src.domain.test_case import TestCase


def build(case: TestCase) -> dict[str, Any]:
    """Devuelve el payload {form: {...}} listo para enviar al agente."""
    return {
        "form": {
            "nombre_iniciativa": case.nombre_iniciativa,
            "declaracion_intent": case.declaracion_intent,
            "area_proponente": case.area_proponente,
            "flujo_de_valor": case.flujo_de_valor,
            "metricas_de_exito": case.metricas_de_exito,
            "impacto_personas": case.impacto_personas,
            "supuesto_riesgo": case.supuesto_riesgo,
            "restricciones": case.restricciones,
            "sponsor": case.sponsor,
            "mail_contacto": case.mail_contacto,
            "tipo_intent": {
                "negocio": case.intent_negocio,
                "operativo": case.intent_operativo,
                "capacidad_equipos": case.intent_capacidad_equipos,
                "tecnico_arquitectural": case.intent_tecnico_arquitectural,
            },
            "datos_requeridos": {
                "ninguno": case.datos_ninguno,
                "datos_publicos": case.datos_publicos,
                "datos_operativos": case.datos_operativos,
                "datos_personales": case.datos_personales,
                "datos_confidenciales": case.datos_confidenciales,
                "otros": {
                    "estado": case.datos_otros,
                    "message": case.datos_otros_mensaje,
                },
            },
        }
    }
