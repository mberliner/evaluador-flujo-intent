#!/usr/bin/env bash
# Pipeline local SDD — verifica el proyecto antes del SDD-Check.
# Combina los checks propios del proyecto con los incorporados de reflexio (bandit).
#
# Uso: bash tools/pipeline_local.sh [--fail-fast]
# Ejecutar desde la raiz del proyecto.

set -euo pipefail

FAIL_FAST=0
[[ "${1:-}" == "--fail-fast" ]] && FAIL_FAST=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Agrega scripts de pip --user al PATH para que lint-imports y otros ejecutables
# instalados con --user sean encontrados en este shell.
PY_USER_SCRIPTS="$(python -c 'import sysconfig; print(sysconfig.get_path("scripts","nt_user"))' 2>/dev/null || true)"
if [[ -n "$PY_USER_SCRIPTS" ]]; then
    PY_USER_SCRIPTS_UNIX="$(cygpath -u "$PY_USER_SCRIPTS" 2>/dev/null || echo "$PY_USER_SCRIPTS")"
    export PATH="$PY_USER_SCRIPTS_UNIX:$PATH"
fi

failed=()
total=0

step() {
    local label="$1"; shift
    total=$((total + 1))
    echo ""
    echo "--- $label ---"
    if (cd "$REPO_ROOT" && "$@"); then
        echo "[OK]    $label"
    else
        failed+=("$label")
        echo "[FALLO] $label"
        if [[ $FAIL_FAST -eq 1 ]]; then
            echo "Pipeline detenido por --fail-fast."
            exit 1
        fi
    fi
}

# ── entorno ───────────────────────────────────────────────────────────────────

step "hooks git instalados" python tools/bootstrap_hooks.py

# ── gobernanza ──────────────────────────────────────────────────────────────

step "constitucion"        python tools/check_constitution.py CONSTITUTION.md
step "trazabilidad SDD"    python tools/check_traceability.py specs

# ── calidad de codigo ─────────────────────────────────────────────────────────

step "ruff lint"           python -m ruff check src tests tools
step "ruff format --check" python -m ruff format --check src tests tools
step "mypy --strict"       python -m mypy --strict src
step "naming agnostico"    python tools/check_naming.py src tests
step "lint-imports"        lint-imports
step "skills multi-tool"   python tools/gen_skill_adapters.py --check

# ── seguridad ─────────────────────────────────────────────────────────────────

step "bandit (seguridad)"  python -m bandit -r src -q

# ── tests ─────────────────────────────────────────────────────────────────────

step "pytest unit"         python -m pytest tests/unit -v
step "pytest integration"  python -m pytest tests/integration -v

# ── resumen ───────────────────────────────────────────────────────────────────

echo ""
echo "=================================================="
ok=$((total - ${#failed[@]}))
if [[ ${#failed[@]} -eq 0 ]]; then
    echo "Pipeline local: VERDE — $total/$total pasos OK"
    exit 0
else
    echo "Pipeline local: ROJO — $ok/$total OK, ${#failed[@]} fallo(s):"
    for f in "${failed[@]}"; do
        echo "  x $f"
    done
    exit 1
fi
