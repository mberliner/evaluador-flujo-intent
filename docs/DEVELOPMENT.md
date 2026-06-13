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
| Pipeline local completo (pre-SDD-Check) | `bash tools/pipeline_local.sh` |
| Pipeline local — detener al primer fallo | `bash tools/pipeline_local.sh --fail-fast` |
| Todo lo anterior vía hook de commit | `pre-commit run --all-files` |

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

### Commits

- Atómicos (un cambio por commit).
- Mensaje en imperativo: `feat: ...`, `fix: ...`, `docs: ...`, `refactor: ...`, `test: ...`, `chore: ...`.
- Cierre de iteración → incluir bloque `[SDD-Check]` (ver `docs/CONTRIBUTING.md`).

## Cuándo correr qué

- Cada cambio: `pre-commit run --all-files` (corre solo, hook bloquea commit).
- Antes de PR: tests unitarios + smoke + verificación de capas + naming.
- Cierre de iteración: `bash tools/pipeline_local.sh` (pipeline completo incluyendo seguridad), luego actualizar `specs/SPECS_REGISTRY.md` y `historial/sdd.md`.
