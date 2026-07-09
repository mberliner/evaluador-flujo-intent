# DEVELOPMENT — Setup y flujo de trabajo

SSOT de cómo correr el proyecto localmente.

## Requisitos

- Python ≥ 3.11
- `pip` ≥ 23
- Acceso al agente bajo test (credenciales en `.env`)

## Setup inicial

### Entorno virtual (opcional en desarrollo)

Puedes trabajar directamente con el Python del sistema o usar un entorno virtual.
Se recomienda el entorno virtual para aislar dependencias.

**Linux / macOS**
```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Instalación de dependencias

**Linux / macOS**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pre-commit install
cp .env.example .env             # rellenar con credenciales reales
```

**Windows (PowerShell)**
```powershell
pip install -r requirements.txt
pip install -r requirements-dev.txt
pre-commit install
Copy-Item .env.example .env      # rellenar con credenciales reales
```

## Comandos clave

| Acción | Comando |
|---|---|
| Dashboard (modo simple — Iter 1+) | `streamlit run src/dashboard/app.py` |
| Tests unitarios | `pytest tests/unit -v` |
| Smoke test (golpea agente real) | `pytest tests/integration -v -k smoke` |
| Suite headless (modo batch) | `python -m src.runner --in <archivo> --out runs/` |
| Estadística de suite a archivo + pantalla (sin ejecutar) | `python -m src.runner --estadistica --out runs/` |
| Lint + format | `ruff check src tests && ruff format src tests` |
| Type check | `mypy --strict src` |
| Verificar capas | `lint-imports` |
| Verificar naming agnóstico | `python tools/check_naming.py src/` |
| Seguridad estática | `bandit -r src -q` |
| Cobertura de tests (mínimo 80%) | `pytest tests/unit tests/integration --cov=src --cov-report=term-missing` |
| Cobertura de `src/domain` (mínimo 96%) | `pytest tests/unit --cov=src/domain --cov-report=term-missing --cov-fail-under=96` |
| Pipeline local completo (pre-SDD-Check) | `bash tools/pipeline_local.sh` |
| Pipeline local — detener al primer fallo | `bash tools/pipeline_local.sh --fail-fast` |
| Hooks de commit (ruff, mypy, naming, capas) | `pre-commit run --all-files` |

## Convenciones

### Estilo

- `ruff` con configuración en `pyproject.toml` (line length 100, target py311).
- `mypy --strict`. Nada de `Any` sin justificación documentada.
- Imports absolutos desde `src.` raíz.

### Naming

Aplicar `specs/SPEC-000-naming.md`. Los identificadores en `src/` no pueden contener referencias a proveedor, framework UI, formato o protocolo de auth.

### Tests

- AAA (Arrange-Act-Assert).
- Unit tests: rápidos, sin red, sin filesystem (usar `tmp_path` cuando hace falta).
- Integration tests: con marker `@pytest.mark.smoke`, requieren `.env` con credenciales válidas.
- Cobertura mínima: **80%** sobre `src/` (unit + integration combinados). Gate configurado en `pyproject.toml` (`[tool.coverage.report].fail_under`), forzado en el pipeline local y en CI.
- Cobertura mínima reforzada: **96%** sobre `src/domain` (solo unit — la capa de lógica de negocio pura no depende de red/filesystem). Umbral más estricto que el global porque el Principio II/III de `CONSTITUTION.md` la marca como núcleo determinista; pasado por línea de comando (`--cov-fail-under=96`) ya que `coverage.py` no admite dos `fail_under` distintos en el mismo `pyproject.toml`.

### Commits

- Atómicos (un cambio por commit).
- Mensaje en imperativo: `feat: ...`, `fix: ...`, `docs: ...`, `refactor: ...`, `test: ...`, `chore: ...`.
- Cierre de iteración → incluir bloque `[SDD-Check]` (ver `docs/CONTRIBUTING.md`).

## Cuándo correr qué

Reparto por trigger (SSOT):

- **Hook de commit** (`pre-commit`, bloquea el commit): ruff (lint+format), mypy `--strict`, naming agnóstico y capas (`import-linter`), acotados a `^src/`. Los hooks locales son auto-contenidos (`language: python`): no requieren el venv en PATH.
- **Push**: sin hooks. (`pytest` se retiró del `pre-push` el 2026-06-14; vivía solo en el pipeline local.)
- **Pipeline local** (`bash tools/pipeline_local.sh`, cierre de iteración): todo lo del commit + gobernanza (constitución, trazabilidad SDD) + `bandit` + `pytest tests/unit` + `pytest tests/integration` + cobertura global (`--cov-fail-under=80`, unit+integration combinados) + cobertura de domain (`--cov-fail-under=96`, solo unit).
- **CI — GitHub Actions** (`.github/workflows/ci.yml`): valida el código (ruff, mypy, naming, capas, bandit, pytest unit, pytest integration, cobertura global ≥80%, cobertura domain ≥96%) ante `push` a `main` o PR que toque `src/`, `tests/`, `tools/` o manifiestos. Cambios solo de `docs/`/`specs/`/`historial/` no lo disparan. No incluye los gates de gobernanza documental.

Resumen operativo:

- Cada cambio: `pre-commit run --all-files` (corre solo, hook bloquea commit).
- Antes de PR: tests unitarios + smoke + verificación de capas + naming.
- Cierre de iteración: `bash tools/pipeline_local.sh` (pipeline completo incluyendo seguridad), luego actualizar `specs/SPECS_REGISTRY.md` y `historial/sdd.md`.
