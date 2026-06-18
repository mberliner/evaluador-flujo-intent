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
| **Hook de autoría** (`tools/sdd_gate.py` vía `PreToolUse`) | Antes de editar `src/` | Bloquea la edición si no hay spec vigente declarada o si la spec no fue editada después de declararla (chequeo de mtime) | Sí |
| **Backstop del pipeline** (`tools/check_traceability.py`) | `bash tools/pipeline_local.sh` | Verifica integridad estructural y de cobertura de todas las specs | Sí |
| **Detección semántica** (skills `/clarify`, `/analyze`) | A pedido, durante la redacción | Detecta US/FR faltantes, ambigüedades, gaps de cobertura | No (LLM) |

### Por qué tres y no una

- El **hook** previene (es el único punto *anterior* a que el código exista), pero solo gobierna la ruta del asistente. Verifica *presencia* de spec y que haya sido *editada* después de declararla (mtime), pero no juzga si el contenido es adecuado.
- El **check** es el backstop determinista; corre sobre todo el repo, pero es *a posteriori*.
- Las **skills** aportan el juicio de *adecuación* que ningún script puede dar, pero son probabilísticas y salteables.

El hook hace **obligatorio** correr el juicio; no lo reemplaza.

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
MUST quedar en las skills (`/analyze`, `/clarify`) y en la revisión humana.

---

## Follow-up registrado

- **FR→test estricto**: hoy las celdas de `Coverage mapping` son prosa. El check valida "todo FR aparece en el mapping" + "paths `tests/...py` referenciados existen", pero no exige que cada FR nombre un nodo de test concreto. El mapeo estricto FR→nodo requeriría **endurecer `docs/SPEC-FORMAT.md`** (celdas con identificadores de test) y migrar las tablas de las specs existentes. Diferido.
- **`pre-commit` activo (desde 2026-06-14)**: el repo está bajo git con hooks de commit acotados a `^src/`. Esto complementa el hook del asistente (`sdd_gate.py`) con un backstop que cubre la ruta humana. El gate sigue siendo independiente de git por diseño.

---

## Referencias

- `CONSTITUTION.md` — Principio V (invariante).
- `docs/SPEC-FORMAT.md` — formato de spec que valida la capa estructural.
- `specs/SPECS_REGISTRY.md` — registro central de specs.
- `analisis/SDD/software/DECISION-ADOPTAR-VS-PORTAR-SPECKIT.md` — decisión de la vía B (externa al repo).
