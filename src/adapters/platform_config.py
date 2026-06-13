"""Configuracion de la plataforma remota.

Unico punto del sistema que conoce los nombres especificos de las
variables de entorno del proveedor. El resto del codigo consume
atributos agnosticos de esta clase.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv as _load_dotenv
except ImportError:  # pragma: no cover - dotenv opcional
    from typing import Any as _Any

    def _load_dotenv(*_args: _Any, **_kwargs: _Any) -> bool:  # type: ignore[misc]
        return False


_REQUIRED_VARS: tuple[str, ...] = (
    "ES_URL_CHAT",
    "ES_URL_TOKEN",
    "ES_AGENTS_URL",
    "ES_TOKEN",
    "AGENT_ID",
)


class MissingConfigError(RuntimeError):
    """Falta una variable de entorno requerida."""


@dataclass(frozen=True, slots=True)
class PlatformConfig:
    chat_url: str
    token_url: str
    agents_url: str
    flows_url: str
    threads_url: str
    api_key: str
    agent_id: str
    accuracy_threshold: float = 0.0

    @classmethod
    def from_env(cls, *, load_dotfile: bool = True) -> PlatformConfig:
        if load_dotfile:
            _load_dotenv()

        missing = [name for name in _REQUIRED_VARS if not os.environ.get(name)]
        if missing:
            raise MissingConfigError(
                "Variables de entorno requeridas faltantes: " + ", ".join(missing)
            )

        chat_url = os.environ["ES_URL_CHAT"]
        if not chat_url.endswith("/"):
            chat_url += "/"

        threshold_raw = os.environ.get("ACCURACY_THRESHOLD", "0.0")
        try:
            threshold = float(threshold_raw)
        except ValueError as err:
            raise MissingConfigError(f"ACCURACY_THRESHOLD invalido: '{threshold_raw}'") from err

        return cls(
            chat_url=chat_url,
            token_url=os.environ["ES_URL_TOKEN"],
            agents_url=os.environ["ES_AGENTS_URL"],
            flows_url=chat_url + "flows",
            threads_url=chat_url + "threads",
            api_key=os.environ["ES_TOKEN"],
            agent_id=os.environ["AGENT_ID"],
            accuracy_threshold=threshold,
        )
