"""Normalización del contenido de un mensaje del thread.

El puerto `AgentClient.get_thread_messages` devuelve `list[dict]` donde el
`content` de cada mensaje puede venir como str plano o como lista de bloques
`{"text": ...}`. Esta función aplana ambos a str. Es lógica pura ligada al
contrato del puerto (no a un proveedor concreto), por eso vive en `domain/` y
la comparten adapters, application y dashboard (ver docs/ARCHITECTURE.md §ADR-005).
"""

from __future__ import annotations

from typing import Any


def extract_message_text(content: Any) -> str:
    """Normaliza el content de un mensaje (str o lista de bloques) a str plano."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(item.get("text", "") for item in content if isinstance(item, dict))
    return ""
