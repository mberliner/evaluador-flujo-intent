"""Tests de TokenProvider con stub de requests.Session."""

from __future__ import annotations

from typing import Any

import pytest

from src.adapters.platform_config import PlatformConfig
from src.adapters.token_provider import TokenError, TokenProvider


class _StubResponse:
    def __init__(self, status_code: int, payload: dict[str, Any] | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text or str(payload)

    def json(self) -> dict[str, Any]:
        return self._payload


class _StubSession:
    def __init__(self, responses: list[_StubResponse]):
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def post(self, url: str, **kwargs: Any) -> _StubResponse:
        self.calls.append({"url": url, **kwargs})
        return self._responses.pop(0)


def _config() -> PlatformConfig:
    return PlatformConfig(
        chat_url="https://example/chat/",
        token_url="https://example/token",
        agents_url="https://example/agents",
        flows_url="https://example/chat/flows",
        threads_url="https://example/chat/threads",
        api_key="apikey-xyz",
        agent_id="agent-1",
    )


def test_obtiene_y_cachea_token() -> None:
    session = _StubSession([_StubResponse(200, {"access_token": "tok-1", "expires_in": 3600})])
    fake_clock = iter([0.0, 10.0, 20.0])

    def clock() -> float:
        return next(fake_clock)

    provider = TokenProvider(_config(), session=session, clock=clock)  # type: ignore[arg-type]
    assert provider.get() == "tok-1"
    assert provider.get() == "tok-1"
    assert len(session.calls) == 1


def test_refresca_token_cuando_expira() -> None:
    session = _StubSession(
        [
            _StubResponse(200, {"access_token": "tok-1", "expires_in": 100}),
            _StubResponse(200, {"access_token": "tok-2", "expires_in": 100}),
        ]
    )
    times = iter([0.0, 200.0, 201.0])

    def clock() -> float:
        return next(times)

    provider = TokenProvider(
        _config(),
        session=session,  # type: ignore[arg-type]
        clock=clock,
        safety_margin_seconds=0,
    )
    assert provider.get() == "tok-1"
    assert provider.get() == "tok-2"
    assert len(session.calls) == 2


def test_error_http_levanta() -> None:
    session = _StubSession([_StubResponse(401, text="unauthorized")])
    provider = TokenProvider(_config(), session=session)  # type: ignore[arg-type]
    with pytest.raises(TokenError, match="401"):
        provider.get()


def test_respuesta_sin_token_levanta() -> None:
    session = _StubSession([_StubResponse(200, {"expires_in": 3600})])
    provider = TokenProvider(_config(), session=session)  # type: ignore[arg-type]
    with pytest.raises(TokenError, match="access_token"):
        provider.get()
