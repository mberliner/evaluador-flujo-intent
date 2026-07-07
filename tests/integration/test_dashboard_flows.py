"""PoC de tests de flujo del dashboard (SPEC-001 / SPEC-003, modo simple).

Ejecuta la app real headless — sin browser ni red — a través del driver
agnóstico de tests/integration/ui_driver.py. La config y el cliente del
agente se stubean en el composition root, igual que en test_runner.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.adapters.agent_client_factory import AgentClientFactory
from src.adapters.platform_config import MissingConfigError, PlatformConfig
from src.domain.ports import AgentResponse
from tests.integration.ui_driver import AppDriver

_APP_PATH = str(Path(__file__).parents[2] / "src" / "dashboard" / "app.py")


class _StubConfig:
    agent_id = "agent-x"
    effective_endpoint_url = "https://agente.example/chat"


class _StubCredentials:
    def get(self) -> str:
        return "token-stub"


class _StubClient:
    """Cliente del agente sin red: siempre responde 'Verde'."""

    def send(self, form: dict[str, Any], conversation_id: str | None = None) -> AgentResponse:
        return AgentResponse(content="A new flow has started", conversation_id="thread-1")

    def wait_for_completion(self, thread_id: str, timeout_seconds: int = 300) -> bool:
        return True

    def get_thread_messages(self, thread_id: str) -> list[dict[str, Any]]:
        return [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "La clasificacion es Verde"},
        ]

    def get_final_response(self, thread_id: str, fallback_content: str) -> AgentResponse:
        return AgentResponse(content="La clasificacion es Verde", conversation_id=thread_id)


def _patch_runtime(monkeypatch: Any) -> None:
    """Sustituye config, credenciales y cliente en el composition root."""
    monkeypatch.setattr(PlatformConfig, "from_env", staticmethod(lambda: _StubConfig()))
    monkeypatch.setattr(
        AgentClientFactory, "resolve_credentials", staticmethod(lambda config: _StubCredentials())
    )
    monkeypatch.setattr(
        AgentClientFactory,
        "create",
        staticmethod(lambda config, credentials=None, timeout_seconds=0: _StubClient()),
    )


def _driver() -> AppDriver:
    return AppDriver(_APP_PATH).open()


def _fill_valid_case(app: AppDriver) -> None:
    """Completa el formulario de caso individual con datos mínimos válidos."""
    app.fill("Nombre de la iniciativa", "Iniciativa X")
    app.mark("Negocio")
    app.fill("Declaracion del intent", "decl")
    app.fill("Area proponente", "area")
    app.fill("Flujo de valor", "flujo")
    app.fill("Metricas de exito", "metricas")
    app.fill("Impacto en personas", "impacto")
    app.mark("Ninguno")
    app.fill("Supuesto / riesgo", "riesgo")
    app.fill("Restricciones", "restric")
    app.fill("Sponsor", "sponsor")
    app.fill("Mail de contacto", "a@b.com")
    # "Clasificacion esperada" queda en "Verde" (primera opción por defecto).


def test_formulario_incompleto_muestra_error_y_no_valida_caso() -> None:
    app = _driver()
    app.press("Validar caso")  # todo vacío: sin nombre, sin intent, sin datos
    assert any("Validacion fallida" in e for e in app.errors)
    assert app.session_value("case_validated") is None


def test_formulario_valido_deja_el_caso_listo_para_enviar() -> None:
    app = _driver()
    _fill_valid_case(app)
    app.press("Validar caso")
    assert app.errors == []
    assert any("Caso valido" in s for s in app.successes)
    assert app.session_value("case_validated") is not None


def test_envio_con_config_incompleta_muestra_error_sin_llamar_al_agente(
    monkeypatch: Any,
) -> None:
    def _raise() -> None:
        raise MissingConfigError("falta VAR_X")

    monkeypatch.setattr(PlatformConfig, "from_env", staticmethod(_raise))

    app = _driver()
    _fill_valid_case(app)
    app.press("Validar caso")
    app.press("Enviar al agente")
    assert any("Configuracion incompleta" in e for e in app.errors)


def test_camino_feliz_muestra_pass_y_persiste_la_corrida(monkeypatch: Any, tmp_path: Path) -> None:
    _patch_runtime(monkeypatch)
    monkeypatch.chdir(tmp_path)  # la persistencia por defecto escribe en ./runs

    app = _driver()
    _fill_valid_case(app)
    app.press("Validar caso")
    app.press("Enviar al agente")

    assert any(s.startswith("PASS") for s in app.successes)
    assert app.errors == []
    assert (tmp_path / "runs").is_dir()  # la corrida quedó persistida
