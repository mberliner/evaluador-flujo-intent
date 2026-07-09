"""Driver agnóstico de la interfaz web para tests de flujo.

Expone acciones con vocabulario de usuario (llenar, marcar, elegir, apretar)
y lecturas de lo que quedó en pantalla (errores, éxitos, estado de sesión).
Los tests hablan solo con este driver y localizan widgets por su label
visible, nunca por claves internas del framework.

El único punto acoplado al framework web es el import de abajo — la misma
estrategia que `import streamlit as ui` en src/dashboard/app.py. Si el
framework cambia, se reescribe este módulo y los tests quedan intactos.
"""

from __future__ import annotations

from typing import Any

from streamlit.testing.v1 import AppTest  # único acople al framework UI


class AppDriver:
    """Maneja la app headless como lo haría una persona: por labels visibles."""

    def __init__(self, app_path: str, *, timeout: float = 10.0) -> None:
        self._app = AppTest.from_file(app_path, default_timeout=timeout)

    def open(self) -> AppDriver:
        """Arranca la app y renderiza la primera pantalla."""
        self._app.run()
        return self

    # ── acciones ──────────────────────────────────────────────────────────

    def fill(self, label: str, value: str) -> None:
        """Escribe en un campo de texto (de una línea o multilínea)."""
        widgets = [*self._app.text_input, *self._app.text_area]
        self._find_by_label(widgets, label).set_value(value)

    def mark(self, label: str) -> None:
        """Marca una casilla de verificación."""
        self._find_by_label(list(self._app.checkbox), label).check()

    def choose(self, label: str, value: str) -> None:
        """Elige una opción en un desplegable (fuera de formulario: re-renderiza al toque)."""
        self._find_by_label(list(self._app.selectbox), label).select(value)
        self._app.run()

    def press(self, label: str) -> None:
        """Aprieta un botón por su texto y procesa la interacción."""
        self._find_by_label(list(self._app.button), label).click()
        self._app.run()

    # ── lecturas ──────────────────────────────────────────────────────────

    @property
    def errors(self) -> list[str]:
        """Mensajes de error visibles en pantalla."""
        return [str(e.value) for e in self._app.error]

    @property
    def successes(self) -> list[str]:
        """Mensajes de éxito visibles en pantalla."""
        return [str(s.value) for s in self._app.success]

    def session_value(self, key: str) -> Any:
        """Valor del estado de sesión, o None si la clave no existe."""
        try:
            return self._app.session_state[key]
        except KeyError:
            return None

    # ── interno ───────────────────────────────────────────────────────────

    @staticmethod
    def _find_by_label(widgets: list[Any], label: str) -> Any:
        for widget in widgets:
            if getattr(widget, "label", None) == label:
                return widget
        visibles = [str(getattr(w, "label", "?")) for w in widgets]
        raise AssertionError(f"No hay un widget '{label}' en pantalla. Visibles: {visibles}")
