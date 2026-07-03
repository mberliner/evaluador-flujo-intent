"""Configuracion de la plataforma remota.

Unico punto del sistema que conoce los nombres especificos de las
variables de entorno del proveedor. El resto del codigo consume
atributos agnosticos de esta clase.

La seleccion del tipo de cliente de agente (SPEC-013 FR-001) y la
requeridad condicional de variables por tipo (FR-006, FR-009) viven aca:
el set de variables exigidas depende exclusivamente del cliente activo.
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


# Tipos de cliente registrados (SPEC-013 FR-001). El valor es contrato con el
# operador via AGENT_CLIENT_TYPE; los identificadores internos son agnosticos.
CLIENT_TYPE_REMOTE_ASYNC = "remote_async"
CLIENT_TYPE_SYNC_HTTP = "sync_http"

# Variables requeridas segun el tipo de cliente activo (FR-006).
_REQUIRED_VARS_BY_CLIENT: dict[str, tuple[str, ...]] = {
    CLIENT_TYPE_REMOTE_ASYNC: (
        "ES_URL_CHAT",
        "ES_URL_TOKEN",
        "ES_AGENTS_URL",
        "ES_TOKEN",
        "AGENT_ID",
    ),
    CLIENT_TYPE_SYNC_HTTP: (
        "ALT_CLIENT_URL",
        "ALT_CLIENT_API_KEY",
    ),
}

KNOWN_CLIENT_TYPES: tuple[str, ...] = tuple(_REQUIRED_VARS_BY_CLIENT)


class MissingConfigError(RuntimeError):
    """Falta una variable de entorno requerida o su valor es invalido."""


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
    client_type: str = CLIENT_TYPE_REMOTE_ASYNC
    alt_client_url: str = ""
    alt_client_api_key: str = ""

    @property
    def effective_endpoint_url(self) -> str:
        """URL efectiva del endpoint/agente bajo test, segun el cliente activo.

        Expone hacia afuera (dashboard, persistencia de corridas) la URL que hoy
        cada adaptador arma internamente, sin cambiar su contrato (SPEC-013
        FR-US2-001). Para `remote_async` replica la construccion de
        RemoteAgentClient.send; para `sync_http` es la URL alternativa tal cual.
        El identificador es agnostico al proveedor (SPEC-000-naming).
        """
        if self.client_type == CLIENT_TYPE_SYNC_HTTP:
            return self.alt_client_url
        return f"{self.chat_url}{self.agent_id}/chat/completions"

    @classmethod
    def from_env(cls, *, load_dotfile: bool = True) -> PlatformConfig:
        if load_dotfile:
            _load_dotenv()

        client_type = os.environ.get("AGENT_CLIENT_TYPE", "").strip() or CLIENT_TYPE_REMOTE_ASYNC
        if client_type not in _REQUIRED_VARS_BY_CLIENT:
            raise MissingConfigError(
                f"AGENT_CLIENT_TYPE desconocido: '{client_type}'. "
                f"Valores registrados: {', '.join(KNOWN_CLIENT_TYPES)}."
            )

        missing = [
            name for name in _REQUIRED_VARS_BY_CLIENT[client_type] if not os.environ.get(name)
        ]
        if missing:
            raise MissingConfigError(
                f"Variables de entorno requeridas faltantes (cliente '{client_type}'): "
                + ", ".join(missing)
            )

        chat_url = os.environ.get("ES_URL_CHAT", "")
        if chat_url and not chat_url.endswith("/"):
            chat_url += "/"

        threshold_raw = os.environ.get("ACCURACY_THRESHOLD", "0.0")
        try:
            threshold = float(threshold_raw)
        except ValueError as err:
            raise MissingConfigError(f"ACCURACY_THRESHOLD invalido: '{threshold_raw}'") from err

        return cls(
            chat_url=chat_url,
            token_url=os.environ.get("ES_URL_TOKEN", ""),
            agents_url=os.environ.get("ES_AGENTS_URL", ""),
            flows_url=chat_url + "flows" if chat_url else "",
            threads_url=chat_url + "threads" if chat_url else "",
            api_key=os.environ.get("ES_TOKEN", ""),
            # AGENT_ID identifica al agente bajo prueba en la metadata de las
            # corridas; para clientes alternativos es opcional (no hay agent id
            # nativo) y cae al tipo de cliente como etiqueta.
            agent_id=os.environ.get("AGENT_ID", "") or client_type,
            accuracy_threshold=threshold,
            client_type=client_type,
            alt_client_url=os.environ.get("ALT_CLIENT_URL", ""),
            alt_client_api_key=os.environ.get("ALT_CLIENT_API_KEY", ""),
        )
