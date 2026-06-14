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

2. **Tooling de calidad** (validadores bloqueantes; el reparto por trigger —hook de commit, pipeline local, CI— es SSOT de [`docs/DEVELOPMENT.md`](../docs/DEVELOPMENT.md) §«Cuándo correr qué»):
   - `ruff` (lint + format) — hook de commit
   - `mypy --strict` sobre `src/` — hook de commit
   - Linter de naming agnóstico (ver [[SPEC-000-naming]]) — hook de commit
   - `import-linter` o equivalente: verifica que `domain/` no importe de `adapters/` ni `dashboard/` — hook de commit
   - `bandit` (seguridad estática sobre `src/`) — pipeline local + CI
   - `pytest` (debe correr aunque no haya tests todavía → exit 0) — pipeline local + CI (no es hook de commit ni de push)

3. **Documentación SSOT** por dominio (patrón EnVivo):
   - `docs/ARCHITECTURE.md`, `docs/DEVELOPMENT.md`, `docs/CONTRIBUTING.md`, `docs/PRODUCT.md`
   - `docs/SPEC-FORMAT.md` — template y convenciones del formato híbrido de specs (GitHub Spec Kit). SSOT del método de redacción de specs desde SPEC-004 en adelante.

4. **Configuración externa**:
   - `.env.example` con todas las vars requeridas (sin secretos)
   - `requirements.txt`
   - `pyproject.toml` (ruff, mypy, pytest)
   - `.pre-commit-config.yaml` (hooks de commit; los hooks locales son auto-contenidos vía `language: python`, no dependen del venv en PATH)
   - `.github/workflows/ci.yml` (GitHub Actions; corre los validadores de código solo ante cambios en `src/`, `tests/`, `tools/` o manifiestos — no ante cambios de `docs/`/`specs/`)

## Criterios de aceptación

- [x] Estructura de carpetas creada (incluye `schemas/` agregado en rev.2026-05-25)
- [x] `pip install -r requirements.txt` instala sin errores en Python ≥3.11 (venv activo y funcional)
- [x] `pre-commit run --all-files` pasa en verde (resuelto 2026-06-14: repo bajo git, hooks instalados; hooks locales `naming`/`import-linter` migrados a `language: python` para no depender del venv en PATH)
- [x] CI de GitHub Actions corre los validadores de código ante cambios en `src/`/`tests/`/`tools/`/manifiestos (`.github/workflows/ci.yml`, 2026-06-14)
- [x] `pytest` exit code 0 (suite completa verde)
- [x] `mypy --strict src` exit code 0 (sin errores de tipos)
- [x] `lint-imports` verifica la regla de capas (import-linter en `requirements-dev.txt`, contratos en `pyproject.toml`, corre como step en `tools/pipeline_local.sh`)
- [x] Linter de naming pasa — `tools/check_naming.py src tests tools` verde (2026-05-25)
- [x] `historial/sdd.md` registra el cierre de Iter 0 y todas las iters posteriores

## Convenciones de commit (cierre de iteración)

Cada cierre de iter incluye el bloque `[SDD-Check]`. El formato canónico y la
Definition of done son SSOT de [`docs/CONTRIBUTING.md`](../docs/CONTRIBUTING.md);
no se transcriben aquí para no duplicar el workflow.

## Notas

- El linter de naming y la verificación de capas se construyen como tareas dedicadas en Iter 0 o Iter 1. Si no están listos al cierre de Iter 0, esta spec queda `active` con criterios parcialmente cumplidos y arrastra deuda a Iter 1 (documentado en historial).
- **Deuda de git/triggers saldada (2026-06-14):** el único criterio pendiente (`pre-commit run --all-files`, bloqueado por «requiere git init») quedó cerrado. Se acotaron los hooks de commit a `^src/`, se retiró `pytest` del trigger `pre-push` (vivía solo en pipeline local) y se agregó CI de GitHub Actions filtrado por paths de código. El reparto vigente commit/push/pipeline/CI es SSOT de `docs/DEVELOPMENT.md`.
