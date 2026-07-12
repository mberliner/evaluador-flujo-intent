# SPEC-000-bootstrap — Estructura inicial del proyecto y tooling

**Estado:** active
**Iter:** 0
**Depende de:** [[SPEC-000-naming]]

## Propósito

Establecer la estructura mínima del proyecto, la configuración del entorno y las herramientas de validación que harán cumplir las reglas de calidad (naming, arquitectura, tests) desde el primer commit.

## Alcance

1. **Estructura de directorios** según arquitectura por capas:
   - `src/domain/`, `src/adapters/`, `src/build/`, `src/dashboard/`
   - `data/` (fuente humana + dataset enriquecido)
   - `specs/`, `docs/`, `historial/`
   - `tests/unit/`, `tests/integration/`, `runs/`

2. **Tooling de calidad** (todos bloqueantes pre-commit):
   - `ruff` (lint + format)
   - `mypy --strict` sobre `src/`
   - `pytest` (debe correr aunque no haya tests todavía → exit 0)
   - `import-linter` o equivalente: verifica que `domain/` no importe de `adapters/` ni `dashboard/`
   - Linter de naming agnóstico (ver [[SPEC-000-naming]])

3. **Documentación SSOT** por dominio (patrón EnVivo):
   - `docs/ARCHITECTURE.md`, `docs/DEVELOPMENT.md`, `docs/CONTRIBUTING.md`, `docs/PRODUCT.md`

4. **Configuración externa**:
   - `.env.example` con todas las vars requeridas (sin secretos)
   - `requirements.txt`
   - `pyproject.toml` (ruff, mypy, pytest)
   - `.pre-commit-config.yaml`

## Criterios de aceptación

- [x] Estructura de carpetas creada (incluye `schemas/`)
- [x] `pip install -r requirements.txt` instala sin errores en Python ≥3.11 (venv activo y funcional)
- [ ] `pre-commit run --all-files` pasa en verde (pendiente: requiere `git init`)
- [x] `pytest` exit code 0 (suite vacía, colección sin errores)
- [x] `mypy --strict src` exit code 0 (sin errores de tipos)
- [x] `lint-imports` verifica la regla de capas (import-linter en `requirements-dev.txt`, contratos en `pyproject.toml`, corre como step en `tools/pipeline_local.sh`)
- [x] Linter de naming pasa — `tools/check_naming.py src tests tools` verde
- [ ] `historial/sdd.md` registra el cierre de cada iteración

## Convenciones de commit (cierre de iteración)

Cada cierre de iter incluye el bloque `[SDD-Check]`. El formato canónico y la
Definition of done son SSOT de [`docs/CONTRIBUTING.md`](../docs/CONTRIBUTING.md);
no se transcriben aquí para no duplicar el workflow.

## Notas

- El linter de naming y la verificación de capas se construyen como tareas dedicadas en Iter 0 o Iter 1. Si no están listos al cierre de Iter 0, esta spec queda `active` con criterios parcialmente cumplidos y arrastra deuda a Iter 1 (documentado en historial).
