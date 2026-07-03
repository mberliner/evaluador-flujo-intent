"""Factory de clientes de agente (SPEC-013 FR-005).

Unico punto que conoce el condicional tipo-de-cliente -> adaptador concreto
y que resuelve el CredentialProvider correspondiente, para no duplicar ese
cableado en los composition roots (dashboard y runner).
"""

from __future__ import annotations

from src.adapters.platform_config import (
    CLIENT_TYPE_REMOTE_ASYNC,
    CLIENT_TYPE_SYNC_HTTP,
    KNOWN_CLIENT_TYPES,
    PlatformConfig,
)
from src.adapters.remote_agent_client import RemoteAgentClient
from src.adapters.sync_agent_client import SyncHttpAgentClient
from src.adapters.token_provider import StaticCredentialProvider, TokenProvider
from src.domain.ports import AgentClient, CredentialProvider


class UnknownClientTypeError(RuntimeError):
    """El tipo de cliente configurado no esta registrado en el factory (SC-003)."""


def _unknown(client_type: str) -> UnknownClientTypeError:
    return UnknownClientTypeError(
        f"Tipo de cliente de agente no registrado: '{client_type}'. "
        f"Valores registrados: {', '.join(KNOWN_CLIENT_TYPES)}."
    )


class AgentClientFactory:
    """Crea el AgentClient (y su CredentialProvider) segun la config activa."""

    @staticmethod
    def resolve_credentials(config: PlatformConfig) -> CredentialProvider:
        """Resuelve el proveedor de credenciales del tipo de cliente activo.

        Expuesto para que un composition root pueda validar credenciales de
        forma anticipada (p. ej. el dashboard antes de habilitar el envio) y
        luego inyectarlas en create() sin perder el cache.
        """
        if config.client_type == CLIENT_TYPE_REMOTE_ASYNC:
            return TokenProvider(config)
        if config.client_type == CLIENT_TYPE_SYNC_HTTP:
            return StaticCredentialProvider(config.alt_client_api_key)
        raise _unknown(config.client_type)

    @staticmethod
    def create(
        config: PlatformConfig,
        *,
        credentials: CredentialProvider | None = None,
        timeout_seconds: int = 120,
    ) -> AgentClient:
        """Instancia el adaptador que cumple el puerto AgentClient (FR-005)."""
        resolved = credentials or AgentClientFactory.resolve_credentials(config)
        if config.client_type == CLIENT_TYPE_REMOTE_ASYNC:
            return RemoteAgentClient(config, resolved, timeout_seconds=timeout_seconds)
        if config.client_type == CLIENT_TYPE_SYNC_HTTP:
            return SyncHttpAgentClient(config, resolved, timeout_seconds=timeout_seconds)
        raise _unknown(config.client_type)
