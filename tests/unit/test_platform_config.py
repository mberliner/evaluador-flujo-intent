"""Tests de PlatformConfig.from_env()."""

from __future__ import annotations

import pytest

from src.adapters.platform_config import MissingConfigError, PlatformConfig

_FULL_ENV = {
    "ES_URL_CHAT": "https://example/chat",
    "ES_URL_TOKEN": "https://example/token",
    "ES_AGENTS_URL": "https://example/agents",
    "ES_TOKEN": "apikey",
    "AGENT_ID": "agent-1",
}

_ALT_ENV = {
    "AGENT_CLIENT_TYPE": "sync_http",
    "ALT_CLIENT_URL": "https://alt.example/intents",
    "ALT_CLIENT_API_KEY": "llave-alt",
}


def _set_env(monkeypatch: pytest.MonkeyPatch, env: dict[str, str]) -> None:
    for k in (*_FULL_ENV.keys(), *_ALT_ENV.keys(), "ACCURACY_THRESHOLD"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)


def test_carga_env_completa(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch, _FULL_ENV)
    config = PlatformConfig.from_env(load_dotfile=False)
    assert config.chat_url == "https://example/chat/"  # trailing slash agregado
    assert config.agent_id == "agent-1"
    assert config.accuracy_threshold == 0.0


def test_flows_url_y_threads_url_se_derivan_de_chat_url(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch, _FULL_ENV)
    config = PlatformConfig.from_env(load_dotfile=False)
    assert config.flows_url == "https://example/chat/flows"
    assert config.threads_url == "https://example/chat/threads"


def test_chat_url_con_slash_no_se_duplica(monkeypatch: pytest.MonkeyPatch) -> None:
    env = {**_FULL_ENV, "ES_URL_CHAT": "https://example/chat/"}
    _set_env(monkeypatch, env)
    config = PlatformConfig.from_env(load_dotfile=False)
    assert config.chat_url == "https://example/chat/"


@pytest.mark.parametrize("missing", list(_FULL_ENV.keys()))
def test_falla_si_falta_var(monkeypatch: pytest.MonkeyPatch, missing: str) -> None:
    env = {k: v for k, v in _FULL_ENV.items() if k != missing}
    _set_env(monkeypatch, env)
    with pytest.raises(MissingConfigError, match=missing):
        PlatformConfig.from_env(load_dotfile=False)


def test_accuracy_threshold_se_parsea(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch, {**_FULL_ENV, "ACCURACY_THRESHOLD": "0.8"})
    config = PlatformConfig.from_env(load_dotfile=False)
    assert config.accuracy_threshold == 0.8


def test_accuracy_threshold_invalido_falla(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_env(monkeypatch, {**_FULL_ENV, "ACCURACY_THRESHOLD": "no-es-numero"})
    with pytest.raises(MissingConfigError, match="ACCURACY_THRESHOLD"):
        PlatformConfig.from_env(load_dotfile=False)


# ---------------------------------------------------------------------------
# Selección de tipo de cliente (SPEC-013 FR-001, FR-006, FR-009, SC-001/SC-003)
# ---------------------------------------------------------------------------


def test_sin_variable_de_seleccion_usa_cliente_original(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-001 / SC-001: sin AGENT_CLIENT_TYPE el default es el cliente original."""
    _set_env(monkeypatch, _FULL_ENV)
    config = PlatformConfig.from_env(load_dotfile=False)
    assert config.client_type == "remote_async"


def test_tipo_de_cliente_desconocido_falla_temprano(monkeypatch: pytest.MonkeyPatch) -> None:
    """SC-003: un tipo no registrado produce error de configuración detallado."""
    _set_env(monkeypatch, {**_FULL_ENV, "AGENT_CLIENT_TYPE": "no-existe"})
    with pytest.raises(MissingConfigError, match="AGENT_CLIENT_TYPE"):
        PlatformConfig.from_env(load_dotfile=False)


def test_cliente_alternativo_lee_variables_genericas(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-009: las credenciales del cliente alternativo salen de ALT_CLIENT_*."""
    _set_env(monkeypatch, _ALT_ENV)
    config = PlatformConfig.from_env(load_dotfile=False)
    assert config.client_type == "sync_http"
    assert config.alt_client_url == "https://alt.example/intents"
    assert config.alt_client_api_key == "llave-alt"


def test_cliente_alternativo_no_exige_variables_del_original(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-006: con sync_http activo, las ES_* ausentes no bloquean el arranque."""
    _set_env(monkeypatch, _ALT_ENV)
    config = PlatformConfig.from_env(load_dotfile=False)
    assert config.chat_url == ""
    assert config.api_key == ""


def test_cliente_original_no_exige_variables_alternativas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-006: con remote_async activo, las ALT_CLIENT_* ausentes no bloquean."""
    _set_env(monkeypatch, {**_FULL_ENV, "AGENT_CLIENT_TYPE": "remote_async"})
    config = PlatformConfig.from_env(load_dotfile=False)
    assert config.client_type == "remote_async"
    assert config.alt_client_url == ""


@pytest.mark.parametrize("missing", ["ALT_CLIENT_URL", "ALT_CLIENT_API_KEY"])
def test_cliente_alternativo_falla_si_falta_su_variable(
    monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    """FR-006: la requeridad depende del cliente activo — faltantes propias fallan."""
    env = {k: v for k, v in _ALT_ENV.items() if k != missing}
    _set_env(monkeypatch, env)
    with pytest.raises(MissingConfigError, match=missing):
        PlatformConfig.from_env(load_dotfile=False)


def test_agent_id_opcional_para_cliente_alternativo_cae_a_etiqueta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AGENT_ID es metadata para sync_http: sin definir, cae al tipo de cliente."""
    _set_env(monkeypatch, _ALT_ENV)
    config = PlatformConfig.from_env(load_dotfile=False)
    assert config.agent_id == "sync_http"

    _set_env(monkeypatch, {**_ALT_ENV, "AGENT_ID": "clasificador-v2"})
    config = PlatformConfig.from_env(load_dotfile=False)
    assert config.agent_id == "clasificador-v2"
