"""Proveedor de tokens con cache + refresh.

desacoplado del session_state del framework UI original.
"""

from __future__ import annotations

import time
from collections.abc import Callable

import requests

from src.adapters.platform_config import PlatformConfig


class TokenError(RuntimeError):
    """Fallo obteniendo o refrescando el token."""


class StaticCredentialProvider:
    """Cumple el puerto CredentialProvider con una llave fija (SPEC-013).

    Para plataformas cuya auth es una llave estatica por header, sin ciclo
    de emision/refresh de token.
    """

    def __init__(self, key: str) -> None:
        self._key = key

    def get(self) -> str:
        if not self._key:
            raise TokenError("Credencial estatica vacia")
        return self._key


class TokenProvider:
    """Cumple el puerto CredentialProvider del dominio."""

    def __init__(
        self,
        config: PlatformConfig,
        *,
        safety_margin_seconds: int = 60,
        session: requests.Session | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._config = config
        self._safety_margin = safety_margin_seconds
        self._session = session or requests.Session()
        self._clock = clock
        self._cached: str | None = None
        self._expires_at: float = 0.0

    def get(self) -> str:
        if self._cached is not None and self._clock() < self._expires_at:
            return self._cached

        payload = {
            "apikey": self._config.api_key,
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            response = self._session.post(
                self._config.token_url,
                data=payload,
                headers=headers,
                timeout=20,
            )
        except requests.RequestException as err:
            raise TokenError(f"Fallo de red obteniendo token: {err}") from err

        if response.status_code != 200:
            body = response.text[:300] if response.text else ""
            raise TokenError(f"Error auth {response.status_code}: {body}")

        data = response.json()
        token = data.get("access_token")
        if not isinstance(token, str) or not token:
            raise TokenError("Respuesta sin access_token")

        expires_in = data.get("expires_in", 3600)
        try:
            expires_seconds = float(expires_in)
        except (TypeError, ValueError):
            expires_seconds = 3600.0

        self._cached = token
        self._expires_at = self._clock() + expires_seconds - self._safety_margin
        return token
