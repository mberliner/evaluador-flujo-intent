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


def _set_env(monkeypatch: pytest.MonkeyPatch, env: dict[str, str]) -> None:
    for k in (*_FULL_ENV.keys(), "ACCURACY_THRESHOLD"):
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
