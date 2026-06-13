"""Evaluador de clasificacion: extraccion por regex + match exacto.

Ver specs/SPEC-003-classification-evaluator.md para las reglas.
"""

from __future__ import annotations

import re
from typing import Any

from src.domain.ports import AgentResponse
from src.domain.result import TestResult
from src.domain.test_case import PALETA_CLASIFICACION, TestCase

_PATTERN: re.Pattern[str] = re.compile(
    r"\b(verde|amarillo|rojo|negro|rechazado)\b",
    re.IGNORECASE,
)

_RIESGO_PATTERN: re.Pattern[str] = re.compile(
    r"riesgo:\s*(VERDE|AMARILLO|ROJO|NEGRO)",
    re.IGNORECASE,
)

_CANON: dict[str, str] = {color.lower(): color for color in PALETA_CLASIFICACION}


def extract_classification(messages: list[dict[str, Any]]) -> str | None:
    """Extrae la clasificacion del primer mensaje assistant con patron 'riesgo: COLOR'.

    Devuelve la forma canonica de la paleta (title-case) o None.
    """
    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content", "")
        if not isinstance(content, str):
            continue
        if not content.lower().startswith("riesgo:"):
            continue
        match = _RIESGO_PATTERN.search(content)
        if match:
            return _CANON[match.group(1).lower()]
    return None


class ClassificationEvaluator:
    """Pure-domain: no I/O, sin dependencias externas."""

    def extract(self, response: str) -> str | None:
        """Primera ocurrencia de un termino de la paleta o None."""
        if not response:
            return None
        match = _PATTERN.search(response)
        if match is None:
            return None
        return _CANON[match.group(1).lower()]

    def evaluate(self, case: TestCase, agent_response: AgentResponse) -> TestResult:
        extracted = self.extract(agent_response.content)

        if extracted is None:
            passed: bool | None = None
            notes = "sin clasificacion detectada en la respuesta"
        else:
            passed = extracted == case.clasificacion_esperada
            notes = "" if passed else "clasificacion extraida no coincide con la esperada"

        return TestResult(
            case_id=case.id,
            expected=case.clasificacion_esperada,
            actual_response=agent_response.content,
            extracted_classification=extracted,
            passed=passed,
            conversation_id=agent_response.conversation_id,
            notes=notes,
        )
