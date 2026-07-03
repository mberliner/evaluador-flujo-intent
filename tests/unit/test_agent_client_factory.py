"""Tests de AgentClientFactory (SPEC-013 FR-005, SC-002, SC-003)."""

from __future__ import annotations

import pytest

from src.adapters.agent_client_factory import AgentClientFactory, UnknownClientTypeError
from src.adapters.platform_config import PlatformConfig
from src.adapters.remote_agent_client import RemoteAgentClient
from src.adapters.sync_agent_client import SyncHttpAgentClient
from src.adapters.token_provider import StaticCredentialProvider, TokenProvider


def _config(client_type: str) -> PlatformConfig:
    return PlatformConfig(
        chat_url="https://example/chat/",
        token_url="https://example/token",
        agents_url="https://example/agents",
        flows_url="https://example/chat/flows",
        threads_url="https://example/chat/threads",
        api_key="llave-original",
        agent_id="agent-1",
        client_type=client_type,
        alt_client_url="https://alt.example/intents",
        alt_client_api_key="llave-alt",
    )


def test_tipo_original_crea_el_cliente_remoto_asincronico() -> None:
    client = AgentClientFactory.create(_config("remote_async"))
    assert isinstance(client, RemoteAgentClient)


def test_tipo_alternativo_crea_el_cliente_sincronico() -> None:
    client = AgentClientFactory.create(_config("sync_http"))
    assert isinstance(client, SyncHttpAgentClient)


def test_tipo_no_registrado_falla_antes_de_cualquier_red() -> None:
    with pytest.raises(UnknownClientTypeError, match="no-registrado"):
        AgentClientFactory.create(_config("no-registrado"))


def test_resuelve_credenciales_segun_el_tipo() -> None:
    original = AgentClientFactory.resolve_credentials(_config("remote_async"))
    assert isinstance(original, TokenProvider)

    alternativo = AgentClientFactory.resolve_credentials(_config("sync_http"))
    assert isinstance(alternativo, StaticCredentialProvider)
    assert alternativo.get() == "llave-alt"


def test_resolver_credenciales_de_tipo_no_registrado_falla() -> None:
    with pytest.raises(UnknownClientTypeError):
        AgentClientFactory.resolve_credentials(_config("no-registrado"))
