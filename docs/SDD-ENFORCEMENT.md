# SDD-ENFORCEMENT — Cómo se hace cumplir la trazabilidad spec↔código

SSOT del mecanismo de enforcement del **Principio V** de `CONSTITUTION.md`
(Trazabilidad spec↔código). Describe *cómo* se hace cumplir "spec antes que
código", no *qué* es el invariante (eso vive en la constitución).

Este documento gobierna un cambio de **método/framework**, no de producto: por
eso vive en `docs/` y no como `SPEC-NNN` (ver Principio V y la decisión
`analisis/SDD/software/DECISION-ADOPTAR-VS-PORTAR-SPECKIT.md`, vía B).

---

## Las tres capas

El enforcement es defensa en profundidad. Ninguna capa sola alcanza.

| Capa | Cuándo actúa | Qué hace | Determinista |
|------|--------------|----------|--------------|
| **Gate de autoría** (`tools/sdd_gate.py`) | Antes de editar/commitear `src/` | Bloquea si no hay spec vigente declarada o si la spec no fue editada después de declararla (chequeo de mtime) | Sí |
| **Backstop del pipeline** (`tools/check_traceability.py`) | `bash tools/pipeline_local.sh` | Verifica integridad estructural y de cobertura de todas las specs | Sí |
| **Detección semántica** (playbooks `clarify`, `analyze`) | A pedido, durante la redacción | Detecta US/FR faltantes, ambigüedades, gaps de cobertura | No (LLM) |

### Por qué tres y no una

- El **gate** previene (es el único punto *anterior* a que el código exista). Verifica *presencia* de spec y que haya sido *editada* después de declararla (mtime), pero no juzga si el contenido es adecuado.
- El **check** es el backstop determinista; corre sobre todo el repo, pero es *a posteriori*.
- Los **playbooks** aportan el juicio de *adecuación* que ningún script puede dar, pero son probabilísticos y salteables.

> **Portabilidad (agnóstico de asistente).** El procedimiento de cada playbook
> es SSOT neutro en `docs/playbooks/{analyze,clarify}.md`. Cada asistente lo
> *envuelve* sin duplicarlo: Claude Code vía `.claude/skills/{analyze,clarify}/SKILL.md`;
> opencode vía `.opencode/command/{analyze,clarify}.md`; cualquier otro, pegando
> el playbook como prompt. Editar el playbook actualiza todos los wrappers.

El gate hace **obligatorio** correr el juicio; no lo reemplaza.

---

## El gate es multi-transporte (agnóstico de asistente)

`tools/sdd_gate.py` separa la **decisión** (`decide()`, lógica pura) del
**transporte** (cómo llega la ruta a evaluar). Acepta tres entradas con el mismo
contrato de salida (exit 0 permite, exit 2 bloquea, stderr lleva el motivo):

| Transporte | Quién lo usa | Wiring |
|------------|--------------|--------|
| **stdin JSON** | Claude Code (`PreToolUse`) | `.claude/settings.json` |
| **argv** (`sdd_gate.py src/a.py …`) | `pre-commit` (capa git), opencode (plugin) y cualquier hook que pase rutas | `.pre-commit-config.yaml` (hook `sdd-gate`); `.opencode/plugin/sdd-gate.js` (hook `tool.execute.before`) |
| **env** (`SDD_GATE_FILE=…`) | wrappers sin argv ni stdin | a definir por asistente |

Esto vuelve el enforcement preventivo **independiente del asistente**:

- **Claude Code** lo dispara antes de cada `Edit/Write` (más temprano, mejor UX).
- **git** lo dispara en `pre-commit` sobre los `src/` *staged* — el sustrato
  universal: cualquier asistente que commitee pasa por ahí, tenga hooks o no.
- **opencode**: el plugin `.opencode/plugin/sdd-gate.js` intercepta las tools de
  **escritura** (`edit`, `write`, `multiedit`, `apply_patch` y variantes de
  patch) en `tool.execute.before`, extrae **todas** las rutas que tocarían (de
  las claves `filePath`/`path` y parseando las cabeceras de patch estilo Codex
  `*** Add|Update|Delete File:` / `*** Move to:`), las normaliza a absolutas
  bajo `src/` y invoca `sdd_gate.py <ruta-absoluta>` por argv por cada una,
  abortando si el exit es 2 — paridad con el `PreToolUse` de Claude. Las rutas
  del patch son relativas al cwd de la tool, que la API NO expone al hook
  (`tool.execute.before` solo trae tool/sessionID/callID): si una relativa no
  cae en `src/` contra el root pero existe al resolverla bajo `src/`, se asume
  cwd interno a `src/` y se pasa la absoluta (si no, el gate la resolvería contra
  el root y se le escaparía). La *creación* de un archivo nuevo en `src/` con cwd
  interno a `src/` no es determinista aquí y la cubre el `pre-commit`. Es **fail-closed**: prueba intérpretes en orden
  (`.venv` → `python` → `python3`) y, si ninguno logra ejecutar el gate (exit ≠ 0
  y ≠ 2, p. ej. Python ausente o el alias stub de la Microsoft Store),
  **bloquea** en vez de permitir silenciosamente. La ruta llega en `input.args`
  (shape del runtime), no en `output.args` (lo que sugieren los tipos `.d.ts`);
  el plugin lee de ambos por robustez. Enganchar por nombre de tool es una
  allowlist (las tools de lectura no disparan el gate); las tools de escritura no
  contempladas las cubre el `pre-commit`. El hook del asistente pasó de *garante*
  a *tripwire temprano*.

El exit 2 sirve a ambos mundos: Claude lo interpreta como "bloquear y devolver el
motivo al asistente"; `pre-commit`/git lo interpreta como fallo → aborta el commit.

---

## Mecanismo de "spec vigente": `.sdd/current-spec`

El gate no asume git (diseñado para funcionar sin repositorio), así que no hay
"rama por feature". El sustituto es un archivo de declaración en la raíz del
proyecto:

- **`.sdd/current-spec`** MUST contener el ID de la spec que gobierna el trabajo en curso (ej. `SPEC-006-batch-suite`), una por línea.
- Antes de editar `src/`, el autor (humano o asistente) MUST declarar ahí la `SPEC-NNN`.
- El hook valida que el ID exista en `specs/` y esté registrado en `specs/SPECS_REGISTRY.md`. Si falta o es inválido, **bloquea** la edición con un mensaje accionable.
- **Chequeo de mtime**: además de existir, al menos una spec declarada MUST haber sido editada *después* de escribir `current-spec` (comparación `mtime(specs/SPEC-NNN.md) > mtime(.sdd/current-spec)`). Esto impide declarar una spec y saltar directo a codear sin actualizarla primero. El flujo obligado es: declarar → editar la spec (agregar/actualizar FR) → editar `src/`.
- Cambios de **framework/método** (que no tocan `src/`) no requieren declaración: el hook solo intercepta `src/`.

---

## Qué valida `tools/check_traceability.py`

Determinista, corre en el pipeline (`step "trazabilidad SDD"`). Sobre `specs/`:

1. **Estructura** (specs en formato híbrido, SPEC-004+ según el campo `Formato` del registro): presencia de `User Story` con prioridad, `Functional Requirements` con `FR-NNN`, `Success Criteria` con `SC-NNN`, y `Coverage mapping` (ver `docs/SPEC-FORMAT.md`).
2. **Consistencia spec↔registro**: toda `specs/SPEC-*.md` está registrada en `SPECS_REGISTRY.md` con un `Estado` válido; el registro no apunta a archivos inexistentes.
3. **Cobertura FR→test** (solo specs `active`): cada `FR-NNN` declarado aparece en el `Coverage mapping`, y toda referencia a un archivo `tests/...py` dentro del `Coverage mapping` existe.

Exit code: `0` OK, `1` violaciones, `2` error de uso.

---

## Límite honesto: presencia, no adecuación

Ni el hook ni el check juzgan si la spec **describe bien** el cambio. Verifican
que **exista** una spec gobernante y que las specs estén **bien formadas y
cubiertas**. La pregunta "¿este cambio introduce un requisito nuevo sin FR?"
—la que dejó pasar code-first el caso `run_id`— es un juicio de adecuación que
MUST quedar en los playbooks (`analyze`, `clarify`) y en la revisión humana.

---

## Follow-up registrado

- **FR→test estricto**: hoy las celdas de `Coverage mapping` son prosa. El check valida "todo FR aparece en el mapping" + "paths `tests/...py` referenciados existen", pero no exige que cada FR nombre un nodo de test concreto. El mapeo estricto FR→nodo requeriría **endurecer `docs/SPEC-FORMAT.md`** (celdas con identificadores de test) y migrar las tablas de las specs existentes. Diferido.
- **`pre-commit` corre el gate (desde 2026-06-21)**: el hook local `sdd-gate` ejecuta `tools/sdd_gate.py` sobre los `src/` *staged* (transporte argv), llevando el enforcement preventivo a la capa git — tool-agnóstica. El gate sigue funcionando *sin* git por diseño (vía `.sdd/current-spec` + el hook de Claude); pre-commit es una capa adicional, no un reemplazo.
- **opencode dispara el gate (desde 2026-06-21)**: el plugin `.opencode/plugin/sdd-gate.js` (`tool.execute.before`) invoca `tools/sdd_gate.py` por argv antes de cada `edit`/`write` y aborta si el exit es 2 — cierra la asimetría con el `PreToolUse` de Claude. Se versiona como `.js` sin imports de runtime (opencode inyecta `$`/`directory`), coherente con `.opencode/.gitignore` que no versiona `node_modules`.

---

## Referencias

- `CONSTITUTION.md` — Principio V (invariante).
- `docs/SPEC-FORMAT.md` — formato de spec que valida la capa estructural.
- `specs/SPECS_REGISTRY.md` — registro central de specs.
- `analisis/SDD/software/DECISION-ADOPTAR-VS-PORTAR-SPECKIT.md` — decisión de la vía B (externa al repo).
