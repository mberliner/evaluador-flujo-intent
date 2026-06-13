"""Modelo de caso de prueba del dominio.

SSOT del shape y reglas de un caso. Sin dependencias externas, sin I/O.
Ver specs/SPEC-001-single-case-input.md para los criterios de validacion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PALETA_CLASIFICACION: tuple[str, ...] = ("Verde", "Amarillo", "Rojo", "Negro", "Rechazado")


def _require_non_empty(field_name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Campo requerido '{field_name}' vacio o invalido")
    return value.strip()


@dataclass(frozen=True, slots=True)
class TestCase:
    """Caso de prueba inmutable."""

    __test__ = False  # evita que pytest lo recolecte como clase de test

    id: str
    nombre_iniciativa: str

    intent_negocio: bool
    intent_operativo: bool
    intent_capacidad_equipos: bool
    intent_tecnico_arquitectural: bool

    declaracion_intent: str
    area_proponente: str
    flujo_de_valor: str
    metricas_de_exito: str
    impacto_personas: str

    datos_ninguno: bool
    datos_publicos: bool
    datos_operativos: bool
    datos_personales: bool
    datos_confidenciales: bool
    datos_otros: bool
    datos_otros_mensaje: str

    supuesto_riesgo: str
    restricciones: str
    sponsor: str
    mail_contacto: str

    clasificacion_esperada: str
    marcadores: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for name in (
            "id",
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
        ):
            cleaned = _require_non_empty(name, getattr(self, name))
            object.__setattr__(self, name, cleaned)

        if not any(
            (
                self.intent_negocio,
                self.intent_operativo,
                self.intent_capacidad_equipos,
                self.intent_tecnico_arquitectural,
            )
        ):
            raise ValueError("Debe marcarse al menos un tipo de intent")

        if not any(
            (
                self.datos_ninguno,
                self.datos_publicos,
                self.datos_operativos,
                self.datos_personales,
                self.datos_confidenciales,
                self.datos_otros,
            )
        ):
            raise ValueError("Debe marcarse al menos una categoria de datos requeridos")

        if self.clasificacion_esperada not in PALETA_CLASIFICACION:
            raise ValueError(
                f"clasificacion_esperada invalida; debe ser una de {PALETA_CLASIFICACION}"
            )

        if not self.datos_otros:
            object.__setattr__(self, "datos_otros_mensaje", "N/A")
        elif not self.datos_otros_mensaje.strip():
            raise ValueError("Campo requerido 'datos_otros_mensaje' vacio cuando datos_otros=True")

        if not isinstance(self.marcadores, tuple):
            object.__setattr__(self, "marcadores", tuple(self.marcadores))

    def expected(self) -> dict[str, Any]:
        """Ground truth del caso (no se envia al agente)."""
        return {
            "clasificacion": self.clasificacion_esperada,
            "marcadores": list(self.marcadores),
        }
