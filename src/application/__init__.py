"""Capa de aplicación: use-cases de orquestación (ver docs/ARCHITECTURE.md §ADR-005).

Lógica que coordina dominio + puertos para ejecutar corridas, sin framework de
UI ni parsing de CLI. La consumen los composition roots (`src/runner.py` y
`src/dashboard/`). No importa de adapters concretos, dashboard ni runner.
"""
