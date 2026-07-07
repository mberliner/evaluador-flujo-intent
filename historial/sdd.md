# Historial SDD — log evolutivo de iteraciones

Cada entrada registra el cierre de una iteración: scope, decisiones tomadas, specs afectadas, deuda arrastrada. Sirve como memoria del proyecto para detectar cascadas ocultas y validar que las specs son vivas.

---

## 2026-07-05 — Compactación segunda tanda (SPEC-010, SPEC-009, SPEC-011)

**Scope:** editorial, sin tocar `src/`: `specs/SPEC-010-batch-trace.md`, `specs/SPEC-009-parallel-execution.md`, `specs/SPEC-011-agent-under-test.md`. Completa la revisión de candidatas detectadas tras la tanda anterior; **sin cambio normativo** en las tres (IDs de FR/SC, decisiones y semántica intactos).

**Decisiones tomadas:**

- **SPEC-010** (la más densa del repo): el «Hallazgo de correlación» queda como referencia única — su consecuencia estaba re-explicada en FR-US1-004, en los Why-priority, en Assumptions y en Historial; ahora la sección concentra también el descarte de backfill y de re-fetch. Las decisiones de diseño (traza embebida, captura única/opción C) pasan a notas `>` bajo FR-US2-001/007. Coverage agrupado, historial podado.
- **SPEC-009**: Resumen ejecutivo, coverage agrupado FR+SC (mismo artefacto), invariante de naming a una línea, entrada de historial 2026-06-09 comprimida (el mapeo de renumeración queda referido al commit).
- **SPEC-011**: Resumen ejecutivo; justificaciones de capa/typing/reconciliaciones movidas a notas `>` (FR-002/011/014); FR-009 a una línea; IDs `SC-001..SC-003` del coverage escritos literales (convención 5).

**Deuda:** ninguna nueva. Las specs restantes (SPEC-007, 008, 004, 005, 001, 003, 003b, 002b, 000) están en tamaño razonable; sólo les falta el bloque `**Resumen:**`, que se agrega oportunísticamente.

---

## 2026-07-05 — Compactación de las specs restantes (SPEC-006, SPEC-012, SPEC-002)

**Scope:** editorial, sin tocar `src/`: `specs/SPEC-006-batch-suite.md`, `specs/SPEC-012-translation-evaluator.md`, `specs/SPEC-002-agent-client.md`. Salda la deuda declarada en la entrada anterior (se aplicó como migración pedida por el usuario, no oportunística).

**Decisiones tomadas:**

- Las tres reescrituras son **sin cambio normativo**: IDs de FR/SC, contratos y semántica intactos; pipeline VERDE 10/10 (286 tests).
- **SPEC-006** (3.980 → 3.498 palabras): resumen ejecutivo, reglas separadas de justificaciones (notas `>`), invariantes de naming a una línea, coverage agrupado (FR+SC que comparten artefacto), historial podado y reordenado cronológicamente; el mapeo de renumeración FR-viejo→FR-USn queda referido al commit de la migración 2026-05-27.
- **SPEC-012** (4.191 → 3.984): extraída la sección **«Contrato del caso de traducción»** como referencia única del modelo de caso (antes repetido entre FR-US1-001, FR-US2-002, FR-US3-002 y Key Entities); FRs adelgazados con notas.
- **SPEC-002** (1.563 → 1.433): resumen ejecutivo, narrativa de métodos condensada en notas, historial podado. Formato casero pre-híbrido conservado (migrarlo a híbrido sería cambio de fondo, no editorial).
- Ganancia menor que el piloto (−12%/−5%/−8% vs. −46% de SPEC-013): estas specs tenían menos duplicación; el valor principal es estructural (resumen, contrato único, regla/nota).

**Deuda:** ninguna nueva; la deuda de formato verboso queda saldada.

---

## 2026-07-05 — Convenciones de compacidad de specs + Principio VI (SSOT único por tema)

**Scope:** cambio de método SDD, sin tocar `src/`: `CONSTITUTION.md` (0.5.2 → 0.6.0), `docs/SPEC-FORMAT.md`, `specs/SPEC-013-client-adapter-selection.md` (piloto).

**Decisiones tomadas:**

- **Piloto de compactación sobre SPEC-013:** reescritura editorial de 6.573 → 3.533 palabras (−46%) **sin cambio normativo** (IDs y semántica de FR/SC intactos). Palancas: resumen ejecutivo, sección única «Contrato verificado de la plataforma síncrona» (el detalle estaba repetido en FR-US1-010/011, FR-US3-003, Clarifications e Historial), regla separada de justificación en los FR (notas `>`), invariantes constitucionales reducidos a una línea, coverage mapping agrupado, historial podado a qué + por qué.
- **Convenciones formalizadas en `docs/SPEC-FORMAT.md`** (sección «Convenciones de compacidad», 6 reglas). Migración de las demás specs: **oportunística** — al tocar una spec por otro motivo se compacta en el mismo cambio; sin migración masiva dedicada.
- **Enmienda constitucional (MINOR → 0.6.0): nuevo Principio VI — SSOT único por tema.** El invariante ya operaba disperso (AGENTS.md, SPEC-FORMAT, delegaciones tipo SPEC-013→SPEC-005) sin casa formal; la compactación es en el fondo enforcement de este principio. Enforcement: revisión editorial + `/analyze`; detalle en `00-INDEX.md` y `docs/SPEC-FORMAT.md`.
- **Límite del checker documentado:** `check_traceability.py` exige IDs literales completos en el coverage mapping; los rangos (`FR-US1-001..007`) no cuentan como cobertura. Se documenta en la convención 5 en lugar de extender el tool.

**Deuda:** las specs pesadas restantes (SPEC-006, SPEC-012, SPEC-002) siguen en formato verboso hasta que un cambio las toque.

---

## 2026-07-04 — SPEC-006 FR-US1-008: fix índice por caso en progreso batch

**Scope:** `src/dashboard/app.py` — `_run_batch_tick`  
**Decisión:** `for r in done` usaba `len(done)` como índice, mostrando el mismo número para todos los casos completados en cada rerender. Corregido con `enumerate(done, 1)` para que cada fila tenga su índice fijo.  
**Specs afectadas:** SPEC-006 (FR-US1-008 actualizado para explicitar que el índice es posición fija, no tamaño del slice).  
**Deuda:** ninguna nueva.

---

## 2026-07-04 — SPEC-008 FR-010: generate_metrics_report como caso de uso

**Scope:** `src/domain/metrics.py`, nuevo `src/application/generate_metrics_report.py`, `src/domain/ports.py`, `src/runner.py`, `src/dashboard/app.py`, `tests/unit/test_runner.py`.

**Decisiones tomadas:**

- **`format_metrics_report` se mueve a `domain/`**: era una función pura atrapada en `runner.py` (entry point CLI). Al moverla a `src/domain/metrics.py` queda donde corresponde según la arquitectura en capas.
- **Caso de uso en `application/`**: la orquestación `aggregate_suite_metrics → format_metrics_report → repo.save_metrics_report` vive en `src/application/generate_metrics_report.py`, compartido entre el runner headless y el dashboard.
- **Puerto, no adaptador concreto**: el caso de uso recibe `RunRepository` (protocolo de `domain/ports.py`), no `FileRunRepository`. Se extendió el protocolo con `load_all` y `save_metrics_report` para completar el contrato.
- **Dashboard actualizado (FR-010)**: `_render_run_stats_control` llama al caso de uso tras `regenerate_run_stats`, dejando `estadistica-corridas.csv` y `estadistica-matriz.csv` siempre sincronizados en la misma operación de UI.
- **Runner simplificado**: `_report_total_metrics` delega el guardado CSV al caso de uso en lugar de orquestar los tres pasos a mano.

**Verificación:** Pipeline local VERDE 10/10 (286 tests). Sin tests nuevos (la función ya tenía cobertura; el caso de uso es una composición directa de funciones ya cubiertas).

---

## 2026-07-03 — SPEC-013 User Story 3: traza sintetizada del pipeline síncrono

**Scope: toca sólo `src/adapters/sync_agent_client.py` + tests + spec.** La respuesta `200` de la plataforma síncrona ya trae las etapas del pipeline (`output_integridad → output_impacto → output_factibilidad → output_fastgate → output_redactor_mail`), pero el adaptador las descartaba al colapsar sólo el color (FR-US1-011), dejando el visor "Traza de ejecución" (SPEC-007) vacío para `sync_http`. Se sintetiza un `AgentTrace` desde esa respuesta ya obtenida, sin llamadas de red extra, reusando el modelo y el visor de SPEC-007 sin modificarlos.

**Decisiones tomadas:**

- **Síntesis agnóstica a la forma interna** (FR-US3-004): el estado del paso se decide sólo por presencia/contenido no vacío del bloque (`_has_content`), nunca leyendo un campo interno como `resultado`. Bloque con contenido → `completed`; ausente/`null`/vacío → `skipped`; **nunca `failed`** (un `false` de negocio no es fallo técnico, Principio III). Coherente con Clarifications US3 2026-07-03: sólo `output_fastgate` y el discriminador `null` están verificados empíricamente; la forma interna de los demás bloques no se sondeó, por eso no se asume.
- **Cache extendido, sin red extra** (FR-US3-001): `send` retiene el body crudo (`self._bodies`) junto al veredicto ya cacheado; `get_trace` opera sobre lo cacheado (a diferencia de `RemoteAgentClient.get_trace`, que sí consulta `/flows`).
- **Orden fijo del pipeline** (FR-US3-003): constante `_PIPELINE_STAGES` con `step_id` agnóstico y estable, clave `output_*` (confinada al adapter, ADR-001) y etiqueta legible; independiente del orden de claves del body. Consecuencias deliberadas verificadas en test: el gate que corto-circuitó queda `completed` (llegó con contenido) y `output_redactor_mail` (presente en ambas ramas) queda `completed` tras etapas `skipped`.
- **Reuso sin modificar SPEC-007**: `AgentTrace`/`TraceStep` se consumen tal cual; `trace_panel.py` renderiza sin cambios (FR-US3-008). `overall_status="completed"` para un `200`, `flow_id=None`; campos sin dato nativo (`duration_ms`, `child_flow_id`, `started_at`, `completed_at`) en `None`. `get_thread_messages` sigue `[]`.
- **Tolerancia a fallo** (FR-US3-007): fallo técnico (`conversation_id=None`) o `thread_id` sin cache → `AgentTrace(steps=())` sin excepción.

**Verificación:** Pipeline local **VERDE 10/10** (286 tests). 8 tests nuevos en `test_sync_agent_client.py` (pipeline completo `completed` en orden fijo; orden independiente de claves; corto-circuito `skipped` + gate `completed`; nunca `failed`; resúmenes/truncado a 800; sin cache y fallo técnico → vacía). SC-US3-001..003 confirmados automáticamente.

**Deuda arrastrada:**

- **SC-US3-004 pendiente**: prueba funcional manual del usuario (enviar caso con `sync_http` y confirmar que "Traza de ejecución" muestra las etapas, incluido un caso de rechazo con etapas omitidas). SPEC-013 permanece en `draft` hasta ese OK, consistente con [[spec-cierre-requiere-prueba-funcional-manual]].
- **Shape real de los bloques de gate diferido**: la forma interna de `output_integridad/impacto/factibilidad/redactor_mail` sigue sin sondearse; el primer envío funcional (SC-US3-004) puede refinar la spec si aparece un marcador de "ejecutado" que valga la pena distinguir (mismo patrón con que se reconcilió el prefijo `output_` en US1).

**[SDD-Check] — 2026-07-03 (SPEC-013 US3)**
- Specs leídas: SPEC-013, SPEC-007-agent-trace, SPEC-010-batch-trace, SPEC-000-naming; CONSTITUTION.md, docs/ARCHITECTURE.md.
- Includes/excludes verificados: sin llamadas de red extra (traza desde lo cacheado en `send`); `get_thread_messages` sigue `[]`; sin variables de entorno ni dependencias nuevas; visor SPEC-007 sin cambios; síntesis agnóstica a la forma interna de los bloques.
- SSOTs afectados: `specs/SPEC-013-client-adapter-selection.md` (US3), `specs/SPECS_REGISTRY.md` (Iter), `src/adapters/sync_agent_client.py`, `tests/unit/test_sync_agent_client.py`, `historial/sdd.md`.

---

## 2026-07-03 — SPEC-013 User Story 2: trazabilidad del endpoint bajo test

**Scope: toca `src/` (adapters, domain, application, dashboard) + specs SSOT relacionadas + tests.** Se agregó una segunda User Story a SPEC-013 para hacer visible y auditable a qué URL/endpoint concreto se envían las pruebas de cada corrida, cerrando la brecha detectada al preguntar "¿desde runs a qué endpoint hice las pruebas?" (hoy sólo se infería del `agent_id`, que es una etiqueta, no la URL real).

**Decisiones tomadas:**

- **SPEC-013 migrada a estándar multi-HU** (`docs/SPEC-FORMAT.md`): la spec original pasa a **User Story 1** (FR-001..013 → FR-US1-001..013, SC → SC-US1-*, renumeración sin cambio de comportamiento) para admitir la nueva **User Story 2** sin perder la primera.
- **URL resuelta en `PlatformConfig`, no en los adaptadores** (FR-US2-001): property agnóstica `effective_endpoint_url` que reconstruye la URL según `client_type` (`remote_async` → `chat_url + agent_id + "/chat/completions"`; `sync_http` → `alt_client_url`). Ningún adaptador cambia su contrato ni su forma de armar el request: la property sólo **expone** hacia afuera un valor hoy encapsulado. El composition root lee la config, no le pregunta al cliente.
- **No duplicar SSOT**: el campo persistido se define en sus specs dueñas — `SuiteResult.endpoint_url` en [[SPEC-005-run-persistence]] (FR-002 + Key Entities) y la columna `endpoint_url` de `estadistica-corridas.csv` en [[SPEC-006-batch-suite]] (FR-US2-003/005). SPEC-013 US2 sólo **referencia y consume**, no redeclara esas estructuras. Ambas specs actualizadas con entrada de historial propia.
- **Retrocompatibilidad**: `from_dict` usa `data.get("endpoint_url", "")`; corridas persistidas antes del campo se leen con URL vacía sin romper el round-trip. La fila `TOTAL` del CSV deja la columna vacía (un agregado multi-corrida puede mezclar endpoints).
- **Separación domain/UI de SPEC-008 intacta**: la URL se imprime como `caption` en el caller del render (envío single-case, vista de última corrida y vista batch, siempre antes de la matriz), sin que `SuiteMetrics` conozca la URL.

**Verificación:** Pipeline local **VERDE 10/10** (279 tests). Tests nuevos: `effective_endpoint_url` por `client_type` (`test_platform_config.py`), round-trip + retrocompat de `endpoint_url` (`test_result.py`), columna en el CSV poblada/vacía (`test_file_run_repository.py`). SC-US2-001..003 confirmados automáticamente.

**Deuda arrastrada:**

- **SC-US2-004 pendiente**: prueba funcional manual del usuario (confirmar visualmente la URL en dashboard contra cada uno de los dos clientes). SPEC-013 permanece en `draft` hasta ese OK, consistente con [[spec-cierre-requiere-prueba-funcional-manual]] (el pipeline verde no cierra una spec).
- **Comentarios de código con IDs viejos**: la renumeración FR-001..013 → FR-US1-001..013 dejó referencias `SPEC-013 FR-00x` desactualizadas en comentarios de `sync_agent_client.py`, `platform_config.py`, `agent_client_factory.py`, `runner.py` y tests; no se tocaron en esta iteración (no afectan comportamiento). Candidato a barrido de reconciliación documental.

**[SDD-Check] — 2026-07-03 (SPEC-013 US2)**
- Specs leídas: SPEC-013, SPEC-005, SPEC-006, SPEC-008, SPEC-000-naming; CONSTITUTION.md, docs/ARCHITECTURE.md.
- Includes/excludes verificados: URL a nivel corrida (no por caso); dos clientes registrados (no un tercero); sin variables de entorno nuevas; adaptadores sin cambio de contrato.
- SSOTs afectados: `specs/SPEC-013-client-adapter-selection.md` (US2), `specs/SPEC-005-run-persistence.md` (`SuiteResult.endpoint_url`), `specs/SPEC-006-batch-suite.md` (columna CSV), `specs/SPECS_REGISTRY.md` (estado → draft), `src/adapters/platform_config.py`, `src/domain/result.py`, `src/adapters/file_run_repository.py`, `src/application/run_suite.py`, `src/runner.py`, `src/dashboard/app.py`, `historial/sdd.md`.

---

## 2026-07-01 — Auditoría de consistencia docs/specs (reconciliación documental)

**Scope: solo documentación y specs; no toca `src/` ni el producto.** Barrido de contradicciones, redundancias, violaciones de SSOT y simplificaciones sobre la constitución, los documentos de método y las 14 specs registradas. 7 hallazgos, todos resueltos.

**Bajo riesgo (sin decisión):**

- **SPEC-002**: "Expone tres métodos" → enunciado sin conteo frágil (el puerto documenta 4 + `get_trace`).
- **AGENTS.md**: la enumeración del pipeline omitía "trazabilidad SDD"; agregada (alinea con `docs/DEVELOPMENT.md` y `docs/SDD-ENFORCEMENT.md`).
- **SPEC-013**: FR-008/FR-009 estaban fuera de orden en Functional Requirements y en Coverage mapping; reordenados.
- **SPEC-000-naming**: un criterio citaba `_serializer` como excepción documentada inexistente en la tabla; removido.

**Reconciliación spec↔código (verificada contra `src/domain/ports.py`):**

- **Superficie del puerto `AgentClient` (#3)**: los 5 métodos reales estaban repartidos entre SPEC-002 (4) y SPEC-007 (`get_trace`) sin owner único. SPEC-002 §`domain/ports.py` pasa a ser SSOT de la interfaz (tabla método→owner).
- **Puerto `CredentialProvider` (#4)**: existe en el código (`ports.py:67`, implementado por `TokenProvider`) y SPEC-011/013 lo citaban como "puerto existente", pero **ninguna spec lo gobernaba** — gap de trazabilidad (Principio V). Registrado en SPEC-002. *Hallazgo corregido al leer el código: no era abstracción inventada sino puerto huérfano de spec.*
- **Redundancia de "Política de datos" (#7)**: `SPECS_REGISTRY.md` re-describía el mecanismo de carga ya SSOT en ADR-002; recortado a puntero + mapeo spec↔modo. PRODUCT.md ya enlazaba bien (sin cambios).

**Sin cambio de comportamiento:** reconciliación documental; las specs `active` afectadas (SPEC-002, SPEC-000-naming) siguen coherentes con el código vigente. No requiere spec nueva (no se toca `src/`).

**Deuda arrastrada:** la firma `send(form: dict)` (SPEC-002, vigente en código) sigue marcada para migrar a `send(input: AgentInput)` por SPEC-011 FR-014 / SPEC-013 FR-003 (drafts); reconciliación diferida a su implementación, ya registrada en esas specs.

**[SDD-Check] — 2026-07-01 (auditoría docs/specs)**
- Specs leídas: SPEC-002, SPEC-002b, SPEC-005, SPEC-007, SPEC-008, SPEC-011, SPEC-012, SPEC-013, SPEC-000-naming; CONSTITUTION.md, AGENTS.md, 00-INDEX.md, docs/{ARCHITECTURE,PRODUCT,DEVELOPMENT,CONTRIBUTING,SDD-ENFORCEMENT,SPEC-FORMAT}.md.
- Includes/excludes verificados: cambios acotados a docs/specs; verificada la superficie real del puerto contra `src/domain/ports.py` (no se editó `src/`).
- SSOTs afectados: `specs/SPEC-002-agent-client.md` (puerto `AgentClient` + `CredentialProvider`), `AGENTS.md`, `specs/SPEC-013`, `specs/SPEC-000-naming.md`, `specs/SPECS_REGISTRY.md`, `historial/sdd.md`.

---

## 2026-06-21 — Gate SDD cableado en opencode (cierra deuda #1 de la universalización)

**Scope cerrado (método/framework; no toca `src/` ni el producto). Toca el adaptador preventivo de opencode.**

Objetivo: cerrar la asimetría que dejó la universalización del SDD — Claude disparaba el gate en `PreToolUse`, opencode no tenía hook preventivo y dependía solo del `pre-commit`. Resuelve la **deuda arrastrada #1** de la entrada de universalización (plugin de opencode no implementado por no haber opencode en el entorno).

**Decisiones tomadas:**

- **Plugin `.opencode/plugin/sdd-gate.js`** que engancha `tool.execute.before`, filtra las tools `edit`/`write`, e invoca `tools/sdd_gate.py <filePath>` por **transporte argv** (el ya existente; `decide()` y el resto del gate intactos). Exit 2 → `throw` que aborta la edición y propaga el motivo. Paridad funcional con el `PreToolUse` de Claude.
- **`.js` sin imports de runtime** (solo `node:fs`/`node:path`, built-in de Bun). Razón: `.opencode/.gitignore` no versiona `node_modules`/`package.json`, así que el paquete `@opencode-ai/plugin` no existe en un clone limpio; un `import type` lo referenciaría innecesariamente. El plugin se versiona y corre sin `npm install`. Coherente con cómo el repo ya trata `.opencode/` (solo `command/*.md` versionados).
- **Sin gates nuevos.** El resto de checks (mypy, naming, import-linter, ruff) ya corren en la capa git/pre-commit (agnóstica) y protegen a opencode igual; los whole-repo (`check_constitution`, `check_traceability`, `schema_drift`) son de pipeline/CI, no encajan en un hook por-archivo. El único `PreToolUse` que Claude tenía y opencode no era `sdd_gate` — con esto quedan a la par.

**Verificación end-to-end (real, no solo unit):**

- Gate por argv: bloquea `src/` sin spec (exit 2), permite fuera de `src/` (exit 0).
- Sintaxis del plugin OK (`node --check`); `.opencode/plugin/` trackeado por git.
- **E2E en opencode real: OK** (intercepta y aborta la edición de `src/`).
- Pipeline local 9/9 verde (con `.venv/bin/python` en PATH).

**Sin cambio de comportamiento del producto:** solo método/adaptador. No requiere spec (el gate solo intercepta `src/`; este cambio no lo toca).

**Deuda arrastrada:** ninguna nueva. El pipeline (`tools/pipeline_local.sh`) asume `python` en PATH; en este entorno solo existe `.venv/bin/python` → requiere activar el venv. Detalle de entorno, no del cambio.

**[SDD-Check] — 2026-06-21 (gate en opencode)**
- Specs leídas: ninguna de producto (cambio de método); docs/SDD-ENFORCEMENT.md, AGENTS.md, tools/sdd_gate.py.
- Includes/excludes verificados: cambio acotado a método (no `src/`, no producto); plugin restringido a tools `edit`/`write` sobre `filePath`; reutiliza el transporte argv ya existente (mismo veredicto exit 0/2 que Claude y pre-commit).
- SSOTs afectados: enforcement (`.opencode/plugin/sdd-gate.js` nuevo, `tools/sdd_gate.py` docstring, `docs/SDD-ENFORCEMENT.md`), historial/sdd.md.

---

## 2026-06-21 — Universalización del SDD: agnóstico de asistente (Claude/opencode/…)

**Scope cerrado (método/framework; no toca `src/` ni el producto). Toca instrucciones del agente, capa semántica y gate de autoría.**

Objetivo: que el SDD funcione en cualquier asistente IA (ej. opencode), no solo Claude Code. Diagnóstico previo: la *verdad* (specs, checks deterministas, pipeline, `.sdd/current-spec`) ya era agnóstica; lo acoplado eran tres *adaptadores* — instrucciones, comandos y el hook preventivo. Se extrajeron los tres sin perder el cableado de Claude.

**Decisiones tomadas:**

- **#1 — `AGENTS.md` es ahora el SSOT del protocolo del agente** (antes solo apuntaba a `CLAUDE.md`). Se invirtió la dirección: el contenido vive en `AGENTS.md` (estándar de facto que auto-cargan opencode/Cursor/Codex/Aider/Gemini) y `CLAUDE.md` se reduce a `@AGENTS.md` (import nativo de Claude → contenido en contexto, cero salto). Asimetría que lo justifica: Claude puede importar `AGENTS.md`, pero ningún otro asistente puede importar `CLAUDE.md`. Referencias actualizadas en `00-INDEX.md`, `CONSTITUTION.md`, `docs/SPEC-FORMAT.md`, `specs/SPECS_REGISTRY.md`.
- **#3 — `analyze`/`clarify` portados a cuerpo neutro + wrappers finos.** El procedimiento (juicio LLM, no scriptificable) pasó a SSOT neutro en `docs/playbooks/{analyze,clarify}.md` (sin frontmatter ni `$ARGUMENTS`). Wrappers que solo aportan binding propietario: `.claude/skills/{analyze,clarify}/SKILL.md` (Claude, `clarify` liga `AskUserQuestion`) y `.opencode/command/{analyze,clarify}.md` (opencode). Se eliminaron `.claude/commands/{analyze,clarify}.md`. Decisión de diseño: las skills/commands **no** son estándar cross-asistente; la portabilidad viene de la *neutralidad del cuerpo*, no del tipo de wrapper.
- **#2 — `sdd_gate.py` multi-transporte + capa git, hook de Claude conservado (retro-compatible, a pedido del usuario).** `main()` acepta argv → env (`SDD_GATE_FILE`) → stdin JSON; `decide()` quedó intacta (ya era pura). Nuevo hook local `sdd-gate` en `.pre-commit-config.yaml` (transporte argv sobre `^src/` staged): lleva el enforcement preventivo a la capa git, el sustrato universal. El hook `PreToolUse` de Claude pasa de *garante* a *tripwire temprano opcional*. Contrato común exit 0/2 (sirve a Claude y a git).

**Verificación end-to-end (real, no solo unit):**

- pre-commit real (`pre-commit run sdd-gate`): bloquea sin spec, permite con spec declarada+editada, bloquea por mtime, bloquea por spec inexistente.
- Hook de Claude en vivo: `Write` a `src/streamlit.py` bloqueado (exit 2), archivo no creado.
- 8 tests del gate + pipeline local 9/9 verdes. Working tree sin cambios colaterales.

**Sin cambio de comportamiento del producto:** solo método. No requiere spec nueva (el gate solo intercepta `src/`; este cambio no lo toca).

**Deuda arrastrada:** (1) plugin de opencode para el gate (`tool.execute.before` → `sdd_gate.py`) no implementado — no había opencode en el entorno para verificarlo; el `pre-commit` ya cubre esa ruta. (2) Wrappers de opencode escritos contra la convención documentada (`.opencode/command/`), sin ejecutar para confirmar carga.

**[SDD-Check] — 2026-06-21 (universalización del SDD)**
- Specs leídas: SPECS_REGISTRY, CONSTITUTION.md, SPEC-000-naming, AGENTS.md (ex-CLAUDE.md), docs/SDD-ENFORCEMENT.md, docs/SPEC-FORMAT.md.
- Includes/excludes verificados: cambio acotado a método/framework (no `src/`, no producto); hook de Claude intacto; pre-commit `sdd-gate` restringido a `^src/`; los tres transportes del gate dan el mismo veredicto (exit 2 al bloquear).
- SSOTs afectados: protocolo del agente (`AGENTS.md`, `CLAUDE.md`→`@AGENTS.md`), capa semántica (`docs/playbooks/`, wrappers `.claude/skills/` y `.opencode/command/`), enforcement (`tools/sdd_gate.py`, `.pre-commit-config.yaml`, `docs/SDD-ENFORCEMENT.md`), `00-INDEX.md`, `CONSTITUTION.md`, `docs/SPEC-FORMAT.md`, `specs/SPECS_REGISTRY.md`, historial/sdd.md.

---

## 2026-06-16 — Aclaración de método: FR↔SC y cobertura no son 1 a 1

**Scope cerrado (método de redacción de specs; toca solo `docs/SPEC-FORMAT.md`):**

A raíz de la pregunta «¿FR y SC son 1 a 1?», se explicitó en el SSOT del formato lo que estaba implícito en las specs (p. ej. SPEC-008: 8 FR / 3 SC) pero no escrito en la guía:

- **Sección SC**: FR y SC operan en ejes distintos (qué se construye vs. qué valor observable); muchos FR, pocos SC; un FR interno puede no tener SC.
- **Sección Coverage mapping**: una entrada del mapping no es «un test por requisito» — relación requisito↔verificador es N:M; FR de consistencia documental o UI se verifican por revisión/verificación visual, no con `pytest`.

**Sin cambio de comportamiento ni de specs existentes:** solo documentación del método; no requiere tests. Análisis conceptual de origen vive en el repo `analisis/SDD/` (Línea B).

**Deuda arrastrada:** ninguna.

---

## 2026-06-14 — Saldo de deuda de git/triggers: hooks acotados + CI de GitHub Actions

**Scope cerrado (tooling de validación; toca `.pre-commit-config.yaml`, `.github/`, `docs/`, spec de bootstrap):**

SPEC-000-bootstrap arrastraba desde Iter 0 un único criterio pendiente — `pre-commit run --all-files` en verde, bloqueado por «requiere git init». El repo ya está bajo git, así que se saldó la deuda y, de paso, se ordenó el reparto de validaciones por trigger.

**Decisiones tomadas:**

- **Hooks de commit acotados a `^src/`** (ruff, mypy, naming, capas): no corren sobre cambios de docs/specs.
- **`pytest` retirado del trigger `pre-push`** (era el único hook de push; no aportaba sobre el reparto vigente, a pedido del usuario). El hook de git `pre-push` quedó desinstalado. Los tests viven en el pipeline local y en CI.
- **Hooks locales `naming`/`import-linter` migrados de `language: system` a `language: python`** (auto-contenidos): antes fallaban fuera del venv porque el sistema no tiene `python`/`lint-imports` en PATH. Verificado `pre-commit run --all-files` verde desde entorno limpio.
- **CI de GitHub Actions** (`.github/workflows/ci.yml`): valida el código (ruff, mypy, naming, capas, bandit, pytest unit) ante `push` a `main` o PR que toque `src/`/`tests/`/`tools/`/manifiestos. Filtrado por paths: cambios solo de `docs/`/`specs/`/`historial/` no lo disparan (decisión del usuario). No incluye los gates de gobernanza documental (constitución, trazabilidad), que siguen solo en el pipeline local.
- **Actualización del bump de tooling** (commit previo del día): ruff v0.6.9→v0.15.14, mypy v1.11.2→v2.1.0; deps de mypy `python-dotenv`/`streamlit`.

**SSOT del reparto commit/push/pipeline/CI:** `docs/DEVELOPMENT.md` §«Cuándo correr qué» (actualizado). SPEC-000-bootstrap referencia ese SSOT y marca sus criterios como cumplidos.

**Sin cambio de comportamiento del producto:** solo tooling/CI. Pendiente operativo (no de spec): activar branch protection en GitHub para que el check `checks` sea obligatorio, y `git push` para la primera corrida.

**Deuda arrastrada:** ninguna nueva; saldada la de Iter 0.

**[SDD-Check] — 2026-06-14 (git/triggers + CI)**
- Specs leídas: SPEC-000-bootstrap, SPEC-000-naming, SPECS_REGISTRY, CONSTITUTION.md, CLAUDE.md.
- Includes/excludes verificados: CI y hooks de commit restringidos a paths de código (`^src/`, etc.); gobernanza documental excluida de CI (solo pipeline local); `pre-commit run --all-files` verde desde entorno limpio.
- SSOTs afectados: SPEC-000-bootstrap (tooling, config, criterios, notas), `docs/DEVELOPMENT.md` (§Comandos clave, §Cuándo correr qué), `.pre-commit-config.yaml`, `.github/workflows/ci.yml`, historial/sdd.md.

---

## 2026-06-14 — Simplificación editorial de SPEC-011 y SPEC-012 (sin cambio de comportamiento)

**Scope cerrado (solo documentación de spec; sin tocar `src/` ni tests):**

SPEC-011 y SPEC-012 acumulaban redundancia: cada decisión aparecía repetida hasta en cinco lugares (Clarifications Q&A → FR → Key Entities → Coverage → Historial), más material transitorio ya cumplido. Se simplificaron sin perder funcionalidad, estilo ni calidad, a pedido del usuario.

**Decisiones tomadas (método elegido por el usuario vía AskUserQuestion):**

- **Clarifications condensadas in situ** en ambas specs: cada Q&A queda como pregunta + decisión en 1-2 líneas con puntero al FR que la implementa, eliminando los tails de "Consecuencia/rationale" que ya viven en los FR. La sección sigue apta para futuros `/clarify`.
- **Historial comprimido** en ambas specs: SPEC-011 5→3 entradas, SPEC-012 ~10→5 entradas; se conservan todas las fechas/decisiones netas, se quita la narrativa de proceso que duplicaba Clarifications/FR.
- **SPEC-011 Key Entities** reducidas a punteros de sus FR (sin re-explicar el rationale de `AgentInput`/`EvaluatedResult`/registro puro, ya normado en FR-002/011/014/015).
- **SPEC-012:** retirada la «Nota de mapeo» FR-NNN→FR-USn (transitoria; la reorganización ya está cerrada y las Clarifications citan los FR-USn vigentes).

**Sin cambio de comportamiento ni decisión nueva:** no se tocó contenido normativo de los FR, Acceptance Scenarios, Success Criteria, Coverage ni la sección «Referencia: cuestionario de origen». Las specs siguen en estado `draft`.

**Deuda arrastrada:** ninguna nueva.

**[SDD-Check] — 2026-06-14 (simplificación editorial)**
- Specs leídas: SPEC-011-agent-under-test, SPEC-012-translation-evaluator, CONSTITUTION.md, SPECS_REGISTRY.md, CLAUDE.md.
- Includes/excludes verificados: sin cambios en `src/` ni tests; sin referencias colgadas a la «Nota de mapeo» ni a FR-NNN viejos en el cuerpo normativo (solo en Historial, intencional); contenido normativo (FR/Acceptance/SC/Coverage) intacto.
- SSOTs afectados: SPEC-011 (Clarifications, Key Entities, Historial), SPEC-012 (Clarifications, Historial), historial/sdd.md.

---

## 2026-06-13 — Reorganización de SPEC-012 en 3 User Stories (sin cambio de comportamiento)

**Scope cerrado (solo documentación de spec; sin tocar `src/` ni tests):**

SPEC-012-translation-evaluator tenía 15 FR colgando de una sola User Story P1, lo que la volvía difícil de leer y de priorizar. A pedido del usuario se dividió en **tres slices verticales** independientemente entregables y testeables, siguiendo el molde de SPEC-006:

- **US1 — Evaluador determinista (P1):** núcleo puro `domain/` (modelo de caso, extracción/shape, taxonomías exactas, completitud, predicado vacío, garantía constitucional). FR-US1-001..008.
- **US2 — Caso en circuito (P2):** constructor `build/`, carga por archivo, persistencia/render por el circuito del clasificador. FR-US2-001..004.
- **US3 — Similaridad informativa y entrada por pantalla (P3):** fuzzy informativa + entrada por pantalla. FR-US3-001..003.

**Decisiones tomadas:**

- **Sin cambio de comportamiento ni decisión nueva del usuario:** es una reorganización de redacción/estructura. Toda la semántica decidida en las sesiones de `/clarify` (2026-06-09/12/13) se conserva.
- **FR renombrados a `FR-USn-xxx`** y reducidos de 15 → 13: FR-001+FR-014 fusionados en FR-US1-001 (el `form_esperado` y sus tres derivaciones en un solo FR); FR-008 reexpresado como garantía constitucional FR-US1-007; FR-011 (naming) replicado como último FR de cada US (patrón de SPEC-006).
- **Trazabilidad del audit trail preservada:** se agregó una nota de mapeo FR-viejo→FR-nuevo al inicio de Clarifications, de modo que las Q/A previas (que citan FR-001..FR-015) siguen siendo legibles sin reescribir el histórico de decisiones.
- Cada User Story redactada en formato «Como… quiero… **para** \<valor\>», en **afirmativo** (nombra el valor esperado, no lo que se evita), a pedido explícito del usuario.
- Se conservan a nivel spec: Clarifications, «Referencia: cuestionario de origen», Assumptions generales y Fuera de alcance.

**Deuda arrastrada:** ninguna nueva. SPEC-012 sigue en `draft`; `tests/unit/test_translation_evaluator.py` sigue *planificado* (se crea al implementar), igual que antes de esta reorg.

**SSOTs afectados:** `specs/SPEC-012-translation-evaluator.md`, `specs/SPECS_REGISTRY.md` (estado anotado `12 rev.2026-06-13 (3 US)`), `historial/sdd.md`.

**[SDD-Check] — 2026-06-13**
- Specs leídas: SPEC-012-translation-evaluator (reorg), SPEC-006-batch-suite (molde de 3 US)
- Includes/excludes verificados: 8 FR en US1, 4 en US2, 3 en US3; los 8 Acceptance y 6 SC originales repartidos por US; naming replicado por US
- SSOTs afectados: SPEC-012, SPECS_REGISTRY, sdd.md
- Verificación: `check_traceability.py specs` → OK (16 specs)

---

## 2026-06-13 — Enmienda Principio III: invariante de evaluación agnóstico a evaluadores futuros → 0.5.2

**Scope cerrado (constitución, texto del Principio III + SSOT ADR-003; sin tooling):**

Reescrito el invariante del Principio III ("Evaluación determinista"). Antes estaba redactado en términos del único evaluador existente: hablaba de "comparación exacta contra la **clasificación** esperada", de "el regex" como mecanismo único, y su Enforcement listaba un test concreto (`tests/unit/test_classification_evaluator.py`). Al habilitarse un segundo evaluador (traducción, SPEC-012) la letra quedó angosta: cada evaluador nuevo obligaría a reenmendar la constitución. La nueva redacción declara el invariante estable —veredicto por extracción + comparación determinista y exacta contra **el esperado del caso**; ningún evaluador usa LLM-as-judge ni variantes equivalentes; métricas auxiliares informan pero no graduan— y delega la **enumeración de evaluadores concretos** al SSOT (`docs/ARCHITECTURE.md`, ADR-003).

**Decisiones tomadas:**

- **PATCH (0.5.1 → 0.5.2), no MINOR:** el invariante no cambia (evaluación determinista, sin LLM-as-judge, sin variantes equivalentes); solo se quita el detalle operativo (clasificación/regex/un test) que lo hacía envejecer. Mismo patrón que la enmienda del Principio II del 2026-06-08. Coherente con el Preámbulo: "la constitución nunca duplica ese detalle".
- **Enforcement agnóstico:** pasa de un test puntual a "suite de tests de los evaluadores en `tests/unit/`". El validador `check_constitution.py` solo exige que el path exista (lo hace); ningún evaluador concreto se nombra en la constitución.
- **ADR-003 promovido a SSOT enumerativo:** generalizado de "extracción regex + match exacto" a "evaluación determinista por extracción + match exacto", con una tabla de evaluadores (clasificación SPEC-003 ya implementada; traducción SPEC-012 en draft, test planificado). Agregar un evaluador = agregar una fila, no enmendar la constitución. Disparador: preocupación del usuario de no tener que listar cada evaluador futuro en la constitución.
- SPEC-012 **no introduce conflicto constitucional**: respeta el invariante (veredicto 100% determinista; similaridad fuzzy informativa, no graduante). La enmienda solo corrige la letra que se había quedado corta.

**Deuda arrastrada:** `tests/unit/test_translation_evaluator.py` está referenciado en ADR-003 como *planificado* (SPEC-012 en draft); se crea al implementar la spec. No es deuda de cobertura: SPEC-012 no está `active`, así que `check_traceability` no exige el test todavía.

**SSOTs afectados:** `CONSTITUTION.md`, `docs/ARCHITECTURE.md` (ADR-003), `historial/sdd.md`.

**[SDD-Check] — 2026-06-13**
- Specs leídas: CONSTITUTION.md (Principio III), docs/ARCHITECTURE.md (ADR-003), specs/SPEC-012-translation-evaluator.md
- Includes/excludes verificados: cambio de framework SDD (gobernanza, no producto); sin SPEC-NNN nueva
- SSOTs afectados: CONSTITUTION.md, docs/ARCHITECTURE.md, historial/sdd.md
- Verificación: check_constitution.py verde (5 principios activos)

---

## 2026-06-08 — Enmienda Principio II: invariante desacoplado de la enumeración de capas → 0.5.1

**Scope cerrado (constitución, texto del Principio II; sin tooling):**

Reescrito el invariante del Principio II ("Capas limpias con dependencia unidireccional"). Antes enumeraba capas concretas (`domain/` no importa de `adapters/` ni de `dashboard/`); esa enumeración quedó stale al aparecer la capa `application/` (use-cases, ADR-005), que el principio nunca mencionó. La nueva redacción declara el invariante estable —núcleo puro en `domain/` sin dependencias hacia ninguna capa, dependencias unidireccionales hacia el dominio, proveedores concretos detrás de puertos en `adapters/`— y delega la enumeración de capas y la matriz de dependencias al SSOT (`docs/ARCHITECTURE.md`).

**Decisiones tomadas:**

- **PATCH (0.5.0 → 0.5.1), no MINOR:** el invariante no cambia (capas limpias + dependencia unidireccional hacia un dominio puro); solo se quita el detalle operativo duplicado que lo hacía envejecer. Coherente con el Preámbulo: "la constitución nunca duplica ese detalle".
- La capa `application/` ahora queda cubierta sin nombrarla: es "una capa" que apunta hacia el dominio. Futuros reordenamientos de capas no requerirán reenmendar la constitución.
- `docs/ARCHITECTURE.md` (regla de oro, ADR-005) ya contenía la matriz completa y correcta: se mantiene como SSOT, sin cambios.

**Deuda arrastrada:** ninguna.

**SSOTs afectados:** `CONSTITUTION.md`, `historial/sdd.md`.

**[SDD-Check] — 2026-06-08**
- Specs leídas: CONSTITUTION.md (Principio II), docs/ARCHITECTURE.md (regla de oro, ADR-005)
- Includes/excludes verificados: cambio de framework SDD (gobernanza, no producto); sin SPEC-NNN nueva
- SSOTs afectados: CONSTITUTION.md, historial/sdd.md
- Verificación: check_constitution.py verde (5 principios activos)

---

## 2026-06-06 — Enmienda Principio V (Fase 2): enforcement ejecutable spec-first → 0.5.0

**Scope cerrado (framework SDD; no es cambio de producto, no lleva SPEC-NNN):**

Construido el enforcement de tres capas para el Principio V (vía B de la decisión `analisis/SDD/software/DECISION-ADOPTAR-VS-PORTAR-SPECKIT.md`):

- **`tools/check_traceability.py`** (nuevo, molde de `check_naming.py`): gate determinista del pipeline. Valida (1) estructura de specs híbridas SPEC-004+ (User Story+prioridad, FR-NNN, SC-NNN, Coverage mapping); (2) consistencia spec↔`SPECS_REGISTRY.md` (sin huérfanas ni entradas colgadas, estado válido); (3) cobertura FR→test en specs `active` (todo FR en el Coverage mapping + paths `tests/...py` referenciados existen). Cableado: agregado a `PIPELINE_TOOLS` en `check_constitution.py` + step "trazabilidad SDD" en `pipeline_local.sh` + permiso en `.claude/settings.local.json`. Tests: `tests/unit/test_check_traceability.py` (8).
- **`tools/sdd_gate.py`** (nuevo): interlock de autoría, hook `PreToolUse` (`.claude/settings.json`, matcher `Edit|Write`). Bloquea edición de `src/` si no hay una SPEC válida declarada en `.sdd/current-spec`. Es la única capa anterior a que el código exista (sin git no hay pre-commit). Tests: `tests/unit/test_sdd_gate.py` (6). Verificado a mano: bloquea `src/` sin declaración (exit 2), permite fuera de `src/` (exit 0).
- **Skills `/clarify` y `/analyze`** (`.claude/commands/`): capa semántica adaptada de Spec Kit a la estructura `SPEC-NNN`. `/analyze` read-only (gaps de adecuación, FR sin test real, conflictos con principios); `/clarify` ≤5 preguntas que se graban en la spec.
- **`docs/SDD-ENFORCEMENT.md`** (nuevo): SSOT del método de enforcement (tres capas, ciclo `.sdd/current-spec`, límite presencia vs. adecuación).
- **`CONSTITUTION.md`**: `Enforcement:` del Principio V repuntado de `docs/SPEC-FORMAT.md` a `tools/check_traceability.py` + `tools/sdd_gate.py`; `Detalle:` += `docs/SDD-ENFORCEMENT.md`. Versión `0.4.0 → 0.5.0`. El Principio V queda a la par de I/II/III (enforcement ejecutable).

**Decisiones tomadas:**

- El gate verifica *presencia* de spec, no *adecuación*: el juicio de "¿requisito nuevo sin FR?" queda en `/analyze`//`/clarify` y revisión humana (documentado en `SDD-ENFORCEMENT.md`).
- Bifásico respetado: el repunte de `Enforcement:` se hizo recién ahora porque `check_constitution.py` exige que los archivos referenciados existan; antes habría roto el gate de integridad.
- El check afloró un gap real al habilitarse: SPEC-007 declaraba FR-012 sin fila en su Coverage mapping (feature implementada, tabla incompleta) → reconciliado.

**Deuda arrastrada:** FR→test estricto (celdas del Coverage mapping con IDs de nodo de test) requiere endurecer `docs/SPEC-FORMAT.md` y migrar tablas — diferido (ver `SDD-ENFORCEMENT.md`). `git init` habilitaría backstop `pre-commit` además del hook (que solo cubre la ruta del asistente).

**SSOTs afectados:** `CONSTITUTION.md`, `tools/check_traceability.py`, `tools/sdd_gate.py`, `tools/check_constitution.py`, `tools/pipeline_local.sh`, `docs/SDD-ENFORCEMENT.md`, `specs/SPEC-007-agent-trace.md`, `.claude/settings.json`, `.claude/settings.local.json`, `.claude/commands/`, `.sdd/current-spec`, `tests/unit/`, `historial/sdd.md`.

**[SDD-Check] — 2026-06-06**
- Specs leídas: CONSTITUTION.md (Principio V), docs/SPEC-FORMAT.md, docs/SDD-ENFORCEMENT.md
- Includes/excludes verificados: cambio de framework (no producto); sin SPEC-NNN nueva
- SSOTs afectados: ver lista arriba
- Verificación: check_constitution.py verde; pipeline_local.sh verde (9/9 pasos); 226 tests

---

## 2026-06-06 — Enmienda Principio V (Fase 1, texto): admisión + distinción producto/framework → 0.4.0

**Scope cerrado (constitución, texto del Principio V; sin tooling todavía):**

- `CONSTITUTION.md` Principio V (Trazabilidad spec↔código): se fortalece el invariante con dos cláusulas nuevas, sin cambiar el invariante base ("spec antes que código"):
  - **Admisión**: "Un cambio de comportamiento sin spec vigente que lo gobierne no se integra" — convierte la trazabilidad en regla de admisión, no solo aspiración.
  - **Distinción producto/framework**: los cambios al propio método/framework SDD (gobernanza, enforcement, formato de spec) no se describen con specs de producto; se rigen por la constitución y los documentos de método en `docs/`. Registra formalmente que un cambio de framework NO va como `SPEC-NNN`.
- Versión `0.3.0 → 0.4.0` (sube `y`: agrega cláusulas normativas a una sección, no es mera aclaración).

**Decisiones tomadas:**

- **Fase 1 solo texto.** El `Enforcement:` del Principio V sigue apuntando a `docs/SPEC-FORMAT.md` (existe), no al check/hook todavía. Razón: `check_constitution.py` exige que el `Enforcement:` referencie un archivo existente y cableado; repuntarlo a `tools/check_traceability.py` + hook `PreToolUse` antes de construirlos rompería el gate. La Fase 2 (repunte de enforcement) se hará al existir el tooling.
- SSOTs referenciados revisados (procedimiento de enmienda): `docs/SPEC-FORMAT.md` se autodefine como "SSOT del método de redacción de specs" (de producto) y `specs/SPECS_REGISTRY.md` lista specs de producto; ninguno contradice la nueva distinción producto/framework — la clarifica.

**Deuda arrastrada:** Fase 2 del Principio V (repunte de `Enforcement:` al check + hook) pendiente de construir `tools/check_traceability.py`, el hook `PreToolUse` y el doc de método `docs/SDD-ENFORCEMENT.md`; será otro bump cuando existan.

**SSOTs afectados:** `CONSTITUTION.md`, `historial/sdd.md`.

**[SDD-Check] — 2026-06-06**
- Specs leídas: CONSTITUTION.md (Principio V + Governance), docs/SPEC-FORMAT.md (SSOT referenciado)
- Includes/excludes verificados: solo texto del Principio V; invariante base sin cambio; Enforcement sin repuntar (Fase 1)
- SSOTs afectados: CONSTITUTION.md, historial/sdd.md
- Verificación: check_constitution.py verde tras la enmienda; SSOTs referenciados por el principio revisados y consistentes

---

## 2026-06-06 — Gobernanza: re-baseline de versión a serie pre-1.0 (0.x)

**Scope cerrado (constitución / política de versionado, sin cambio de principios):**

- `CONSTITUTION.md`: la versión se corrige de `1.0.0` a `0.3.0`. El `1.0.0` original implicaba una madurez que el sistema no tiene; se adopta serie pre-1.0.
- `CONSTITUTION.md` §Governance: se agrega el bullet **"Fase pre-1.0"** sin remover la definición de `MAJOR/MINOR/PATCH` (se conserva y se le mapea encima): mientras dure la fase pre-madura, lo que tras `1.0.0` sería MAJOR o MINOR sube `y` (`0.y.0`); lo que sería PATCH sube `z`. Todo artefacto versionado nuevo MUST iniciar en `0.1.0`. MUST NOT declararse `1.0.0` hasta madurez sostenida.

**Decisiones tomadas:**

- Re-baseline, no bump: no se "sube" de 1.0.0; se reconoce que el estado actual equivale a `0.3.0` (pre-madurez con varias iteraciones acumuladas). Las futuras enmiendas parten de ahí (`0.4.0`, etc.).
- Verificación de alcance: el único artefacto de madurez en `1.0` era `CONSTITUTION.md`. `pyproject.toml` ya estaba en `0.0.1`. El resto de coincidencias de "versión" en el repo son prosa ("datos no versionados", "schema versionado", "comparar versiones del agente"), no números de madurez.
- El registro histórico previo (`historial/sdd.md`, entrada de creación de la constitución que dice "Versión inicial 1.0.0") **no se reescribe**: es log factual; esta entrada documenta la corrección.

**Deuda arrastrada:** la enmienda al Principio V (trazabilidad: admisión "sin spec no se integra" + distinción producto/framework, y repunte de `Enforcement:` al check/hook) sigue pendiente; se hará en bumps posteriores (`0.4.0` texto, y el repunte de enforcement recién cuando exista el tooling, por el gate de integridad de `check_constitution.py`).

**SSOTs afectados:** `CONSTITUTION.md`, `historial/sdd.md`.

**[SDD-Check] — 2026-06-06**
- Specs leídas: CONSTITUTION.md (Governance), no aplica spec de producto (cambio de framework, no de producto)
- Includes/excludes verificados: solo versión + política de versionado; principios I–V sin cambio de invariante
- SSOTs afectados: CONSTITUTION.md, historial/sdd.md
- Verificación: búsqueda de marcadores `1.0` en el repo — único artefacto de madurez afectado era la constitución

---

## 2026-06-05 — Fix: el display batch no se limpiaba al subir un archivo distinto (SPEC-006 FR-US1)

**Scope cerrado (solo dashboard, sin cambio de spec):**

- `src/dashboard/app.py`: al subir un archivo batch distinto al anterior, el dashboard ahora descarta el resultado batch previo en pantalla **y** todo estado de una corrida en curso del archivo viejo. Antes solo borraba `batch_result`, dejando que una corrida `batch_phase == "running"` siguiera ejecutando los `batch_pending` del archivo anterior bajo el archivo nuevo.
- La detección de "archivo distinto" pasó de la clave frágil `nombre:tamaño` al **hash sha256 del contenido**: dos archivos con igual nombre y tamaño pero distinto contenido ahora cuentan como distintos.
- Extraído el helper puro `_clear_batch_run_state(state)` (más la constante `_BATCH_RUN_KEYS`), reutilizado por `_reset_case` para eliminar la lista de claves duplicada.
- Test nuevo `tests/unit/test_dashboard_batch_reset.py`: el helper limpia resultado + corrida en curso, no toca `batch_file_key` ni estado ajeno, y es idempotente sin estado.

**Decisiones tomadas:**

- El parámetro `state` del helper se tipa `Any` (no `MutableMapping`/`Protocol`): el estado de sesión de la interfaz (`SessionStateProxy`) usa firmas sobrecargadas/posicionales que no encajan en un Protocol mínimo, y acoplar el helper a ese tipo violaría la agnosticidad de UI (SPEC-000). El `dict` de los tests cubre el contrato real (get/pop/setitem).
- No se modifica SPEC-006: el MUST de FR-US1 ("al subir un archivo distinto al anterior, el dashboard descarta el resultado batch previo en pantalla, no mezcla corridas de archivos diferentes") ya describía el comportamiento; esto es endurecimiento de implementación para cumplirlo de verdad.

**Deuda arrastrada:** ninguna nueva. La lógica de detección de cambio de archivo sigue inline en `_render_batch` (no testeable sin fakear widgets); el helper de limpieza, que es la parte con riesgo, sí quedó cubierto.

**SSOTs afectados:** `src/dashboard/app.py`, `tests/unit/test_dashboard_batch_reset.py`, `historial/sdd.md`.

**[SDD-Check] — 2026-06-05**

- Specs leídas: CLAUDE.md, SPECS_REGISTRY, SPEC-006-batch-suite (FR-US1 MUST línea 31), SPEC-000-naming.
- Includes/excludes verificados: **incluido** el descarte de resultado batch + corrida en curso al cambiar de archivo y la detección por hash de contenido; **excluido** cualquier cambio de spec (el MUST ya existía) y test de la rama inline de `_render_batch` (requiere fakear widgets de UI).
- SSOTs afectados: ver lista arriba.
- Pipeline local: VERDE 8/8 (constitución, lint, format, mypy, naming, capas, bandit, pytest unit — 211 tests).

---

## 2026-06-04 — SPEC-011 + SPEC-012 creadas (draft): agente bajo prueba seleccionable + evaluador de traducción

**Scope (specs, sin código todavía):**

- Verificada la existencia del agente `traductor_intents` (id `3da38f33-3788-44c2-b326-fdbf3cd0605c`) en la instancia vía `tools/connection_check.py --list-agents`. Inspeccionado su contrato (`description`/`instructions`): es el **inverso** del clasificador — entra texto natural, sale el `{form}` de `schemas/FI_Orquestador_Input.schema.json`, con `tipo_intent` mutuamente excluyente, `datos_requeridos` inferido y prohibición de inventar campos.
- `SPEC-011-agent-under-test` (draft): concepto de **perfil de agente bajo prueba** = `(profile_id, agent_id, constructor de entrada, evaluador)`. Registro de 2 perfiles (clasificador actual + traductor), selección por `.env` con default al clasificador (compatibilidad), argumento CLI opcional con precedencia, puerto `Evaluator` común en `domain/ports.py`. Diseño extensible.
- `SPEC-012-translation-evaluator` (draft): caso de traducción (textos de entrada + form esperado), `TranslationEvaluator` puro en `domain/`, constructor de entrada de texto natural en `build/`. Veredicto determinista = taxonomías exactas + completitud poblado/vacío condicionada al esperado; extracción del `{form}` (sin form → indeterminado, no fail).
- `SPECS_REGISTRY.md`: alta de SPEC-011 y SPEC-012 como `draft`.

**Decisiones tomadas:**

- **Selección de agente por `.env`**, default al perfil clasificador para no romper setups existentes; cada perfil resuelve su propio `agent_id` (clasificador conserva `AGENT_ID`).
- **Opción A para el fuzzy** (decisión de gobernanza del usuario): la similaridad fuzzy de `nombre_iniciativa`/nombre del intent se calcula pero es **informativa**, NO graduante. El veredicto pass/fail usa solo lo 100% determinista (taxonomías + completitud). Así **no se toca la Constitución**: el Principio III (match exacto, sin variantes equivalentes, sin LLM-judge) queda intacto. La Opción B (fuzzy graduante) exigiría enmienda formal del Principio III y queda fuera salvo decisión posterior.
- El registro de perfiles vive en una **capa de composición** (no en `domain/`, que no importa de `build/` ni `adapters/`), porque la terna compone una pieza de `build/` con una de `domain/`.

**Deuda arrastrada / `[NEEDS CLARIFICATION]` a resolver al implementar:**

- SPEC-011: nombres exactos de las variables de entorno (selección de perfil y `agent_id` del traductor); si el dashboard ofrece selector interactivo además de reflejar el `.env`.
- SPEC-012: cuáles son exactamente los 5 campos de texto de entrada del caso de traducción; fuente del form esperado de ground truth; algoritmo de similaridad fuzzy y su umbral de reporte.
- Extensión de la matriz de confusión ([[SPEC-008]]) al contrato de traducción: trabajo futuro, no de SPEC-012.

**SSOTs afectados:** `specs/SPEC-011-agent-under-test.md` (nueva), `specs/SPEC-012-translation-evaluator.md` (nueva), `specs/SPECS_REGISTRY.md`, `historial/sdd.md`.

**[SDD-Check] — 2026-06-04 (creación de specs)**

- Specs leídas: CONSTITUTION, 00-INDEX, SPECS_REGISTRY, AGENT-INVOCATION, SPEC-FORMAT, SPEC-000-naming, SPEC-002, SPEC-002b, SPEC-003, SPEC-008 (referencia de formato), test_case.py, ports.py.
- Includes/excludes verificados: selección de agente (SPEC-011) y evaluador de traducción (SPEC-012) **incluidos como draft sin código**; implementación, persistencia/render del traductor y extensión de métricas **excluidos**; Opción B (fuzzy graduante / enmienda constitucional) **excluida**.
- SSOTs afectados: ver lista arriba.

---

## 2026-06-04 — Corrección de `schemas/FI_Orquestador_Input.schema.json` (descripciones corridas)

**Scope cerrado:**

- Verificación de **identidad** entre el schema que el agente `traductor_intents` tiene embebido en sus `instructions` (su "Formato del JSON OBLIGATORIO") y `schemas/FI_Orquestador_Input.schema.json`. Comparación **estática del comportamiento del agente** (lectura de su configuración vía `/agents`), **sin ejecutarlo**.
- Resultado: estructura idéntica (12 claves del `form`, mismos tipos, mismos defaults, taxonomías `tipo_intent` y `datos_requeridos` iguales). Única divergencia: dos `description` mal asignadas en **nuestro** archivo (bug de copy/paste), no en el agente:
  - `metricas_de_exito.description` estaba `""` → corregido a `"Indicadores medibles que definen si el intent funcionó."`
  - `nombre_iniciativa.description` tenía la descripción de métricas → corregido a `"Nombre descriptivo de la iniciativa."`
- Tras la corrección, la comparación da **identidad exacta** (incluidas descripciones y defaults).

**Decisiones tomadas:**

- Se toma como autoritativa la versión del **agente** (coherente) y se alinea nuestro schema a ella. Las `description` no afectan la evaluación (que mira claves/tipos/valores), pero el schema es un contrato versionado (ADR del schema en `00-INDEX`/`docs`), así que se mantiene fiel al agente real.

**Herramienta agregada:**

- `tools/schema_drift_check.py` (nueva, naming verde): verifica de forma **estática** (sin ejecutar el agente) el drift de contrato entre el bloque de formato declarado en las `instructions` de un agente y un schema local versionado. Parametrizable (`--agent-name`, `--schema`, `--marker`, `--dump`); exit codes 0=sin drift, 1=drift, 2=error. Formaliza el probe temporal que se usó para esta verificación. Volcado opcional (gitignored) en `runs/agent-format-block.json`.

**SSOTs afectados:** `schemas/FI_Orquestador_Input.schema.json`, `tools/schema_drift_check.py`, `historial/sdd.md`.

---

## 2026-06-04 — Nota de deuda: `connection_check.py` mezcla JSON y logs en stdout

**Deuda arrastrada (tooling, no bloqueante):**

- `tools/connection_check.py` con `--list-agents --raw` imprime el JSON de los agentes y, a continuación, líneas de estado (`[info] AGENT_ID ...`, `[ok] ... presente en la lista`) **en el mismo stdout** (ver `_list_and_verify_agents`, `tools/connection_check.py:109-145`). Eso hace que el output **no sea pipeable** a un parser: `... --raw | jq` / `| python -c "json.loads(...)"` falla con `Expecting value` al toparse con el texto no-JSON tras el array.
- **Mejora propuesta:** emitir el JSON crudo a `stdout` y mover los mensajes `[info]/[ok]/[..]` a `stderr`, de modo que `python tools/connection_check.py --only-list --list-agents --raw 2>/dev/null | jq` funcione directo. Workaround actual: consultar `cfg.agents_url` con `requests` desde un script propio en vez de parsear el stdout de la utilidad.
- Detectada mientras se verificaba la existencia del agente `traductor_intents` (id `3da38f33-3788-44c2-b326-fdbf3cd0605c`) de cara a SPEC-011/SPEC-012 (selección de agente bajo prueba + evaluador de traducción), aún sin abrir.

---

## 2026-06-01 — SPEC-006 US3: parada manual de la corrida batch

**Scope cerrado:**

- Forma estándar de frenar una corrida batch y quedarse con los casos completados (sin el caso en vuelo ni los pendientes), en headless y dashboard, con finalización y persistencia compartidas.
- `src/runner.py`: `run_batch` corta ante `KeyboardInterrupt` (Ctrl+C) con `break`, descartando el caso en vuelo y devolviendo lo acumulado; `main` detecta la corrida parcial, informa K/N por consola y no persiste un run vacío. `_execution_failure` → `execution_failure` (pública, reutilizada por el dashboard).
- `src/dashboard/app.py`: ejecución batch reescrita como interrumpible — `@ui.fragment(run_every=0.4)` ejecuta un caso por tick cediendo el control entre casos; botón "Frenar y guardar lo hecho"; `_finalize_batch` arma el `SuiteResult` con lo completado y persiste (misma ruta que headless); nota de parada manual y guarda de corrida vacía en `_render_batch_result`.
- `tests/unit/test_runner.py`: stub con `interrupt_on_send_call`; tests de descarte del caso en vuelo y de persistencia/round-trip del run parcial.

**Decisiones tomadas:**

- Mecanismo "std": Ctrl+C (SIGINT) en headless; botón "Frenar" en dashboard.
- Caso en vuelo **excluido** (no se inventa un Indeterminado).
- Dashboard interrumpible vía `fragment` (no threads): Streamlit 1.57 lo soporta; evita las asperezas de `session_state` desde hilos.
- Diferencia de granularidad aceptada y documentada: headless aborta el caso en vuelo; el dashboard termina el caso actual y frena antes del siguiente (Streamlit no interrumpe un caso en curso). Invariante común: no se incluyen casos que no completaron.
- La corrida parcial es un `SuiteResult` de longitud K, indistinguible en formato de una corrida de K casos.

**Deuda arrastrada:**

- SC-US3-003: verificación funcional del botón "Frenar" en la app real (pendiente; `run_every`/responsividad del fragment solo validados por diseño, no en ejecución contra el agente).
- Reanudar (resume) una corrida frenada: fuera de alcance.

**Pipeline:** ruff (lint+format), mypy --strict, naming (src), lint-imports, bandit, pytest unit (209) — todo verde. `check_constitution` OK.

**SSOTs afectados:** `specs/SPEC-006-batch-suite.md` (US3 nueva), `specs/SPECS_REGISTRY.md` (rev.2026-06-01), `historial/sdd.md`.

---

## 2026-05-22 — Iter 0 (bootstrap)

**Scope cerrado:**

- Estructura de carpetas: `src/{domain,adapters,build,dashboard}`, `data/`, `specs/`, `docs/`, `historial/`, `tests/{unit,integration}`, `runs/`, `tools/`.
- Datasets crudos copiados desde el proyecto raíz a `data/` (`intake_clasificacion.csv`, `intake_clasificacion.json`).
- Specs base:
  - `SPEC-000-naming` (active) — regla transversal de nomenclatura agnóstica.
  - `SPEC-000-bootstrap` (active) — alcance, criterios y tooling de la Iter 0.
  - `SPECS_REGISTRY.md` listando todas las specs vigentes y planeadas.
- Documentación SSOT por dominio (patrón EnVivo): `docs/{ARCHITECTURE,DEVELOPMENT,CONTRIBUTING,PRODUCT}.md`.
- Configuración: `.env.example`, `requirements.txt`, `requirements-dev.txt`, `pyproject.toml` (ruff + mypy strict + import-linter), `.pre-commit-config.yaml`, `.gitignore`, `README.md`, `CLAUDE.md` (protocolo SDD para asistentes).
- Linter de naming agnóstico: `tools/check_naming.py` con AST + lista de tokens prohibidos vinculada a `SPEC-000-naming`. Verificado en suite vacía: exit 0.

**Decisiones tomadas:**

- Nombre del proyecto: `agent-test-suite` (agnóstico).
- Ubicación: `c:\AA\Proyectos\Claude\test_circuito_intents\agent_test_suite\`.
- `domain/` no importa de `adapters/` ni `dashboard/` (ADR-001 en `ARCHITECTURE.md`); validado por `import-linter`.
- Dataset enriquecido vive en `data/test_cases.dataset.json`, gitignored por defecto (decisión revisable en Iter 1 según el flujo de versión que el equipo prefiera).
- Linter de naming verifica nombres de clase, función, variable top-level, anotaciones y stem del archivo. Excepciones documentadas en `SPEC-000-naming` ("Excepciones explícitas") cubren `.env` vars y docs orientadas a humanos.

**Deuda arrastrada a Iter 1:**

- `pre-commit install` y verificación end-to-end del hook depende de tener `git init` y `pre-commit` instalado en el entorno; no se ejecutó como parte de Iter 0.
- `lint-imports` necesita ser instalado y validado contra la estructura real una vez existan módulos importables (Iter 1).
- `mypy --strict src` sobre `src/` vacío (solo `__init__.py`) pasa trivialmente; verificación real llega con código en Iter 1.

**SSOTs afectados:**

- `specs/SPECS_REGISTRY.md`, `specs/SPEC-000-naming.md`, `specs/SPEC-000-bootstrap.md`
- `docs/ARCHITECTURE.md`, `docs/DEVELOPMENT.md`, `docs/CONTRIBUTING.md`, `docs/PRODUCT.md`
- `README.md`, `CLAUDE.md`, `historial/sdd.md` (este archivo)

**[SDD-Check] — Iter 0**

- Specs leídas: SPEC-000-naming, SPEC-000-bootstrap
- Includes/excludes verificados: nombres agnósticos en `src/` (suite vacía, sin violaciones); capas declaradas en `pyproject.toml` (validación real en Iter 1 con código)
- SSOTs afectados: ver lista arriba

---

## 2026-05-22 — Pivot post-Iter 0: datos no versionados + dos modos de entrada

**Aprendizaje aplicado** (ciclo SDD adaptativo en acción): el usuario aclaró que el CSV/JSON del workspace padre son **referencia del schema y modelos**, no fuente operativa del proyecto. Los datos de prueba se cargan en runtime por la interfaz; no se commitean. El roadmap arranca por el caso **simple** (un caso por pantalla) y posteriormente agrega el modo **batch** (interfaz estable).

**Cambios aplicados:**

- Eliminados `data/intake_clasificacion.csv` y `data/intake_clasificacion.json` que se habían copiado al proyecto en Iter 0.
- `.gitignore` ahora excluye todo `data/*` salvo `.gitkeep`.
- `SPECS_REGISTRY.md` reordenado:
  - `SPEC-001-single-case-input` (Iter 1) — entrada por pantalla, un caso.
  - `SPEC-002-agent-client` (Iter 2).
  - `SPEC-003-classification-evaluator` (Iter 3).
  - `SPEC-004-batch-input` (Iter 4) — entrada batch por interfaz estable.
  - `SPEC-005-runner` (Iter 5).
  - `SPEC-006-dashboard-suite` (Iter 6).
- `SPECS_REGISTRY.md` agrega sección "Política de datos".
- `docs/PRODUCT.md` describe los dos modos y reemplaza "Origen del dataset" por "Referencia del schema".
- `docs/ARCHITECTURE.md`: ADR-002 reescrito ("Datos cargados en runtime por interfaz, no versionados"); `src/build/` queda reservado para utilidades del modo batch.
- `README.md` y `docs/DEVELOPMENT.md` actualizan comandos: el dashboard arranca el modo simple; el runner headless queda para más adelante.

**SSOTs afectados:**

- `specs/SPECS_REGISTRY.md`
- `docs/PRODUCT.md`, `docs/ARCHITECTURE.md`, `docs/DEVELOPMENT.md`
- `README.md`, `.gitignore`

**Nota SDD**: este pivot ilustra exactamente la naturaleza adaptativa de SDD — la spec inicial se ajustó tras una observación del usuario, sin necesidad de "abrir un cambio formal". Las specs registradas como `draft` para Iter 1+ aún no se escribieron, así que solo se renombraron en el registry.

---

## 2026-05-22 — Iter 1 (entrada de un caso por pantalla)

**Scope cerrado:**

- `SPEC-001-single-case-input` (active): schema del `TestCase`, reglas de validación, alcance del dashboard simple, fuera-de-alcance documentado con links a futuras specs.
- `src/domain/test_case.py`: dataclass frozen + slots con 23 campos (identificación, intent, declaración, datos requeridos, contexto, esperado). Validación completa en `__post_init__`. Constante pública `PALETA_CLASIFICACION = ("Verde", "Amarillo", "Rojo", "Negro")`. Métodos `to_payload()` y `expected()` para separar lo que va al agente del ground truth.
- `src/domain/ports.py`: `Protocol`s para `AgentClient`, `TestCaseRepository`, `CredentialProvider` + dataclass `AgentResponse`. Stubs listos para las implementaciones de Iter 2+.
- `src/dashboard/app.py`: formulario interactivo agrupado por secciones (identificación, intent, declaración, datos, contexto, esperado). Encapsula el framework UI bajo el alias `ui` para mantener nombres agnósticos en el dominio. Modo simple end-to-end de la captura: form → validación → display del payload + esperado. **No** envía al agente (eso es Iter 2).
- `tests/unit/test_test_case.py`: 26 tests, 100% cobertura del modelo, parametrizados por campo y por clasificación.

**Verificaciones ejecutadas:**

- `pytest tests/unit`: 26/26 pasados, 0 warnings.
- `ruff check src tests tools`: All checks passed.
- `ruff format --check`: 14 archivos OK.
- `tools/check_naming.py src` y `tests`: sin violaciones.
- Cobertura `src/domain/test_case.py`: 100%.

**Decisiones tomadas:**

- `TestCase` con `__test__ = False` para evitar que pytest intente recolectarlo como clase de test (Python permite la convivencia del modelo de dominio con el naming `Test*` que se usa para casos de prueba — el conflicto es de pytest, no del dominio).
- Validación lanza `ValueError` con el nombre del campo afectado en el mensaje, para que el dashboard pueda mostrarlo directamente.
- `marcadores` se almacena como `tuple` (inmutable) aun si el caller pasa una lista; conversión transparente en `__post_init__`.
- Streamlit se importa como `ui` para que ningún identificador del archivo arrastre el nombre del framework. El nombre del paquete (`dashboard`), del módulo (`app`) y de las funciones (`_render_*`, `main`) son agnósticos. (Validado por el linter de naming.)
- Test `test_caso_es_inmutable` ahora captura `FrozenInstanceError` específicamente (no `Exception`) — atendiendo a `B017` de ruff.

**Deuda arrastrada a Iter 2:**

- `mypy --strict src` no se ejecutó (mypy no instalado en el Python del sistema). Acción: instalar `requirements-dev.txt` y correrlo. La estructura del código es type-safe pero no verificado por la herramienta.
- `lint-imports` no se ejecutó. Acción: instalar `import-linter` y verificar el contrato declarado en `pyproject.toml`.
- `pre-commit install` y validación de hooks pendiente: requiere `git init` en el proyecto.

**SSOTs afectados:**

- `specs/SPECS_REGISTRY.md` (SPEC-001 marcada como active)
- `specs/SPEC-001-single-case-input.md` (criterios de aceptación marcados)
- `src/domain/test_case.py`, `src/domain/ports.py`, `src/dashboard/app.py`
- `tests/unit/test_test_case.py`
- `historial/sdd.md` (este archivo)

**[SDD-Check] — Iter 1**

- Specs leídas: SPEC-000-naming, SPEC-000-bootstrap, SPEC-001-single-case-input
- Includes/excludes verificados: nomenclatura agnóstica en `src/` y `tests/` (linter verde); envío al agente y comparación contra esperado **excluidos explícitamente** (van a SPEC-002 y SPEC-003); modo batch excluido (SPEC-004).
- SSOTs afectados: ver lista arriba.

---

## 2026-05-22 — Iter 2 (cliente de agente remoto + smoke de conexión)

**Scope cerrado:**

- `SPEC-002-agent-client` (active): contrato del adapter remoto + spec del smoke.
- `src/adapters/platform_config.py`: `PlatformConfig` (frozen) con `from_env()`. Único punto del sistema que lee `os.environ`. Normaliza `chat_url` (asegura trailing slash) y parsea `ACCURACY_THRESHOLD`. Falla con `MissingConfigError` legible si falta alguna var.
- `src/adapters/token_provider.py`: `TokenProvider` con cache + refresh contra `time.monotonic`, inyectable para tests. Reusa el flujo de `chat.py:get_token` sin `st.session_state`.
- `src/adapters/remote_agent_client.py`: `RemoteAgentClient` implementa `AgentClient`. Reusa `chat.py:call_agent_api`; payload con/sin `thread_id`, manejo legible de errores HTTP, conversación devuelta en `AgentResponse.conversation_id`.
- `tools/connection_check.py`: CLI de smoke (`python tools/connection_check.py [--list-agents] [--prompt ...]`), exit codes 10/20/30 distinguen fallo de config, token y envío.
- 18 tests unitarios nuevos (44 totales): cubren stubs para session HTTP, expiración + refresh de token, payloads con/sin thread, errores HTTP, respuestas malformadas, parsing de env.

**Verificaciones ejecutadas:**

- `pytest tests/unit`: 44/44 verde.
- `ruff check` y `ruff format --check`: All checks passed.
- `tools/check_naming.py` sobre `src/`, `tests/`, `tools/`: sin violaciones.

**Decisiones tomadas:**

- Inyección de `requests.Session` y `clock` en `TokenProvider` y `RemoteAgentClient` para tests determinísticos sin red.
- Errores HTTP en `send()` **no** levantan excepción; devuelven `AgentResponse` con `content` que empieza con prefijo legible (`"Error API:"`, `"Error conexion:"`, `"Respuesta sin formato:"`). Decisión: mantener la semántica del proyecto base (chat.py) para no romper el dashboard cuando se integre.
- `dotenv` es opcional: si no está instalado, `from_env()` sigue funcionando leyendo solo `os.environ` (importante para CI sin `.env`).
- **Excepción de naming**: `json` se permite explícitamente como identificador (método `.json()` de `requests.Response`) — ver actualización a `SPEC-000-naming`, sección "Identificadores permitidos". El linter respeta una constante `ALLOWED_IDENTIFIERS`.

**Deuda arrastrada a Iter 3:**

- **Smoke real contra el agente**: pendiente que el usuario corra `python tools/connection_check.py` con un `.env` válido. Sin esto, la spec queda con un criterio sin marcar.
- Integración del adapter al dashboard (envío real desde el form) se hace al inicio de Iter 3, una vez que exista el evaluador, para mostrar pass/fail completo en pantalla.
- `mypy --strict` aún no se ejecutó (mypy no instalado en el entorno).

**SSOTs afectados:**

- `specs/SPECS_REGISTRY.md`, `specs/SPEC-002-agent-client.md`, `specs/SPEC-000-naming.md` (allowlist `json`)
- `src/adapters/{platform_config,token_provider,remote_agent_client}.py`
- `tools/{connection_check,check_naming}.py`
- `tests/unit/test_{platform_config,token_provider,remote_agent_client}.py`

**[SDD-Check] — Iter 2**

- Specs leídas: SPEC-000-naming, SPEC-001, SPEC-002
- Includes/excludes verificados: cliente y smoke implementados; comparación contra esperado **excluida** (SPEC-003); integración al dashboard pospuesta a Iter 3; allowlist de naming documentado en `SPEC-000-naming`.
- SSOTs afectados: ver lista arriba.

---

## 2026-05-22 — Iter 2 follow-up: smoke real verde

El usuario corrió `tools/connection_check.py` con `.env` real. Diagnóstico iterativo:

1. Primer intento: 500 en `/agents`. Causa identificada: las URLs del `.env` tenían el placeholder `<instance-id>` sin reemplazar. La instrumentación del request (URL + headers) que se agregó al smoke permitió detectarlo de un vistazo.
2. Reemplazado el instance id y configurado `AGENT_ID` real, auth y envío respondieron 200. El agente devolvió `"A new flow has started. This chat session is currently dedicated to the flow..."` con un `conversation_id`.

**Observaciones para próximas specs:**

- El agente puede no responder con clasificación al primer envío: arranca un *flow* y espera turnos sucesivos en el mismo `thread_id`. SPEC-003 absorbe este caso como "indeterminado" sin agregar polling todavía. Si el patrón se mantiene en uso real, abrir una iter dedicada con `RetryingAgentClient` / polling de turnos.
- Endpoint del cliente confirmado funcional (`{chat_url}{agent_id}/chat/completions`).

---

## 2026-05-22 — Iter 3 (evaluador + tajada vertical completa del modo simple)

**Scope cerrado:**

- `SPEC-003-classification-evaluator` (active): reglas de extracción (regex case-insensitive + bordes de palabra), normalización a paleta canónica, política "primer match", semántica de indeterminado.
- `src/domain/result.py`: `TestResult` frozen + slots con `to_dict()` y propiedad `verdict` (`pass` / `fail` / `indeterminado`).
- `src/domain/classification_evaluator.py`: `ClassificationEvaluator.extract(response)` y `evaluate(case, agent_response)`. Sin I/O, sin red, sin estado.
- `src/dashboard/app.py`: integración completa de SPEC-001 + SPEC-002 + SPEC-003. Botón **Validar caso** persiste el caso en `session_state`; botón **Enviar al agente** dispara `PlatformConfig.from_env()` → `TokenProvider` → `RemoteAgentClient.send` → `ClassificationEvaluator.evaluate` → muestra veredicto + métricas + respuesta cruda + `conversation_id` + JSON del `TestResult`.
- `tests/unit/test_classification_evaluator.py`: 17 tests (paleta completa, case-insensitive, bordes de palabra, primer match, sin match, pass/fail/indeterminado, serialización).

**Verificaciones ejecutadas:**

- `pytest tests/unit`: 61/61 verde.
- `ruff check` y `ruff format --check`: All checks passed.
- `tools/check_naming.py` sobre `src/`, `tests/`, `tools/`: sin violaciones.

**Decisiones tomadas:**

- **Indeterminado vs error**: si la respuesta del agente no contiene un color de la paleta, no es un fallo del cliente sino un caso "indeterminado". Permite separar fallos de comunicación (manejados en `RemoteAgentClient` con prefijos `"Error API:"`) de respuestas semánticas no-clasificatorias (flows en curso, preguntas de clarificación).
- **`TestResult.passed: bool | None`**: tri-estado para no perder información cuando no hubo extracción. La UI distingue tres veredictos.
- **Prompt construido en el dashboard**: encabezado fijo `"Clasifica la siguiente iniciativa segun la paleta..."` + payload del caso serializado. Decisión revisable: podría moverse a un módulo de dominio dedicado (`PromptBuilder`) si el prompt requiere más sofisticación en iters futuras.
- **`import json` con alias local `_serializer`** dentro de `_build_prompt`: el módulo estándar `json` es la API de Python, no es nuestro identificador. El linter (que escanea nombres asignados) lo ignora correctamente, pero usamos alias `_serializer` para reforzar la intención agnóstica si alguien lee el código sin contexto.
- **Sin polling de flow del agente** en esta iter: deuda registrada. Si la mayoría de las respuestas reales caen en "indeterminado", abriremos una iter dedicada al patrón multi-turno.

**Deuda arrastrada a Iter 4 (o iter intermedia):**

- **Verificación funcional end-to-end con un caso real**: pendiente que el usuario lance el dashboard y observe el veredicto.
- **Polling multi-turno** si el agente requiere conversación para clasificar.
- `mypy --strict` y `lint-imports` siguen pendientes de instalación.

**SSOTs afectados:**

- `specs/SPECS_REGISTRY.md`, `specs/SPEC-003-classification-evaluator.md`
- `src/domain/{result,classification_evaluator}.py`
- `src/dashboard/app.py`
- `tests/unit/test_classification_evaluator.py`

**[SDD-Check] — Iter 3**

- Specs leídas: SPEC-000-naming, SPEC-001, SPEC-002, SPEC-003
- Includes/excludes verificados: tajada vertical del modo simple completa; modo batch (SPEC-004) y persistencia de runs (SPEC-005) **excluidos**; polling de flow **excluido** con deuda explícita.
- SSOTs afectados: ver lista arriba.

---

## 2026-05-24 — Corrección crítica SPEC-002 + verificación e2e SPEC-003 + enriquecimiento SPEC-007

**Scope cerrado:**

- Diagnóstico y corrección de `wait_for_completion()`: el polling de `/flows` nunca funcionaba porque `thread_id` (de `chat/completions`) ≠ `agent_thread_id` (en `/flows`) — son dos sistemas de IDs distintos. Reemplazado por polling de `/threads/{thread_id}/messages`.
- Descubierto que el campo `content` en mensajes del thread puede ser una lista `[{"response_type":"text","text":"..."}]`; agregado helper `_extract_text()` en `remote_agent_client.py`.
- `conversation_probe.py` corregido con el mismo mecanismo.
- Dashboard (`app.py`): respuesta cruda ahora renderiza como markdown y muestra todos los mensajes del thread.
- Errores de linting preexistentes en `tools/connection_check.py` y `tools/list_orchestrate_instances.py` corregidos.
- Specs actualizadas: SPEC-002 (wait_for_completion, criterios, historial), SPEC-003 (step 5 del flujo), SPEC-007 (get_trace por run_id, correlación pendiente).
- `docs/AGENT-INVOCATION.md` reestructurado: nueva sección 2 que documenta los dos planos de IDs, `run_id` como candidato de correlación, uso correcto de `/flows` para traza, formato de content como lista.

**Verificaciones ejecutadas:**

- `pytest tests/unit`: 79/79 verde.
- `ruff check` + `ruff format --check` sobre `src/`, `tests/`, `tools/`: All checks passed.
- Prueba real del flow completo vía `_post_chat` directo: confirmado que el payload completo desencadena flow async (~5.5 s, control message), y la respuesta final aparece en `/threads/{thread_id}/messages` a los ~10 s como `riesgo: VERDE\n\nFastGate Preguntas: ...`.
- Verificación funcional e2e del dashboard: el usuario confirmó que el dashboard funciona correctamente tras el fix — **criterio final de SPEC-003 cerrado**.

**Decisiones tomadas:**

- `/flows` NO sirve para polling de completion (IDs distintos). SÍ sirve para traza interna (SPEC-007).
- `/threads/{thread_id}/messages` es el mecanismo correcto para saber cuándo terminó el agente.
- `run_id` del body de `chat/completions` es el candidato para correlacionar con `/flows` en SPEC-007 — pendiente verificación empírica antes de implementar `get_trace()`.
- `_extract_text()` exportada como función de módulo (no método) para reutilización en dashboard y tools.
- `flows_url` permanece en `PlatformConfig` para SPEC-007; no se elimina.

**Deuda arrastrada:**

- ~~Verificación funcional e2e del dashboard~~ — cerrado 2026-05-24.
- Verificación empírica de correlación `run_id` → `instance_id` en `/flows` (prerrequisito para implementar SPEC-007).
- `mypy --strict src/`: verde (verificado 2026-05-24, 13 archivos sin issues).
- `lint-imports` sigue pendiente (no instalado).
- `pre-commit install` pendiente (no hay git repo).

**SSOTs afectados:**

- `specs/SPECS_REGISTRY.md` (SPEC-002 iter actualizada)
- `specs/SPEC-002-agent-client.md` (wait_for_completion, criterios, historial)
- `specs/SPEC-003-classification-evaluator.md` (step 5 del flujo de integración)
- `specs/SPEC-007-agent-trace.md` (get_trace por run_id, correlación, cambio en send())
- `docs/AGENT-INVOCATION.md` (secciones 2–9 reestructuradas)
- `src/adapters/remote_agent_client.py` (_extract_text, wait_for_completion)
- `src/dashboard/app.py` (display markdown, thread messages expander)
- `tools/conversation_probe.py` (_poll_thread reemplaza _poll_flow)
- `tools/connection_check.py`, `tools/list_orchestrate_instances.py` (linting)
- `tests/unit/test_remote_agent_client.py` (tests de wait_for_completion reescritos)

**[SDD-Check] — 2026-05-24**

- Specs leídas: SPEC-002, SPEC-003, SPEC-007, AGENT-INVOCATION.md
- Includes/excludes verificados: corrección de wait_for_completion incluida; implementación de SPEC-007 (get_trace) **excluida** — pendiente verificación de run_id; modo batch (SPEC-004) y runner (SPEC-005) excluidos.
- SSOTs afectados: ver lista arriba.

---

## 2026-05-22 — Estado al cierre de sesión (snapshot para retomar)

> **Para la próxima sesión: leer esta sección + `specs/SPECS_REGISTRY.md` y arrancar.**

### Resumen ejecutivo

Iter 0–3 cerradas en código (61 tests verde, ruff/format/naming limpios). La **verificación end-to-end con el agente real está bloqueada** por una particularidad del agente bajo test, no por bugs del cliente.

### Lo que funciona hoy

- `agent_test_suite/` con estructura completa (domain / adapters / dashboard / build / specs / docs / historial / tests / tools).
- Auth OAuth2 contra Watson IAM: OK (`tools/connection_check.py` devuelve token de ~1898 chars).
- POST a `{chat_url}{agent_id}/chat/completions`: OK (200, respuesta válida).
- Cliente, evaluator, dashboard integrados y testeados con stubs.
- Linter de naming agnóstico con allowlist documentado en `SPEC-000-naming`.

### El bloqueo

El agente bajo test (`AGENT_ID=16bf9a27-3eea-4ce6-8e6d-fd5bacce4a1b`, nombre **"TEST - FI Orquestador"**) responde **siempre** lo mismo en `stream=false`:

> "A new flow has started. This chat session is currently dedicated to the flow and will resume once the flow is complete."

La clasificación (Verde/Amarillo/Rojo/Negro) **nunca llega por esa vía**.

### Hipótesis descartadas (no volver a probar)

1. **`thread_id` mal enviado** — Descartada. El probe instrumentado (`tools/conversation_probe.py --verbose`) confirma que el server respeta el thread (turno 3 de `runs/probe-20260522T164700.json` lo prueba: pedimos algo con el thread del turno 2 y el server reconoce el contexto del flow en curso).
2. **El cliente nuevo difiere de `chat.py` base** — Descartada. **El usuario probó `chat.py` original (Streamlit del proyecto base) y se comporta exactamente igual**: también recibe el placeholder y no llega a clasificación. No es regresión del código nuevo.
3. **Timeout corto cortando la respuesta** — Descartada. El server responde **rápido** con el placeholder (no se queda procesando dentro de la misma request HTTP).
4. **Orden de claves en el payload** — Normalizado de todos modos (`thread_id` primero como en `chat.py:152`), no cambia el comportamiento.

### Hipótesis vigentes (sin testear todavía)

1. **(MÁS PROBABLE)** **Streaming SSE**: el flow real devuelve la clasificación por chunks SSE cuando se llama con `"stream": "true"`. La UI de Watson Orchestrate probablemente usa este modo. **Probe armado en `tools/streaming_probe.py`** pero **no se ejecutó con un caso real todavía**. Esto es lo primero a probar al retomar.
2. **Endpoint separado** (`/runs/<id>`, `/executions/<id>` o similar): el flow corre asíncrono y el resultado se recupera por otro endpoint. Investigable abriendo DevTools del navegador en la UI de Watson mientras se corre el flow manualmente.
3. **Agente alternativo síncrono**: el usuario no sabe si existe otro agente del catálogo que devuelva la clasificación inline sin pasar por el orquestador. Pregunta abierta.

### Próximos pasos al retomar (en orden)

1. **Lanzar `tools/streaming_probe.py`** con un caso real:
   ```bash
   cd c:/AA/Proyectos/Claude/test_circuito_intents/agent_test_suite
   python tools/streaming_probe.py --file <caso.json> --timeout 300
   ```
   El probe guarda el stream crudo en `runs/streaming-<ts>.txt`.

2. **Inspeccionar los chunks devueltos**:
   - Si entre los chunks aparece la clasificación (Verde/Amarillo/Rojo/Negro) → confirmado streaming. Agregar `stream_send()` a `RemoteAgentClient` y actualizar `SPEC-002` para soportar ambos modos.
   - Si solo llega el placeholder y se cierra → no es streaming. Investigar endpoint alternativo (paso 3).

3. **Si streaming no es el camino**: pedir al usuario que abra DevTools en la UI de Watson Orchestrate mientras ejecuta el flow manualmente, copie las llamadas de red al ver el resultado, y las comparta.

4. **Alternativa paralela**: averiguar si hay otro agent_id directo. Si sí, cambiar `AGENT_ID` en `.env` y volver a testear la suite tal cual está — no requiere código nuevo.

### Archivos clave para retomar

- `specs/SPECS_REGISTRY.md` — qué specs hay, qué estado.
- `specs/SPEC-002-agent-client.md` — modificar al agregar streaming.
- `src/adapters/remote_agent_client.py` — agregar método `stream_send()` cuando confirmemos el patrón.
- `tools/streaming_probe.py` — probe listo a lanzar.
- `runs/probe-20260522T164700.json` — transcripción que prueba que el thread_id sí se respeta.
- `runs/probe-20260522T165434.json` — JSON solo, 1 turno, placeholder inmediato.
- `runs/probe-20260522T165516.json` — JSON + poke, prueba que poke en el thread no trae resultado.

### Deuda técnica acumulada (no bloqueante)

- `mypy --strict src` y `lint-imports` no se han ejecutado nunca (mypy/import-linter no instalados en el entorno).
- `pre-commit install` pendiente: requiere `git init` en `agent_test_suite/`.
- Smoke real del flujo end-to-end de Iter 3 pendiente (depende de resolver el bloqueo).

### Decisiones tomadas que NO revisar al retomar (a menos que el usuario lo pida)

- Nomenclatura agnóstica como regla transversal (SPEC-000-naming).
- Tres capas (`domain` / `adapters` / `dashboard`) con `domain` libre de imports de adapters.
- Datos no versionados; carga por interfaz en cada run (simple / batch).
- Match exacto contra `clasificacion_esperada` (no LLM-judge, no variantes aceptables).
- Streamlit como framework del dashboard, encapsulado en `src/dashboard/`.

### Lo último que estabas haciendo

El usuario lanzó `chat.py` base (Streamlit) para comparar comportamiento. Después del fix de `.env` (faltaba copiarlo a la carpeta del proyecto base), pudo conectarse y **confirmó que `chat.py` se comporta igual**: el agente devuelve "flow has started" y no la clasificación, igual que con el código nuevo. Eso ratifica que el problema es del lado del agente, no del cliente.

**[SDD-Check] — snapshot de cierre de sesión**

- Specs leídas: SPEC-000-naming, SPEC-000-bootstrap, SPEC-001, SPEC-002, SPEC-003 (todas active).
- Includes/excludes verificados: bloqueo documentado, hipótesis vigentes listadas, próximos pasos accionables sin tener que reconstruir contexto.
- SSOTs afectados: `historial/sdd.md` (este archivo).

---

## 2026-05-25 — Pivot de formato: SDD híbrido (Spec Kit) desde SPEC-004

### Contexto

El bloqueo del agente (placeholder "flow has started") quedó **resuelto**; SPEC-001/002/003 se
cierran con el método casero. A partir de aquí se adopta un **formato de spec híbrido**: se mantiene
el registro central (`SPECS_REGISTRY.md`), la nomenclatura `SPEC-NNN-slug`, las specs vivas y el
`historial/`, pero **el cuerpo de cada spec nueva usa la anatomía de GitHub Spec Kit**: User Story
con prioridad (P1/P2/P3), `FR-NNN MUST`, `SC-NNN` medibles, escenarios Given/When/Then y un
*coverage mapping* requisito→cobertura. NO se adopta la CLI `specify`, ni branches git, ni la
carpeta `specs/[###-feature]/` por feature (incompatibles con el registro central y con que este
repo no usa git).

Esto forma parte del experimento "**híbrido vs baseline B-06**" del proyecto SDD de análisis
(`analisis/SDD/`, ver `software/ANALISIS-SPEC-KIT.md` y `experimentos/RESULTADO-EXPERIMENTO-B6.md`).
Este repo es el **proyecto testigo** de esa investigación.

### Decisión de corte (acordada con el usuario)

- Hasta **SPEC-003** → formato casero (terminado, no se re-toca: preserva la baseline observacional B-06 congelada al 2026-05-24).
- Desde **SPEC-004** → formato híbrido.

### Re-corte del roadmap en HUs (IDs reusados / redefinidos)

El viejo roadmap (004 batch-input, 005 runner, 006 dashboard-suite, 007 trace) se rebanó en tajadas
verticales independientemente testeables:

- **SPEC-004-single-case-file** (P1) — carga de un caso unitario desde archivo (sigue modo simple).
- **SPEC-005-run-persistence** (P1) — persistir/revisar el resultado de una ejecución (unitario); fija el esquema de `runs/` (ADR-004).
- **SPEC-006-batch-suite** (P2) — ejecución batch + resultados conjuntos + accuracy global (absorbe el viejo SPEC-004 + la ejecución del viejo SPEC-005).
- **SPEC-008-suite-metrics** (P2) — matriz de confusión 4×4 + accuracy por clase + % sin clasificación (separado del viejo SPEC-006).
- **SPEC-007-agent-trace** → estado **`notas`, fuera de secuencia activa**: diagnóstica (no bloquea el valor de producto) y con la correlación `run_id → flow instance_id` sin verificar. Se reescribirá como HU si se retoma. No cuenta para el experimento de formato.

Orden de implementación por dependencias: **004 → 005 → 006 → 008**.

### Notas de diseño

- Se respetaron las capas (`build/` carga, `domain/` lógica pura + agregados como `SuiteResult`, `adapters/` I/O como `FileRunRepository`, `dashboard/` solo render) y la nomenclatura agnóstica (SPEC-000-naming).
- Las specs referencian entidades aún inexistentes (`SuiteResult`, `FileRunRepository`, `src/runner`, `domain/metrics.py`) como forward-references; se crean al implementar cada HU.
- Los `[NEEDS CLARIFICATION]` quedaron **embebidos** en cada spec (decisión del usuario: resolver al implementar): multi-caso en modo simple, esquema del run JSON, manejo de filas inválidas en batch, tratamiento de Indeterminados en accuracy/matriz, ubicación del runner headless.

### Deuda arrastrada

- Implementar SPEC-004→008 (draft, sin código).
- Resolver los `[NEEDS CLARIFICATION]` al implementar cada HU.
- Riesgo `run_id → instance_id` de SPEC-007 (congelado en notas).
- Deuda de tooling previa: `mypy --strict`, `lint-imports`, `pre-commit install` (requiere `git init`) — sigue pendiente, no bloqueante.
- Redactar el experimento intervencional "híbrido vs baseline B-06" en `analisis/SDD/experimentos/` (tarea del proyecto de análisis, no de este repo).

**[SDD-Check]**

- Specs leídas: SPEC-000-naming, SPEC-001, SPEC-002, SPEC-003, PRODUCT.md, ARCHITECTURE.md.
- Includes/excludes verificados: formato híbrido SPEC-004+; SPEC-007 fuera de secuencia; SPEC-001/002/003 casero no se re-tocan (baseline B-06 intacta).
- SSOTs afectados: `specs/SPECS_REGISTRY.md` (tabla + convenciones + sección notas) y este `historial/sdd.md`. `PRODUCT.md`/`ARCHITECTURE.md` no modificados.

---

## 2026-05-25 — Schema del agente, MessageBuilder, RECHAZADO y mejoras de UX

### Scope cerrado

**Specs nuevas:**
- `SPEC-002b-message-builder` (active) — `MessageBuilder` en `src/build/`: mapping canónico `TestCase → {"form": {...}}` según la firma oficial del agente. Formaliza el contrato de envío que antes era un string ad-hoc serializado por el caller.
- `SPEC-003b-rejected-response` (active) — Detección de `RECHAZADO` en la respuesta del agente y evaluación por exact match (mismo mecanismo que las clasificaciones de riesgo).

**Revisiones de specs existentes:**
- `SPEC-001` rev.2026-05-25 — campo `datos_otros_mensaje: str` agregado a `TestCase`; `PALETA_CLASIFICACION` extendida con `"Rechazado"`.
- `SPEC-002` — sección "Revisión pendiente" que documenta conflicto con FR-004 de SPEC-002b (firma de `send()` cambiada).
- `SPEC-003` rev.2026-05-25 — botón "Evaluar otro caso" (dos posiciones); corrección de referencia `SPEC-004-batch-input` → `SPEC-006-batch-suite`; `client.send(prompt)` → `client.send(form)`.
- `SPEC-000-bootstrap` — `docs/SPEC-FORMAT.md` declarado como SSOT del formato híbrido.
- `00-INDEX` — `schemas/` incorporado a la estructura y al mapa de SSOTs; `docs/SPEC-FORMAT.md` en ruta de lectura.

**Código implementado:**
- `src/domain/test_case.py`: campo `datos_otros_mensaje: str` con validación (fuerza `"N/A"` si `datos_otros=False`; rechaza vacío si `datos_otros=True`); `PALETA_CLASIFICACION` incluye `"Rechazado"`; `to_payload()` eliminado (responsabilidad movida al builder).
- `src/build/message_builder.py`: función pura `build(case) → dict` con mapping completo de 22 campos, 3 excluidos (`id`, `clasificacion_esperada`, `marcadores`), estructura anidada correcta (`tipo_intent`, `datos_requeridos.otros`).
- `src/adapters/remote_agent_client.py`: `send()` cambia firma de `str` a `dict[str, Any]`; serialización a JSON ocurre internamente. Fix de detección de mensaje final: ya no busca solo `"riesgo:"` — toma el primer mensaje `assistant` que no sea el control message, capturando también respuestas `RECHAZADO`.
- `src/domain/ports.py`: `AgentClient.send()` actualizado a `form: dict[str, Any]`.
- `src/domain/classification_evaluator.py`: regex extendido con `rechazado`; `_CANON` incluye la forma canónica `"Rechazado"`.
- `src/dashboard/app.py`: contador de generación `form_gen` para resetear todos los widgets del formulario con valores por defecto; botón "Evaluar otro caso" en dos posiciones (arriba del payload y al pie de resultados); campo `datos_otros_mensaje` con `disabled` condicional.
- `schemas/FI_Orquestador_Input.schema.json`: contrato oficial del agente incorporado y versionado en el proyecto.

**Tests:**
- 96 tests pasando (desde 61 antes de la sesión): +3 `TestCase` (datos_otros_mensaje), +6 `MessageBuilder`, +6 `ClassificationEvaluator` (RECHAZADO), +5 adapter actualizados, +4 classification_evaluator (regression guards).

### Decisiones tomadas

- **`to_payload()` eliminado del dominio**: el dominio no debe conocer el schema del adapter. La responsabilidad de construir el payload es del `MessageBuilder` en `src/build/`, que sí conoce la firma del agente.
- **`schemas/` como directorio de primer nivel**: el schema del agente es un contrato de interfaz externo, no datos ni código. Se versiona junto al proyecto para que cualquier cambio en la firma del agente sea visible en el diff.
- **RECHAZADO en paleta**: `"Rechazado"` es un valor válido de `clasificacion_esperada`. Permite probar intencionalmente que el agente rechaza casos inválidos. El veredicto sigue siendo exact match: esperaba Rechazado y vino Rechazado → pass.
- **Fix de detección de mensaje final**: el filtro `"riesgo:"` ocultaba respuestas RECHAZADO. Reemplazado por "primer mensaje assistant que no sea el control message" — más robusto y cubre todos los formatos de respuesta del agente.
- **Contador de generación para reset de formulario**: Streamlit cachea widgets por key; cambiar el sufijo de todas las keys al resetear fuerza valores por defecto sin recargar la página.

### Deuda arrastrada

- SPEC-004 → 005 → 006 → 008 sin implementar (draft).
- `lint-imports` y `pre-commit install` pendientes (sin git init).
- Verificación empírica del campo `datos_otros_mensaje` en una respuesta real del agente con `datos_otros=True`.

**SSOTs afectados:**
- `specs/SPECS_REGISTRY.md`, `specs/SPEC-001-single-case-input.md`, `specs/SPEC-002-agent-client.md`, `specs/SPEC-002b-message-builder.md`, `specs/SPEC-003-classification-evaluator.md`, `specs/SPEC-003b-rejected-response.md`, `specs/SPEC-000-bootstrap.md`
- `00-INDEX.md`, `schemas/FI_Orquestador_Input.schema.json`
- `src/domain/test_case.py`, `src/domain/ports.py`, `src/domain/classification_evaluator.py`
- `src/build/message_builder.py`, `src/adapters/remote_agent_client.py`, `src/dashboard/app.py`
- `tests/unit/test_{test_case,message_builder,classification_evaluator,remote_agent_client}.py`

**[SDD-Check] — 2026-05-25**

- Specs leídas: SPEC-001, SPEC-002, SPEC-002b, SPEC-003, SPEC-003b, SPEC-000-bootstrap, FI_Orquestador_Input.schema.json.
- Includes/excludes verificados: MessageBuilder y schema enforcement incluidos; SPEC-004+ excluidos; traza (SPEC-007) excluida; `to_payload()` eliminado del dominio correctamente.
- SSOTs afectados: ver lista arriba.

---

## 2026-05-25 — Cierre de etapa SPEC-000 a SPEC-003b: sincronización docs + cierre SPEC-002b

### Scope cerrado

**SPEC-002b cerrada (draft → active):**
- 2 tests nuevos de validación jsonschema: `test_payload_valida_contra_schema_oficial` y `test_payload_con_datos_otros_valida_contra_schema` — verifican que `MessageBuilder.build()` produce un dict que pasa `jsonschema.validate()` contra `schemas/FI_Orquestador_Input.schema.json`.
- SC-001 a SC-004 marcados `[x]`. Total: 8 tests en `test_message_builder.py`, 98 tests en la suite.
- `SPECS_REGISTRY.md` actualizado: SPEC-002b `draft → active`.

**Cosmética del dashboard (`src/dashboard/app.py`):**
- Botones renombrados: `"Evaluar otro caso"` → `"Limpiar y Evaluar otro caso"` (ambas posiciones).
- Botón superior reubicado al nivel del título: columnas `[8, 2]`, visible solo cuando hay un caso validado en session. Eliminado el botón que estaba debajo del subheader "Envio al agente bajo test".
- Campo `id` declarado opcional en el formulario: si el usuario lo deja vacío el dashboard genera un identificador interno (`TC-{uuid[:8].upper()}`). El dominio no cambió (`TestCase` sigue exigiendo `id` no vacío — siempre llega con valor).

**Sincronización SPEC-002 con la implementación:**
- `send()` renombrado `prompt → form` en la spec (recibe `dict`, serializa internamente).
- Ejemplo de flujo corregido: `client.send(json.dumps(form))` → `client.send(form)` con `message_builder.build(case)` explícito.
- `extract_classification()` aclarada como responsabilidad de SPEC-003, no de SPEC-002.
- Sección "Revisión pendiente" eliminada (SPEC-002b ya está cerrada).

**SPEC-001 actualizada:**
- `id` documentado como correlación interna; el dashboard lo genera automáticamente si se deja vacío. Criterio de aceptación nuevo marcado `[x]`.

**Documentación reescrita:**
- `docs/AGENT-INVOCATION.md` — reescrito como SSOT real de conexión y flujo: diagrama corregido (muestra polling de `/threads`, no el viejo `/flows`); RECHAZADO documentado en sección de formato; `/flows` separado en sección dedicada de traza interna con estados y sub-agentes.
- `docs/ARCHITECTURE.md` — `src/build/` actualizado: ya no está vacío; describe `message_builder.py` y reserva el futuro batch.
- `docs/SPEC-FORMAT.md` — reescrito: origen del formato casero, origen del GitHub Spec Kit, tabla de por qué hibridar, estructura completa del template híbrido, reglas de redacción (FR/SC/Given-When-Then), ciclo de vida de estados, referencia a SPEC-003b como primer ejemplo real.
- `README.md` — paleta actualizada (agrega Rechazado), quick start corregido a Linux, tabla de docs agrega AGENT-INVOCATION.md, estado actualizado (iters 0–3b completadas).
- `00-INDEX.md` — AGENT-INVOCATION.md agregado a ruta de lectura (ítem 5) y mapa de SSOTs.

### Verificaciones ejecutadas

- `pytest`: 98/98 verde.
- `mypy --strict src`: 14 archivos sin issues.
- `ruff check src tests tools`: All checks passed.
- `ruff format --check src tests tools`: 29 archivos OK.
- `tools/check_naming.py src tests tools`: sin violaciones.

### Decisiones tomadas

- **`id` opcional en el form, obligatorio en el dominio**: el schema del agente no requiere el ID — es solo correlación interna. El dashboard asume la responsabilidad de generarlo; el dominio no necesita saber que puede venir vacío del formulario.
- **AGENT-INVOCATION.md como SSOT operativo**: distingue claramente "flujo del cliente" (lo que implementa `RemoteAgentClient`) de "flujo interno del agente" (lo que hace Watson Orchestrate con `/flows`). El diagrama anterior mezclaba ambos y mostraba la exploración diagnóstica como si fuera el flujo productivo.
- **SPEC-FORMAT.md reescrito desde cero**: el template genérico del GitHub Spec Kit no era útil sin el contexto SDD del proyecto. El nuevo documento explica el origen, la razón de hibridar y las reglas específicas del proyecto.

### Deuda arrastrada

- SPEC-004 → 005 → 006 → 008 sin implementar (draft).
- `lint-imports` y `pre-commit install` pendientes (sin git init).
- Verificación empírica de `datos_otros_mensaje` con un caso real donde `datos_otros=True`.

**SSOTs afectados:**
- `specs/SPECS_REGISTRY.md`, `specs/SPEC-001-single-case-input.md`, `specs/SPEC-002-agent-client.md`, `specs/SPEC-002b-message-builder.md`
- `docs/AGENT-INVOCATION.md`, `docs/ARCHITECTURE.md`, `docs/SPEC-FORMAT.md`
- `README.md`, `00-INDEX.md`
- `src/dashboard/app.py`
- `tests/unit/test_message_builder.py`

**[SDD-Check] — cierre etapa SPEC-000 a SPEC-003b**

- Specs leídas: SPEC-000-bootstrap, SPEC-000-naming, SPEC-001, SPEC-002, SPEC-002b, SPEC-003, SPEC-003b.
- Includes/excludes verificados: toda la documentación de SPEC-000 a SPEC-003b sincronizada con implementación; SPEC-004+ excluidos; traza SPEC-007 excluida.
- SSOTs afectados: ver lista arriba.

---

## 2026-05-26 — Pipeline local SDD + bandit (seguridad estática)

**Scope cerrado:**

- `tools/pipeline_local.sh`: script bash que corre en secuencia los 7 pasos del SDD-Check local: `ruff lint`, `ruff format --check`, `mypy --strict`, `naming agnostico`, `lint-imports`, `bandit -r src -q` (nuevo), `pytest tests/unit`. Acepta `--fail-fast` para detenerse en el primer fallo. Acumula fallos y reporta resumen al final con código de salida 0/1.
- `docs/DEVELOPMENT.md`: tabla "Comandos clave" actualizada con `bandit`, `pipeline_local.sh` y su variante `--fail-fast`. Sección "Cuándo correr qué" apunta el pipeline como paso de cierre de iteración.
- `CLAUDE.md`: paso 1 de "Al cerrar una iteración" reemplaza `pre-commit run --all-files` por `bash tools/pipeline_local.sh` como referencia primaria; pre-commit queda como fallback.

**Decisiones tomadas:**

- Bandit incorporado como check de seguridad estática (tomado del repertorio de reflexio); alcance `src/` con `-q` para output compacto.
- El pipeline es local y autocontenido: no referencia rutas externas (reflexio). La integración de checks de reflexio se resolvió incorporando el check equivalente (`bandit`) directamente, no creando dependencia de paths.
- Pre-commit se mantiene como mecanismo de hook de commit; el pipeline es la herramienta de cierre de iteración.

**Primera corrida verde (2026-05-26):**

- 7/7 pasos OK: ruff lint, ruff format, mypy --strict (15 archivos), naming agnóstico, lint-imports (contrato domain KEPT), bandit, pytest unit (120/120).
- Corrección aplicada en camino: docstring largo en `tests/unit/test_case_loader.py:122` acortado (E501); ruff format aplicado al mismo archivo. Ambos arrastrados desde la iter anterior sin detectar.
- Fix de entorno: `lint-imports` instalado vía `pip --user` no estaba en el PATH del shell bash; el script resuelve esto detectando `sysconfig.get_path("scripts","nt_user")` y agregándolo al PATH al inicio.

**Deuda arrastrada:**

- SPEC-004 → 005 → 006 → 008 sin implementar (draft, sin cambio respecto a iters anteriores).

**SSOTs afectados:**

- `tools/pipeline_local.sh` (nuevo)
- `docs/DEVELOPMENT.md`
- `CLAUDE.md`
- `historial/sdd.md` (este archivo)

**[SDD-Check] — 2026-05-26**

- Specs leídas: SPEC-000-naming, SPEC-000-bootstrap
- Includes/excludes verificados: pipeline corre checks de comportamiento sin cambiar lógica de dominio; SPEC-004+ excluidos.
- SSOTs afectados: ver lista arriba.

---

## 2026-05-25 — Convención de keywords en FRs (SPEC-FORMAT.md)

**Scope cerrado:** corrección de convención de redacción en specs híbridas — sin cambio de comportamiento ni de código.

### Decisión tomada

**Keywords al inicio del FR, nunca en el medio.** Formato: `MUST: [sujeto + verbo en presente]`. Motivación: la posición del keyword en el medio de la frase (`El sistema MUST aceptar...`) rompe la lectura natural en español. La regla se formalizó en `docs/SPEC-FORMAT.md` (sección "FR — Functional Requirements") con ejemplo bien/mal y template actualizado.

### Specs corregidas

Todos los FRs y bullets de Edge Cases con keyword en medio de frase fueron migrados al nuevo formato en: SPEC-002b, SPEC-003b, SPEC-004, SPEC-005, SPEC-006, SPEC-007, SPEC-008.

### Deuda arrastrada

Sin cambio respecto al cierre anterior.

**SSOTs afectados:** `docs/SPEC-FORMAT.md`, SPEC-002b a SPEC-008 (sección FR de cada una).

**[SDD-Check]**

- Specs leídas: SPEC-FORMAT.md (SSOT de convenciones), SPEC-002b, SPEC-003b, SPEC-004, SPEC-005, SPEC-006, SPEC-007, SPEC-008.
- Includes/excludes verificados: SPEC-000 a SPEC-003 (formato casero) excluidos — la convención aplica solo al formato híbrido.
- SSOTs afectados: `docs/SPEC-FORMAT.md`.

---

## 2026-05-26 — Constitución del proyecto + Constitution Check

### Contexto

Los principios no-negociables estaban dispersos (nomenclatura en `SPEC-000-naming`, capas/evaluación/datos en ADRs de `ARCHITECTURE.md`, spec-first en `CLAUDE.md`). No había un único artefacto que declarara "esto nunca cede" ni un paso que lo verificara. Se adopta el patrón `constitution.md` + Constitution Check de GitHub Spec Kit, adaptado al contexto sin CLI: documento liviano de invariantes que referencia los SSOTs (no duplica) + check de integridad en el pipeline + gate de lectura en el protocolo del agente.

### Scope cerrado

- `CONSTITUTION.md` (nuevo, raíz): 5 principios no-negociables del sistema — I. Nomenclatura agnóstica, II. Capas limpias, III. Evaluación determinista (sin LLM-judge), IV. Datos no versionados, V. Trazabilidad spec↔código. Cada principio declara un invariante autocontenido + `Enforcement:` + `Detalle:` apuntando al SSOT. Sección Governance con versionado semver y procedimiento de enmienda. Versión inicial 1.0.0.
- `tools/check_constitution.py` (nuevo): verifica integridad — cada `Detalle:`/`Enforcement:` referencia un archivo que existe; el enforcement automático (`check_naming.py`, `lint-imports`) está cableado en el pipeline; la línea de versión está bien formada. Imprime los principios para visibilidad. Exit 0/1.
- `tools/pipeline_local.sh`: nuevo paso `constitucion` como primer check (sección gobernanza). Total 8/8.
- `CLAUDE.md`: gate — leer `CONSTITUTION.md` es el primer ítem de "Antes de cualquier cambio"; un conflicto spec↔principio se resuelve ajustando la spec. Lista de checks del pipeline actualizada.
- `00-INDEX.md`: `CONSTITUTION.md` agregado a la ruta de lectura (ítem 2) y al mapa de SSOTs.

### Decisiones tomadas

- **La constitución es del sistema, no del agente.** `CLAUDE.md` es el arranque del asistente IA y puede cambiar si se usa otro sistema; la constitución sigue vigente. Por eso "specs primero" se expresa como invariante de trazabilidad del proyecto (Principio V), no como protocolo del agente.
- **Invariante en la constitución, detalle en el SSOT.** El documento declara la afirmación estable (ej. "los identificadores no nombran al proveedor"); el detalle que evoluciona (allowlist, ejemplos) vive en el SSOT referenciado. Esto evita ambigüedad sobre dónde está el contenido canónico y elimina riesgo de duplicación divergente.
- **Control por integridad, no bloqueante por contenido.** El check no juzga si el código respeta los principios (eso lo hacen `check_naming`, `lint-imports`, tests); verifica que la constitución sea coherente (sin referencias rotas) y la hace visible en cada corrida. Equivale a una versión liviana de la consistency propagation de `/speckit.constitution`.

### Verificaciones ejecutadas

- `python tools/check_constitution.py CONSTITUTION.md`: exit 0, imprime 5 principios.
- Prueba negativa: `Detalle:` apuntando a ruta inexistente → exit 1 con la referencia rota señalada. Revertido.
- `bash tools/pipeline_local.sh`: VERDE 8/8 (constitución, ruff lint, ruff format, mypy --strict, naming, lint-imports, bandit, pytest unit 120/120).
- Corrección en camino: `ruff format` aplicado a `tools/check_constitution.py`; fix de encoding (reconfigure stdout/stderr a UTF-8) para imprimir el carácter `↔` del Principio V en consolas Windows cp1252.

### Deuda arrastrada

- SPEC-004 `active`; SPEC-005 → 006 → 008 sin implementar (draft, sin cambio).
- `lint-imports` y `pre-commit install` siguen pendientes de cableado a git (sin `git init`).
- Capa opcional futura: skill `/constitution` en `.claude/commands/` para enmiendas con versionado/propagación automatizados (equivalente a `/speckit.constitution`). No implementada.

**SSOTs afectados:**

- `CONSTITUTION.md` (nuevo), `tools/check_constitution.py` (nuevo)
- `tools/pipeline_local.sh`, `CLAUDE.md`, `00-INDEX.md`
- `historial/sdd.md` (este archivo)

**[SDD-Check] — 2026-05-26**

- Specs leídas: SPEC-000-naming, ARCHITECTURE.md (ADR-001/002/003), SPECS_REGISTRY.md, SPEC-FORMAT.md (para derivar los invariantes).
- Includes/excludes verificados: la constitución declara invariantes y referencia SSOTs (no duplica); no introduce reglas nuevas, consolida las existentes. Skill `/constitution` excluido.
- SSOTs afectados: ver lista arriba.

---

## 2026-05-26 — Iter 5 (persistencia de runs, modo unitario)

**Aprendizaje aplicado:** al resolver los `[NEEDS CLARIFICATION]` de SPEC-005 con el usuario surgieron decisiones de diseño que se documentan abajo. El accuracy a nivel caso resultó redundante con el veredicto → se separó la estadística en dos granularidades y la de corridas se difirió a SPEC-006.

### Scope cerrado

- `domain/result.py`: `verdict` ahora se serializa en `TestResult.to_dict()`; nuevo `SuiteResult` (frozen) con factory puro `create()` (deriva `run_id`/`timestamp` de un instante, sin I/O), propiedades de conteo, `summary`, `to_dict()`/`from_dict()`.
- `domain/ports.py`: nuevo puerto `RunRepository` (`save`/`load`).
- `adapters/file_run_repository.py` (nuevo): `FileRunRepository` escribe `runs/detail/run-<ts>-<case_id>.json` y apendea `runs/stats/estadistica-casos.csv` (encabezado único); `load`/`load_latest`; `RunPersistenceError` para fallo de I/O explícito.
- `dashboard/app.py`: persiste la corrida tras evaluar, informa dónde quedó guardada, y expone un expander que relee el último run desde disco sin invocar al agente (FR-007).
- Tests: `tests/unit/test_result.py` (verdict serializado, summary, round-trip, factory) y `tests/unit/test_file_run_repository.py` (round-trip incl. Indeterminado, append sin duplicar encabezado, `load_latest`, run inexistente, error de I/O).

### Decisiones tomadas

- **Carpetas separadas por tipo de salida**: detalle navegable en `runs/detail/` (JSON), estadística tabular en `runs/stats/` (CSV). Nombre de detalle `run-<ts>-<case_id>.json`; `run_id` = `run-YYYYMMDDTHHMMSS` vincula detalle ↔ filas CSV.
- **Dos granularidades de estadística**: `estadistica-casos.csv` (una fila por caso × corrida, sin accuracy — a nivel caso es redundante con el veredicto) la genera SPEC-005; `estadistica-corridas.csv` (con `accuracy_bruta` y `accuracy_efectiva`) se difiere a SPEC-006, donde una corrida agrega N casos y el accuracy tiene sentido. Disparada desde la misma pantalla a pedido.
- **Tratamiento de Indeterminado en accuracy** (a aplicar en SPEC-006): dos columnas — `accuracy_bruta = pass/total` y `accuracy_efectiva = pass/(total-indeterminado)`, `null` si el denominador es cero — para no perder información.
- **Factory de corrida en el dominio**: `SuiteResult.create()` usa `datetime.now(UTC)` como dato puro (cómputo, no I/O), respetando las capas; el dashboard compone y el adapter sólo escribe.

### Verificaciones ejecutadas

- `bash tools/pipeline_local.sh`: VERDE 8/8 (constitución, ruff lint, ruff format, mypy --strict, naming, lint-imports, bandit, pytest unit 131/131).
- `python tools/check_naming.py src`: exit 0 (los identificadores del adapter no nombran `json`/`csv`; el formato queda confinado en imports y literales).
- SC-005 (verificación funcional en la app real): ejecutada por el usuario — el resultado persiste y se relee desde disco. OK.

### Deuda arrastrada

- SPEC-006 (batch + estadística de corridas) reescrita con dos User Stories; sigue `draft` con cuatro `[NEEDS CLARIFICATION]`: filas inválidas, ubicación del runner headless, formato del archivo batch, estrategia de regeneración del CSV de corridas (regenerar vs. apendear).
- SPEC-007 / SPEC-008 sin implementar.
- `lint-imports` y `pre-commit install` siguen pendientes de cableado a git (sin `git init`).

**SSOTs afectados:**

- `specs/SPEC-005-run-persistence.md` (draft → active), `specs/SPEC-006-batch-suite.md` (reescrita), `specs/SPECS_REGISTRY.md`
- `docs/ARCHITECTURE.md` (ADR-004 actualizado con la estructura `detail/` + `stats/`)
- `src/domain/result.py`, `src/domain/ports.py`, `src/adapters/file_run_repository.py`, `src/dashboard/app.py`
- `tests/unit/test_result.py` (nuevo), `tests/unit/test_file_run_repository.py` (nuevo)
- `historial/sdd.md` (este archivo)

**[SDD-Check] — 2026-05-26 (Iter 5)**

- Specs leídas: SPEC-005-run-persistence, SPEC-006-batch-suite, SPEC-000-naming, SPEC-FORMAT.md, CONSTITUTION.md, ARCHITECTURE.md (ADR-001/004).
- Includes/excludes verificados: SPEC-005 genera detalle JSON + `estadistica-casos.csv`; excluye `estadistica-corridas.csv` y accuracy (→ SPEC-006) y métricas por clase (→ SPEC-008). Naming agnóstico verificado en el adapter de persistencia.
- SSOTs afectados: ver lista arriba.

---

## 2026-05-26 — Iter 6 (batch + estadística de corridas)

**Scope cerrado:**

- **Modo batch (US1)**: `build/batch_loader.py` parsea un CSV tabular plano (separador autodetectado `;`/`,`), mapea columnas a `TestCase`, reporta filas inválidas aparte y no aborta. `src/runner.py` orquesta headless (`python -m src.runner --in <archivo> --out runs/`): `run_one`/`run_batch` (un fallo no aborta la suite), `build_suite`, `select_final_response` (compartida con el dashboard). `SuiteResult` gana `accuracy_bruta`/`accuracy_efectiva`.
- **Estadística de corridas (US2)**: `FileRunRepository.load_all()` + `regenerate_run_stats()` regeneran `runs/stats/estadistica-corridas.csv` completo (idempotente, sin llamar al agente), con una fila por corrida y una fila `TOTAL` final (estadística general vía `aggregate_runs`/`OverallStats` en `domain/`). Disparado a pedido desde la sección Estadísticas del dashboard.
- **Visibilidad**: progreso por caso en vivo (callback `on_result` en `run_batch`; el headless imprime por línea, el dashboard lo renderiza) y respuesta cruda por caso en el dashboard.
- **Dashboard**: integración batch (cargar → ejecutar → resultados conjuntos + accuracy + detalle por caso), control de estadística, y títulos reescritos para reflejar la funcionalidad (Dashboard de pruebas — Agente de atención de intents).
- **Muestra**: `data/muestra_batch.csv` (gitignored) con 2 casos por clase (V/A/R/N) derivada de `intake_clasificacion.csv`.

**Decisiones tomadas (resolución de los 4 `[NEEDS CLARIFICATION]` + agregados):**

- Filas inválidas: reportar y seguir (no abortar), coherente con FR-006.
- Runner headless en `src/runner` (compone capas, no importado por `domain/`).
- Formato batch: CSV plano, separador autodetectado, nombres planos de `TestCase`, `clasificacion_esperada` obligatoria, `marcadores` opcional, columnas desconocidas (`resultado_p1..p5`) ignoradas.
- Regeneración del CSV de corridas: regenerar completo (idempotente), no apendear.
- Separador `;` en `estadistica-casos.csv` y `estadistica-corridas.csv` (coherencia con el input y Excel español) — ajuste también en SPEC-005 (spec viva).
- Naming del detalle: sufijo `-<case_id>` sólo en unitario; en batch `run-<ts>.json`.
- Estadística general: fila `TOTAL` al final del CSV + métricas en pantalla; cómputo en `domain/`.
- Archivo de entrada inexistente/ilegible: el runner falla de forma controlada (mensaje + exit 1), sin traceback.

**Verificaciones ejecutadas:**

- `bash tools/pipeline_local.sh`: VERDE 8/8 (constitución, ruff lint/format, mypy --strict, naming, lint-imports, bandit, pytest unit 158/158).
- SC-003 (suite headless escribe el run) y SC-007 (batch + estadística en el dashboard) verificados en la app real por el usuario.

**Deuda arrastrada:**

- **Evaluación del Fast Gate por pregunta** (`resultado_p1..p5`): requiere extender `TestCase`/`ClassificationEvaluator` → candidata a spec propia.
- SPEC-007 (traza del agente) y SPEC-008 (matriz de confusión, accuracy por clase) sin implementar.
- SPEC-009 (ejecución paralela): el batch actual es secuencial a propósito.
- `lint-imports`/`pre-commit install` siguen sin cableado a git (sin `git init`).
- El run persiste sólo `agent_id`; no versión de prompt ni entorno.

**SSOTs afectados:**

- `specs/SPEC-006-batch-suite.md` (draft → active), `specs/SPEC-005-run-persistence.md` (ajuste spec viva: separador `;`, naming detalle), `specs/SPECS_REGISTRY.md`
- `docs/ARCHITECTURE.md` (ADR-004)
- `src/domain/result.py`, `src/runner.py` (nuevo), `src/build/batch_loader.py` (nuevo), `src/adapters/file_run_repository.py`, `src/dashboard/app.py`
- `tests/unit/test_batch_loader.py` (nuevo), `tests/unit/test_runner.py` (nuevo), `tests/unit/test_result.py`, `tests/unit/test_file_run_repository.py`
- `historial/sdd.md` (este archivo)

**[SDD-Check] — 2026-05-26 (Iter 6)**

- Specs leídas: SPEC-006-batch-suite, SPEC-005-run-persistence, SPEC-004-single-case-file, SPEC-003-classification-evaluator, SPEC-002-agent-client, SPEC-000-naming, SPEC-FORMAT.md, CONSTITUTION.md, ARCHITECTURE.md (ADR-001/004), DEVELOPMENT.md, PRODUCT.md.
- Includes/excludes verificados: batch (parseo + ejecución + persistencia + estadística por corrida y general) incluido; matriz/accuracy por clase → SPEC-008; traza → SPEC-007; paralelismo → SPEC-009; Fast Gate por pregunta fuera de alcance. Naming agnóstico verificado en runner, batch_loader y persistencia.
- SSOTs afectados: ver lista arriba.

---

## 2026-05-27 — SPEC-010 creada (traza por caso en corridas batch)

**Scope cerrado (solo specs, sin código):**

- `SPEC-010-batch-trace` (nueva, `draft`): lleva la traza de ejecución del modo simple (SPEC-007) al flujo batch. Dos User Stories **encapsuladas de inicio a fin** (Acceptance/FR/Key Entities/SC/Assumptions/Coverage/Fuera de alcance propios por HU) y numeración de FR/SC **prefijada por HU** (`FR-US1-NNN`, `SC-US1-NNN`): US1 (P3) traza por caso a pedido, reutilizando modelo, puerto `get_trace` y panel de SPEC-007; US2 (P4, deseable) persistencia de la traza como extensión de SPEC-005.
- Recableado de punteros cruzados: `SPECS_REGISTRY.md` (fila nueva), `SPEC-007` (Relacionada con + Fuera de alcance ahora apuntan a SPEC-010), `SPEC-006` y `SPEC-008` (su "Traza del agente → SPEC-007/notas" reapuntado a SPEC-010), `SPEC-005` (Relacionada con + persistencia de traza → SPEC-010 US2).

**Decisiones tomadas:**

- **Spec dedicada en vez de HU en 007 u 008.** Se evaluaron tres hogares: SPEC-007 (cohesión por capacidad de traza), SPEC-008 (cohesión por contexto batch) y una spec nueva. Decisión del usuario: spec propia. Razón: meter batch en SPEC-007 rompía su slice deliberado ("un caso", su Independent Test es un caso simple) y la persistencia es en realidad extensión de SPEC-005, no de 007/008.
- **Paridad simple↔batch como motivación.** La traza en batch se obtiene igual que en simple (`get_trace` a pedido); persistirla es deseable pero no necesario, por eso queda como US2 diferible.
- **`[NEEDS CLARIFICATION]` registrados, no asumidos:** (1) FR-US1-004 — el detalle batch persiste `conversation_id` por caso, pero `get_trace()` consume `thread_id`; falta confirmar si coinciden o si hay que persistir `thread_id` (ligado al NEEDS CLARIFICATION de FR-008 de SPEC-007 sobre correlación `run_id → instance_id`). (2) FR-US2-001 — estructura de persistencia de la traza (embebida en `run-<ts>.json` vs. artefacto separado).

**Deuda arrastrada:**

- SPEC-010 sin implementar (draft); su US1 depende de que SPEC-007 esté implementada y estable (hoy `draft`, con la correlación `run_id`/`thread_id` aún sin verificar empíricamente).
- SPEC-007, SPEC-008, SPEC-009 siguen sin implementar.
- Resolver los dos `[NEEDS CLARIFICATION]` de SPEC-010 antes de codear.

**SSOTs afectados:**

- `specs/SPEC-010-batch-trace.md` (nuevo), `specs/SPECS_REGISTRY.md`
- `specs/SPEC-005-run-persistence.md`, `specs/SPEC-006-batch-suite.md`, `specs/SPEC-007-agent-trace.md`, `specs/SPEC-008-suite-metrics.md` (punteros cruzados)
- `historial/sdd.md` (este archivo)

**[SDD-Check] — 2026-05-27**

- Specs leídas: CONSTITUTION.md, SPEC-FORMAT.md, SPEC-005, SPEC-006, SPEC-007, SPEC-008, SPECS_REGISTRY.md.
- Includes/excludes verificados: SPEC-010 reutiliza el modelo/puerto/panel de SPEC-007 (no redefine traza), apunta la persistencia a SPEC-005 y excluye métricas (→ SPEC-008) y comparación entre runs/replay. Sin código en esta entrada; pipeline no aplica (cambio solo de specs).
- SSOTs afectados: ver lista arriba.

---

## 2026-05-27 — Estándar multi-HU formalizado + migración de SPEC-006

**Scope cerrado (solo specs/docs, sin código):**

- `docs/SPEC-FORMAT.md` (SSOT del método de redacción): nuevo **estándar multi-HU** para specs con 2+ User Stories — cada HU se encapsula de inicio a fin (Acceptance/FR/Key Entities/SC/Assumptions/Coverage/Fuera de alcance propios; solo header + Historial globales) y los FR/SC se **prefijan por historia** (`FR-US1-001`, `SC-US2-001`). Sección de estructura + esqueleto, regla en «User Stories y numeración», nota en «FR», y SPEC-010 citada como referencia viva del estándar. Specs de una sola HU siguen con el template simple (`FR-001` sin prefijo).
- `SPEC-006-batch-suite` migrada al estándar: reestructurada a dos HUs encapsuladas y renumerada (sin cambio de comportamiento). Mapeo registrado en su Historial. Las entradas históricas previas conservan la numeración vieja (registro de su fecha).

**Decisiones tomadas:**

- **Estándar único, no variante opcional** (decisión del usuario): no conviven dos estilos multi-HU. La forma de SPEC-010 (encapsulado total + prefijo por HU) es la regla; el patrón previo de SPEC-006 (numeración continua + secciones globales) queda obsoleto.
- **SPEC-006 se migra, no se deja como legacy** (decisión del usuario): aunque está `active`, se reescribe para consistencia total. Es renumeración + reagrupación, sin tocar comportamiento ni código; los SC siguen `[x]`.
- El SSOT de la regla es `docs/SPEC-FORMAT.md` (ya declarado SSOT del formato híbrido en SPEC-000-bootstrap y 00-INDEX); las decisiones de formato se registran en este historial, no en el doc (que no lleva sección Historial).

**Deuda arrastrada:**

- SPEC-006 es la única multi-HU preexistente; SPEC-010 ya nació en el estándar. No quedan otras specs multi-HU por migrar.
- Pendiente correr el pipeline local si en el futuro un check valida formato de specs (hoy no hay linter de estructura de specs; el cambio es documental).

**SSOTs afectados:**

- `docs/SPEC-FORMAT.md`
- `specs/SPEC-006-batch-suite.md` (migrada)
- `historial/sdd.md` (este archivo)

**[SDD-Check] — 2026-05-27 (estándar multi-HU)**

- Specs leídas: SPEC-FORMAT.md, SPEC-006, SPEC-010, SPEC-000-bootstrap, SPECS_REGISTRY.md.
- Includes/excludes verificados: regla documentada como estándar único; SPEC-006 migrada (renumeración sin cambio de comportamiento); specs single-HU no afectadas; sin cambios de código.
- SSOTs afectados: ver lista arriba.

## 2026-05-27 — Iter 7 (visor de traza de ejecución del agente — "traza simple")

**Scope cerrado:**

- `SPEC-007-agent-trace` implementada y pasada a `active`. Tajada completa por capas: modelo en `domain/`, fetching+mapeo en `adapters/`, render en `dashboard/`.
- `src/domain/agent_trace.py`: dataclasses frozen+slots `TraceStep` y `AgentTrace` + constante pública `TRACE_STEP_STATUSES`; validación en `__post_init__` (`step_id`/`agent_name` no vacíos, `status` en la paleta).
- `src/domain/ports.py`: `AgentClient` gana `get_trace(thread_id) -> AgentTrace`; `AgentResponse` gana `run_id: str | None = None`.
- `src/adapters/remote_agent_client.py`: `send()` captura `run_id` del body; `get_trace()` consulta `/flows`, selecciona el flow externo del agente más reciente y mapea sus pasos al dominio; nunca propaga excepción (devuelve traza sin pasos ante fallo/vacío). Normalización de estados del proveedor y resumen acotado de input/output viven solo en el adapter.
- `src/dashboard/trace_panel.py` + integración en `app.py`: sección "Traza de ejecución" colapsada por defecto tras el veredicto; "Traza no disponible" si no hay pasos.
- Tests: `tests/unit/test_agent_trace.py` (modelo) y casos nuevos en `tests/unit/test_remote_agent_client.py` (captura de `run_id`, mapeo de `/flows`, selección por recencia, vacío/error). Pipeline local **verde 8/8** (174 tests).

**Decisiones tomadas (resuelven los `[NEEDS CLARIFICATION]`):**

- **FR-007** — Se extendió `AgentResponse` con `run_id` opcional (default `None`) en vez de crear un dataclass nuevo: menos superficie, no rompe llamadores.
- **FR-008** — "Traza simple": correlación por **fallback documentado** (flow `trigger == flow_async_chat` + `agent_id` + más reciente), sin verificar empíricamente `run_id`. El `run_id` ya se captura para estrechar la correlación cuando se confirme contra un run real.
- **FR-010** — Streamlit no permite expanders anidados; como el panel vive dentro del expander de la sección, el input/output se muestra como resumen inline acotado (máx. 800 chars) en lugar de sub-expanders. Spec ajustada.

**Deuda arrastrada:**

- **SC-003 pendiente**: verificación funcional contra el agente real (un caso real desde el dashboard). Confirmará además la **forma real de `/flows`** — el mapeo del adapter se hizo contra la estructura documentada en `docs/AGENT-INVOCATION.md`; si difiere, se ajusta el mapper (no el dominio).
- Correlación exacta `run_id → flow` sigue sin verificar (FR-008): `[NEEDS CLARIFICATION]` acotado en la spec.
- Persistencia de la traza y traza por caso en batch quedan fuera de alcance → SPEC-005 (extensión futura) y SPEC-010.

**SSOTs afectados:**

- `specs/SPEC-007-agent-trace.md` (draft→active, decisiones registradas), `specs/SPECS_REGISTRY.md`
- `historial/sdd.md` (este archivo)

**[SDD-Check] — 2026-05-27 (Iter 7)**

- Specs leídas: SPEC-007, SPEC-000-naming, SPEC-002, SPEC-003, SPEC-005, SPECS_REGISTRY.md, CONSTITUTION.md, docs/ARCHITECTURE.md, docs/AGENT-INVOCATION.md.
- Includes/excludes verificados: FR-001..FR-011 implementados; FR-007/008 resueltos vía fallback simple; SC-001/002/004 verdes, SC-003 diferido a verificación funcional. Capas respetadas (mapeo del proveedor solo en adapter; `domain/` puro). Naming agnóstico verde sobre `src/`.
- SSOTs afectados: SPEC-007, SPECS_REGISTRY, historial/sdd.md.

## 2026-05-27 — Iter 7 fix: mapeo de traza al shape REAL de /flows (SC-003)

**Síntoma:** en el dashboard todos los pasos de la traza salían `in_progress` pese a que el agente ya había terminado.

**Causa raíz:** el adapter se había escrito contra la estructura *documentada* (asumida) de `/flows`, no la real. Verificado con un run real (vía nuevo `tools/dump_agent_trace.py`): el proveedor usa `state` (no `status`) para el estado del flow y de cada paso; los pasos viven en `tasks` (no `steps`); el orden de ejecución está en `sequence.steps`; la duración real está en `trace_context.duration_ms` (los `created_at`/`updated_at` son del registro, dan deltas irreales ~0.06s). Como `_map_step` leía `status` (inexistente), todo caía al default `in_progress`.

**Fix (solo adapter + ajuste menor de modelo, dominio sigue puro):**

- `_map_step` lee `state`, `task_instance_id`, `trace_context.duration_ms`; `_flow_steps` toma `tasks` y los ordena por `sequence.steps`; `overall_status` lee `state`.
- `TraceStep` gana `duration_ms: int | None` (additivo, default `None`); panel muestra duración desde `duration_ms`.
- Nueva herramienta de diagnóstico `tools/dump_agent_trace.py` (vuelca el JSON crudo de `/flows`; `--keys` lista claves por nivel) — clave para futuras divergencias de shape.
- Tests del adapter reescritos con fixture del shape real (estado por `state`, orden por `sequence`, descarte de task sin nombre, `duration_ms`). Pipeline local **verde 8/8** (175 tests).

**Verificación real:** `get_trace()` contra el agente devuelve 9 pasos ordenados (`cargar_iniciativa_v2` → … → `__flow_end__`), todos `completed`, con duraciones reales (2.7s, 16.8s, …). SC-003 marcado `[x]` (resta solo la mirada visual en el dashboard).

**Decisiones / deuda:**

- `docs/AGENT-INVOCATION.md` §6 ahora documenta el mapeo concreto (tablas flow/task) como SSOT del shape real.
- Recencia por `created_at` top-level (ISO). Correlación exacta `run_id → flow` sigue pendiente (FR-008): el fallback por recencia basta mientras no se confirme empíricamente.
- `tasks` sin `name` se descartan; sub-flows en `children` no se aplanan aún (la traza muestra los pasos del flow externo, suficiente para "traza simple").

**SSOTs afectados:** `specs/SPEC-007-agent-trace.md` (FR-002/FR-006/SC-003), `docs/AGENT-INVOCATION.md` (§6), `historial/sdd.md`.

**[SDD-Check] — 2026-05-27 (Iter 7 fix)**

- Specs leídas: SPEC-007, SPEC-000-naming, docs/AGENT-INVOCATION.md, docs/ARCHITECTURE.md.
- Includes/excludes verificados: mapeo corregido al shape real (state/tasks/sequence/duration_ms); dominio sigue puro (campo additivo); shape documentado en AGENT-INVOCATION §6; naming verde sobre `src/`; pipeline 8/8.
- SSOTs afectados: SPEC-007, AGENT-INVOCATION.md, historial/sdd.md.

## 2026-05-27 — Iter 7 fix #2: timing de la traza + reconciliación de docs

**Síntoma:** con el mapeo ya corregido, una corrida real mostró `overall_status: interrupted` y el task `actualizar_iniciativa` en `in_progress · 0.0s`, pese a que el veredicto llegó OK.

**Causa raíz (verificada, no es bug):** se consultó el mismo flow minutos después y estaba `completed` con `actualizar_iniciativa` en `completed` (6152ms) + `send_mail` + `__flow_end__`. El agente **deposita la clasificación en el thread antes de cerrar su cola de tareas finales**; `wait_for_completion()` retorna al ver ese mensaje, así que el primer `get_trace()` captura el flow externo aún `interrupted`. El veredicto (SPEC-003) no se ve afectado.

**Fix (UI, sin bloquear):**

- Nuevo **FR-012** en SPEC-007: botón "Actualizar traza" que re-`get_trace(thread_id)`; nota explicativa cuando `overall_status` no es terminal (`completed`/`failed`). `thread_id` ahora se guarda en `session_state["eval_result"]`. Helper `_refresh_trace()` en `app.py` (reconstruye runtime, re-fetch, `rerun`).
- Se descartó bloquear/poll en `get_trace()` (mantener la traza no-bloqueante; el refresh manual es más honesto y simple).

**Reconciliación de `docs/AGENT-INVOCATION.md` (puntos viejos que contradecían el shape real):**

- §6: la lista "Sub-agentes del flow anidado (`flow_nested`)" se reemplazó por "Pasos del flow externo (`tasks`)" con los 9 pasos reales en orden de `sequence.steps`. Se aclaró que las sub-evaluaciones (integridad/impacto/factibilidad) **no son tasks**: viven en `output.data.output_validador_intent` del task `FI - Agente validador de Intents`; la clasificación FastGate en `output.data.output_fast_gate` del task `FI Fast Gate Google`.
- §6: nota de timing en el estado `interrupted` (apunta a FR-012).
- §7: fila "Detalle de sub-evaluaciones" corregida (apunta al `output` del task, no a un `trigger == flow_nested`).

**Deuda:** correlación exacta `run_id → flow` sigue pendiente (FR-008); el aplanado de `children` (sub-flows) sigue fuera de alcance. Verificación visual final en el dashboard (reiniciar server) a cargo del usuario.

**SSOTs afectados:** `specs/SPEC-007-agent-trace.md` (FR-012), `docs/AGENT-INVOCATION.md` (§6/§7), `historial/sdd.md`.

**[SDD-Check] — 2026-05-27 (Iter 7 fix #2)**

- Specs leídas: SPEC-007, docs/AGENT-INVOCATION.md, docs/ARCHITECTURE.md.
- Includes/excludes verificados: causa de timing verificada empíricamente (flow pasó a `completed`); fix solo UI (refresh no-bloqueante); docs reconciliadas con el shape real; pipeline 8/8.
- SSOTs afectados: SPEC-007, AGENT-INVOCATION.md, historial/sdd.md.

## 2026-05-27 — Iter 7 cierre (verificación visual confirmada)

**Scope cerrado:** el usuario confirmó la verificación visual de la traza en el dashboard. Con esto **SC-001..SC-004 quedan completos** y SPEC-007 se cierra.

- SPEC-007 SC-003: nota de "resta verificación visual" reemplazada por la confirmación del usuario (la sección "Traza de ejecución" renderiza los pasos, "Actualizar traza" refresca el estado, "Traza no disponible" ante traza vacía).
- `SPECS_REGISTRY.md`: marca de iteración `7 impl.2026-05-27` → `7` (iteración cerrada, sin pendientes bloqueantes).
- Pipeline local **verde 8/8** (175 tests) reconfirmado al cierre.

**Deuda arrastrada (no bloqueante):**

- Correlación exacta `run_id → flow instance_id` (FR-008): `run_id` ya se captura (FR-007); estrechar el fallback por recencia cuando se ejercite empíricamente con un run real.
- Aplanado de sub-flows (`children`) fuera de alcance — la "traza simple" muestra los pasos del flow externo.
- Persistencia de la traza y traza por caso en batch → SPEC-005 (extensión futura) y SPEC-010.

**SSOTs afectados:** `specs/SPEC-007-agent-trace.md` (SC-003 + historial), `specs/SPECS_REGISTRY.md`, `historial/sdd.md`.

**[SDD-Check] — 2026-05-27 (Iter 7 cierre)**

- Specs leídas: SPEC-007, SPECS_REGISTRY.md, CONSTITUTION.md, 00-INDEX.md.
- Includes/excludes verificados: SC-001..SC-004 completos (verificación visual confirmada por el usuario); deuda de correlación `run_id` y aplanado de `children` documentada como no bloqueante; sin cambios de código (solo cierre documental); pipeline 8/8.
- SSOTs afectados: SPEC-007, SPECS_REGISTRY, historial/sdd.md.


## 2026-05-27 — Iter 10 (SPEC-010 cierre): traza por caso en batch

**Scope cerrado:** persistir la traza de ejecución por caso en corridas batch y exponer su `flow_id` para abrir el flow en la plataforma. Motivación del usuario: anclar cada caso del lote a su flow en Watson Orchestrate. SPEC-010 `draft`→`active`.

**Decisiones de diseño (previas a codear, ver SPEC-010 rev.2026-05-27):**

- Se descartó el **backfill** de runs ya guardados: el `conversation_id` persistido es el `thread_id` del cliente, que **no aparece en `/flows`**, y `get_trace()` correlaciona por recencia, no por `thread_id` (ver "Hallazgo de correlación" en SPEC-010 y `docs/AGENT-INVOCATION.md` §3/§6). Un fetch a pedido post-corrida no es confiable.
- Se invirtió el supuesto de SPEC-010: la traza se **captura en vivo** durante la corrida (US2, prerequisito) y la vista (US1) la **lee del run** sin invocar al agente.
- **Cierre del flow ("dos pasos") — opción C:** captura única por caso, sin poll ni segundo fetch; la traza se persiste tal cual aunque `overall_status` quede no terminal; el `flow_id` es el ancla. No se replica el botón "Actualizar traza" del dashboard (su refresh por recencia no es válido en batch). Descartadas A (poll hasta terminal) y B (refresh post-corrida por `flow_id`).

**Implementación:**

- `src/domain/agent_trace.py`: `TraceStep.from_dict` y `AgentTrace.from_dict` (round-trip).
- `src/domain/result.py`: `TestResult` gana `trace: AgentTrace | None = None` + propiedad `flow_id`; `to_dict` serializa la traza embebida; `SuiteResult.from_dict` la reconstruye.
- `src/runner.py`: `run_one` captura `client.get_trace(thread_id)` (única, vía helper `_capture_trace` que no aborta el caso ante fallo) y la adjunta con `dataclasses.replace`.
- `src/dashboard/app.py`: vista batch muestra `flow_id` por caso y, a pedido (checkbox, sin expander anidado), `render_trace` + nota si el estado no es terminal, sin botón de refresco.
- Tests: round-trip `from_dict` de la traza; round-trip de `SuiteResult` con traza (en memoria y a disco); captura única por caso; traza no terminal persistida tal cual; fallo de `get_trace` no aborta el caso.

**Verificación:** pipeline local **verde 8/8 (188 tests)**. **Verificación funcional confirmada por el usuario (2026-05-27):** corrida batch real y dashboard OK — `flow_id` por caso y traza se ven correctamente. Esto confirma empíricamente el supuesto de la opción C (en batch secuencial la recencia de `/flows` trae el flow del caso recién corrido). SC-US1-001..003 y SC-US2-001..003 completos.

**Deuda arrastrada (no bloqueante):**

- La captura por recencia asume ejecución **secuencial**; SPEC-009 (paralelo) la rompería hasta resolver la correlación exacta `run_id → flow_id` (deuda de SPEC-007 FR-008). Documentado en Assumptions de SPEC-010 US2.
- El modo simple (SPEC-007) sigue sin persistir la traza (queda en `session_state`); unificarlo con el esquema persistido es opcional.

**SSOTs afectados:** `specs/SPEC-010-batch-trace.md`, `specs/SPECS_REGISTRY.md`, `historial/sdd.md`.

**[SDD-Check] — 2026-05-27 (Iter 10 cierre)**

- Specs leídas: SPEC-010, SPEC-007, SPEC-005, SPEC-006, SPEC-009, SPEC-000-naming, CONSTITUTION.md, 00-INDEX.md, SPECS_REGISTRY.md, docs/AGENT-INVOCATION.md.
- Includes/excludes verificados: captura única en vivo (sin poll); traza embebida en el detalle del caso; round-trip save→load con y sin traza; resiliencia ante get_trace fallido; nomenclatura agnóstica (`flow_id`/`trace`); capas (domain/result importa domain/agent_trace, sin tocar adapters); pipeline 8/8; verificación funcional batch+dashboard confirmada por el usuario.
- SSOTs afectados: SPEC-010, SPECS_REGISTRY, historial/sdd.md.


## 2026-05-27 — Iter 8 (SPEC-008 cierre): métricas de suite (matriz de confusión)

**Scope cerrado:** matriz de confusión + accuracy por clase + % sin clasificación sobre corridas persistidas, sin re-ejecutar el agente. SPEC-008 `draft`→`active`.

**Decisiones de diseño (acordadas con el usuario antes de codear):**

- **Ejes de la matriz:** se usa `PALETA_CLASIFICACION` completa (5 clases, incluida `Rechazado` que agregó SPEC-003b), reconciliando la contradicción "4×4" del draft contra FR-002 (reutilizar la constante, no derivar una sublista). Matriz 5 filas × 6 columnas.
- **Indeterminados** (resuelve el `[NEEDS CLARIFICATION]` del Scenario 3): caen en una columna extra `Sin clasificación` (cada caso ocupa una celda; la suma de la matriz = total) **y** además se reportan como `% sin clasificación`.

**Ampliaciones acordadas durante la implementación:**

- **Matriz general agregada** (FR-007): `aggregate_suite_metrics` en `domain/metrics.py` trata los `TestResult` de N corridas como una sola población; toma el accuracy global de `aggregate_runs` (mismo cómputo que la fila TOTAL de `estadistica-corridas.csv`, sin duplicar fórmula).
- **Dashboard** (FR-004/006): matriz tras cada corrida batch; selector de corrida persistida (`run_id`) para ver su matriz sin re-ejecutar; opción «Todas las corridas» en el mismo selector para la matriz general. El render solo lee agregados del dominio.
- **Runner headless `--estadistica`** (FR-008, modo exclusivo, no ejecuta la suite): matriz total a **pantalla en Markdown** (tablas alineadas legibles) vía `format_metrics_markdown` y a **archivo CSV** (`runs/stats/estadistica-matriz.csv`, `;`) vía `format_metrics_report` + `save_metrics_report` (repositorio). `--in` pasó a opcional (obligatorio solo en modo normal). La salida a pantalla evita caracteres fuera de cp1252 (las flechas `↓/→` crasheaban la consola Windows; los tests con `capsys` no lo detectaban por capturar en UTF-8).

**Implementación:**

- `src/domain/metrics.py` (nuevo): `SuiteMetrics` (puro, serializable), `compute_suite_metrics`, `aggregate_suite_metrics`, helper `_build_metrics`. `accuracy_global` delega en `SuiteResult.accuracy_bruta`.
- `src/dashboard/app.py`: `_render_suite_metrics` / `_render_metrics_block`; selector en `_render_latest_run`.
- `src/runner.py`: `format_metrics_report` (CSV) + `format_metrics_markdown` (pantalla) + `_md_table` + modo `--estadistica`.
- `src/adapters/file_run_repository.py`: `save_metrics_report` → `estadistica-matriz.csv`.
- Tests: 14 en `tests/unit/test_metrics.py` + 6 en `tests/unit/test_runner.py` (formato CSV/Markdown, modo a pantalla+CSV, sin corridas, `--in` obligatorio).

**Verificación:** pipeline local **verde 8/8 (207 tests)**. **Verificación funcional CLI confirmada por el usuario** (`--estadistica` sobre 32 corridas / 327 casos: matriz Markdown alineada en pantalla + CSV escrito). Los tres renders del **dashboard** (matriz post-corrida, selector, «Todas las corridas») **verificados visualmente por el usuario (2026-05-28)**.

**Deuda arrastrada (no bloqueante):**

- Como la columna `marcadores` puede consolidar texto sin `|`, un caso puede quedar con un único "marcador" largo; separar tokens de descripción quedó fuera de alcance.

**SSOTs afectados:** `specs/SPEC-008-suite-metrics.md`, `specs/SPECS_REGISTRY.md`, `historial/sdd.md`.

**[SDD-Check] — 2026-05-27 (Iter 8 cierre)**

- Specs leídas: SPEC-008, SPEC-006, SPEC-005, SPEC-003, SPEC-003b, SPEC-001, SPEC-000-naming, CONSTITUTION.md, 00-INDEX.md, SPECS_REGISTRY.md, docs/PRODUCT.md.
- Includes/excludes verificados: matriz 5×5 sobre `PALETA_CLASIFICACION` (incluye `Rechazado`); columna extra `Sin clasificación` para indeterminados (suma de matriz = total); accuracy por clase N/A para clase sin casos (sin división por cero); cómputo puro en `domain/` sin I/O; `accuracy_global` reutiliza `accuracy_bruta` (no duplica fórmula de PRODUCT.md); matriz general agregada reutiliza `aggregate_runs`; runner `--estadistica` doble formato (Markdown pantalla / CSV archivo); nomenclatura agnóstica (sin `csv`/UI en identificadores); pipeline 8/8; verificación CLI confirmada; render de dashboard sin verificación visual (deuda anotada).
- SSOTs afectados: SPEC-008, SPECS_REGISTRY, historial/sdd.md.

## 2026-05-28 — SPEC-008 verificación visual completada

El usuario confirmó la verificación visual de los tres renders del dashboard: matriz post-corrida, selector de corrida persistida y opción «Todas las corridas». Con esto **SPEC-008 queda completamente cerrada** (todos los SC y FR verificados).

- `specs/SPEC-008-suite-metrics.md`: coverage mapping de FR-004/FR-006/FR-007 actualizado con la confirmación.
- `historial/sdd.md`: deuda de verificación visual eliminada.

**[SDD-Check] — 2026-05-28 (SPEC-008 cierre total)**

- Specs leídas: SPEC-008, SPECS_REGISTRY.md.
- Includes/excludes verificados: sin cambios de código; solo cierre documental de la deuda de verificación visual.
- SSOTs afectados: SPEC-008, historial/sdd.md.

## 2026-06-07 — ADR-005: extracción de la capa de aplicación (use-cases)

Refactor arquitectónico (no agrega capacidad de producto; gobernado por ADR, no por SPEC nueva — Principio V). La orquestación de corridas vivía atrapada en `src/runner.py`, el composition root del modo CLI; el dashboard la consumía con `from src.runner import run_one, ...` — un composition root importando a otro, arrastrando `argparse`/`sys` a la sesión Streamlit. Diagnóstico empírico: import cruzado real (`dashboard/app.py:37`) + el path unitario del dashboard (`_send_and_evaluate`) reescribía a mano el cuerpo de `run_one`.

**Decisiones tomadas (acordadas con el usuario):**

- **Nueva capa `src/application/`** (`run_suite.py`): use-cases `run_one`, `run_batch`, `build_suite`, `execution_failure`, `_capture_trace`, `ProgressCallback`. Reciben puertos por parámetro, reportan progreso por callback; sin UI, sin CLI, sin I/O directo. `runner.py` re-exporta por compatibilidad y queda como entrypoint headless/composition root.
- **`_extract_text` → `domain/message_text.py`** como `extract_message_text` (función pura ligada al contrato del puerto; antes privada en el adapter, importada por runner y dashboard).
- **Control message detrás del puerto** (revisión SPEC-002): nuevo método `AgentClient.get_final_response(thread_id, fallback_content)`. El filtrado del control message (`"a new flow has started"`) y la constante se confinan en `adapters/remote_agent_client.py`, donde ese conocimiento ya residía en `wait_for_completion` (ADR-001). `run_one` invoca `get_final_response`; `select_final_response` se disolvió (ya no es código compartido). `get_thread_messages` sigue crudo para el display del dashboard (2 GET en el path interactivo, 1 en el headless).
- **Stepping batch del dashboard** (`_run_batch_step`/`_finalize_batch`) permanece en `dashboard/`: es control de flujo de presentación (un caso por tick para atender "Frenar"), reutiliza `application.run_one`.
- **Formateo de reportes** (`format_metrics_*`) queda en `runner.py` (fuera de alcance).
- **Enforcement**: dos contratos `import-linter` nuevos — `application/` no importa adapters/dashboard/runner; el de `domain/` se extendió para prohibir además `application` y `runner`.

**Deuda arrastrada (no bloqueante):** el texto literal del control message sigue siendo un string acoplado al proveedor, ahora confinado al adapter; un próximo paso podría modelarlo como configuración del adapter.

**SSOTs afectados:** `docs/ARCHITECTURE.md` (ADR-005 + diagrama de capas), `specs/SPEC-002-agent-client.md`, `specs/SPEC-005-run-persistence.md`, `specs/SPEC-006-batch-suite.md`, `specs/SPEC-010-batch-trace.md`, `specs/SPECS_REGISTRY.md`, `pyproject.toml`, `historial/sdd.md`.

**[SDD-Check] — 2026-06-07 (ADR-005)**

- Specs leídas: SPEC-002-agent-client, SPEC-005-run-persistence, SPEC-006-batch-suite, SPEC-010-batch-trace, SPEC-000-naming, CONSTITUTION.md, 00-INDEX.md, SPECS_REGISTRY.md, docs/ARCHITECTURE.md.
- Includes/excludes verificados: capa `application/` sólo importa `domain/`+`build/` (lint-imports verde); `domain/` no importa application/runner; control message confinado al adapter (ningún caller lo conoce); `get_final_response` con fallback; `extract_message_text` agnóstico (naming verde); stepping batch del dashboard fuera de la capa; formateo de reportes fuera de alcance; re-export desde runner para compatibilidad de tests; pipeline local VERDE 9/9 (227 tests). Pendiente: verificación funcional del dashboard en la app real (modo simple + batch).
- SSOTs afectados: docs/ARCHITECTURE.md, SPEC-002, SPEC-005, SPEC-006, SPEC-010, SPECS_REGISTRY.md, pyproject.toml, historial/sdd.md.

---

## 2026-06-07 — SPEC-004: resolución hallazgo A1 de `/analyze` (cobertura FR-007)

**Scope (cambio de tests, sin cambio de comportamiento):**

`/analyze` sobre SPEC-004 detectó (A1, HIGH) que los tests de FR-007 duplicaban la lógica de inyección de `clasificacion_esperada` con un helper local `_inject()`, dejando las funciones reales del dashboard `_file_needs_clasificacion` e `_inject_clasificacion` sin cobertura — un bug en ellas (p. ej. bool invertido en la detección) pasaría verde. Mismo patrón que el gap histórico de `run_id`.

**Decisiones tomadas:**
- Eliminada la duplicación: `tests/unit/test_case_loader.py` reusa la `_inject_clasificacion` real en sus fixtures.
- Nuevo `tests/unit/test_dashboard_file_load.py`: ejercita directamente `_file_needs_clasificacion` (con/sin clave, vacía, JSON malformado, raíz no-objeto, fixture formato agente) e `_inject_clasificacion` (inyección, round-trip con la detección, raíz no-objeto, flujo end-to-end hasta `TestCase`).
- Import de helper puro del dashboard en tests: patrón ya establecido (`test_dashboard_batch_reset.py`).

**Deuda arrastrada (resto del reporte `/analyze`, no abordada aquí):** A2/A3 (Edge Cases implícitos: `form` no-dict, precedencia anidado>plano), A4 (FR-003 mapeado a `check_naming.py` en vez de `lint-imports`), A5/A6 (equivalencia de error form↔archivo, claim "100%" de SC-002), A7/A8 (defaults implícitos, FR-005 sin test).

**[SDD-Check] — 2026-06-07 (A1)**
- Specs leídas: SPEC-004-single-case-file, CONSTITUTION.md, SPECS_REGISTRY.md.
- Includes/excludes verificados: helpers FR-007 del dashboard ejercitados por código real (no copia); fixtures usan `_inject_clasificacion` real; sin cambio en `src/` (solo tests + spec); pipeline local VERDE 9/9 (238 tests).
- SSOTs afectados: SPEC-004 (Coverage mapping FR-007 + Historial), historial/sdd.md.

---

## 2026-06-14 — Terminología: «tajada vertical» → «corte vertical»

**Scope (cambio editorial/terminológico, sin cambio de comportamiento):**

A pedido del usuario se unificó el vocabulario del proyecto: «tajada vertical» (traducción rústica de *vertical slice*) pasa a **«corte vertical»**, más técnico y neutro. Renombradas las 7 ocurrencias en SSOTs vivos (`specs/SPEC-001`, `specs/SPEC-003` ×2, `specs/SPEC-009`, `docs/SPEC-FORMAT` ×2, `src/dashboard/app.py` docstring), con corrección de concordancia de género (`la/primera/completa` → `el/primer/completo`). El término queda fijado como canónico en `docs/SPEC-FORMAT.md` (nota "Término canónico"), prohibiendo «tajada» y «rebanada».

**Decisiones tomadas:**
- `historial/sdd.md` **no** se modifica (log append-only): las 4 ocurrencias previas reflejan la terminología vigente al momento de escribirse.
- No se toca `SPEC-000-naming`: regula tokens de tecnología (provider/framework/formato), no vocabulario de prosa; el SSOT del término es `docs/SPEC-FORMAT.md`.
- El docstring de `src/dashboard/app.py` es cosmético → sin test nuevo.

**Deuda arrastrada:** ninguna.

**[SDD-Check] — 2026-06-14**
- Specs leídas: SPEC-000-naming, SPEC-001-single-case-input, SPEC-003-classification-evaluator, SPEC-009-parallel-execution, docs/SPEC-FORMAT.md, CLAUDE.md.
- Includes/excludes verificados: 7 ocurrencias en specs/docs/src renombradas (grep "tajada" en `specs/ docs/ src/` → 0 residuos); `historial/` excluido a propósito; término canónico fijado en SPEC-FORMAT; cambio sin comportamiento (docstring) → sin test nuevo.
- SSOTs afectados: SPEC-001, SPEC-003, SPEC-009, docs/SPEC-FORMAT.md, src/dashboard/app.py, historial/sdd.md.

---

## 2026-06-28 — Skills multi-asistente (Claude/Codex/Antigravity/opencode)

**Scope (tooling del harness, sin SPEC — análogo a `docs/SDD-ENFORCEMENT.md` + `tools/sdd_gate.py`):**

Investigación web confirmó que Codex y Antigravity convergieron en el mismo formato de skill que Claude: carpeta `.agents/skills/<n>/SKILL.md` con frontmatter `name`+`description` y auto-descubrimiento por `description`. opencode es el único divergente (commands con invocación explícita, sin skill-dir; sus *custom prompts* quedaron deprecados a favor de skills).

Se estableció el patrón de unificación en dos capas: contenido en `docs/playbooks/<n>.md` (ya existente) y wrapper en `.agents/skills/<n>/SKILL.md` (nuevo SSOT, leído directo por Codex y Antigravity). El nuevo `tools/gen_skill_adapters.py` genera desde esa fuente los dos adaptadores que divergen: `.claude/skills/<n>/SKILL.md` y `.opencode/command/<n>.md`. Migradas las skills `analyze` y `clarify`; los `.claude/` y `.opencode/` previos pasan a ser artefactos generados (con cabecera `NO EDITAR A MANO`).

**Decisiones tomadas:**
- **Sin symlinks** (requisito Win+Linux): los symlinks de git necesitan Developer Mode en Windows. Se generan archivos reales committeados.
- **EOL forzado a LF** vía `.gitattributes` nuevo para que `--check` sea determinista entre SO.
- `--check` cableado en `tools/pipeline_local.sh` (paso «skills multi-tool») como gate anti-drift, mismo patrón que el resto del pipeline.
- **No es SPEC**: las SPEC-NNN son para comportamiento del producto, no para tooling. SSOT en `docs/SKILLS-MULTITOOL.md`.
- Cuerpo de `clarify` vuelto agnóstico: el binding `AskUserQuestion` (Claude) se reescribió como nota condicional ("si tu asistente ofrece UI de opción múltiple…").

**Deuda arrastrada:** rutas de Codex/Antigravity tomadas de docs oficiales (jun-2026); validar contra instalación real al adoptarlas. Antigravity tiene además `.agents/rules/` y `.agents/workflows/` (always-on/pipelines) fuera del alcance de este generador.

**[SDD-Check] — 2026-06-28**
- Specs leídas: ninguna (tooling del harness, sin SPEC); CONSTITUTION.md, AGENTS.md, docs/SDD-ENFORCEMENT.md (precedente de tooling sin spec).
- Includes/excludes verificados: `.agents/skills/{analyze,clarify}/SKILL.md` como fuente; `.claude/skills/` y `.opencode/command/` regenerados y verificados con `--check`; ruff+mypy --strict sobre `tools/gen_skill_adapters.py` VERDE; `.gitattributes` fuerza LF; pipeline gana paso «skills multi-tool».
- SSOTs afectados: docs/SKILLS-MULTITOOL.md (nuevo), .agents/skills/ (nuevo), 00-INDEX.md, tools/pipeline_local.sh, historial/sdd.md.

---

## 2026-07-03 — Iter 13: selección de adaptador de cliente (SPEC-013)

**Scope:** implementación completa de SPEC-013-client-adapter-selection (permanece `draft`: toda spec requiere la prueba funcional manual del usuario antes de cerrarse, y está pendiente). La plataforma tecnológica del agente bajo prueba pasa a ser seleccionable por configuración (`AGENT_CLIENT_TYPE`): `remote_async` (cliente original, default, retrocompatible) o `sync_http` (nuevo adaptador síncrono REST con auth por header de llave).

**Cambios:**
- `adapters/platform_config.py`: lee `AGENT_CLIENT_TYPE` (FR-001) con requeridad de variables condicional al tipo activo (FR-006) y nuevas variables genéricas `ALT_CLIENT_URL`/`ALT_CLIENT_API_KEY` (FR-009). Tipo desconocido → `MissingConfigError` antes de cualquier red (SC-003).
- `adapters/sync_agent_client.py` (nuevo): `SyncHttpAgentClient` cumple los 5 métodos del puerto `AgentClient` (FR-002). Postea el `form` plano en la raíz del body, sin envoltorio ni `id` (FR-010); colapsa el pipeline multi-etapa por pass-through genérico del color del bloque final, o `Rechazado` si el bloque viene `null` por corto-circuito (FR-011); simula el ciclo conversacional con `conversation_id` sintético + cache, transparente para `run_one` (FR-012); fallos técnicos (no-200, timeout, forma inesperada) → `conversation_id=None` → Indeterminado, nunca `Rechazado` (FR-013).
- `adapters/agent_client_factory.py` (nuevo): `AgentClientFactory.create(config) -> AgentClient` centraliza el condicional de creación y la resolución del `CredentialProvider` (FR-005); expone `resolve_credentials` para la validación anticipada del dashboard.
- `adapters/token_provider.py`: `StaticCredentialProvider` (llave fija, sin ciclo de token).
- `dashboard/app.py` y `runner.py`: composition roots cableados vía factory; anotaciones relajadas al puerto `AgentClient` (FR-008); el runner reporta config inválida por stderr con exit 1 en vez de traceback.
- `.env.example`: documenta `AGENT_CLIENT_TYPE` y las `ALT_CLIENT_*`.
- `docs/ARCHITECTURE.md` (ADR-001 y sección adapters) reconciliado con la selección por configuración.

**Decisiones tomadas:**
- Discriminador del corto-circuito precisado en FR-011: bloque final **presente con `null`** (la clave existe en ambas ramas, verificado empíricamente); body sin la clave = forma inesperada → fallo técnico (FR-013). Evita mapear respuestas anómalas a `Rechazado` (Principio III).
- `AGENT_ID` opcional para `sync_http` (metadata de corridas; fallback a la etiqueta del tipo de cliente).
- FR-007 (SDKs de terceros) no se ejerció: el adaptador usa `requests`, ya presente; sin dependencias nuevas.

**Deuda arrastrada / bloqueante de cierre:** SC-001..003 confirmados por la suite automatizada. Se agregó **SC-004** (prueba funcional manual del usuario, requisito de cierre de toda spec): validar contra la plataforma alternativa real (`AGENT_CLIENT_TYPE=sync_http` + `ALT_CLIENT_URL` + `ALT_CLIENT_API_KEY` en el entorno) y re-validar el camino original por defecto. Con el OK del usuario se tilda SC-004 y la spec pasa a `active`.

**[SDD-Check] — 2026-07-03**
- Specs leídas: SPEC-013-client-adapter-selection, SPEC-000-naming, SPEC-002-agent-client, SPEC-002b-message-builder, SPEC-003-classification-evaluator, CONSTITUTION.md, docs/ARCHITECTURE.md.
- Includes/excludes verificados: fuera de alcance respetado (sin soporte multi-cliente por corrida; `MessageBuilder` intacto); naming agnóstico en identificadores nuevos; `requests` confinado a `adapters/`; pipeline local VERDE (constitución, trazabilidad, ruff, mypy --strict, naming, lint-imports, bandit, pytest).
- SSOTs afectados: specs/SPEC-013-client-adapter-selection.md (draft, pend. validación funcional), specs/SPECS_REGISTRY.md, docs/ARCHITECTURE.md (ADR-001), .env.example, historial/sdd.md.

---

## 2026-07-03 — Cierre de SPEC-013: OK funcional del usuario, spec pasa a `active`

**Scope:** cierre de SPEC-013-client-adapter-selection. El usuario confirmó la prueba funcional manual (SC-004): un caso real con `AGENT_CLIENT_TYPE=sync_http` contra la plataforma alternativa devuelve veredicto correcto por el circuito completo, y el camino por defecto (sin la variable) sigue operando contra el proveedor original.

**Cambios:** SC-004 tildado en la spec; estado `draft` → `active` en la spec y en `SPECS_REGISTRY.md`. Sin cambios de código (solo cierre documental).

**[SDD-Check] — 2026-07-03 (cierre SPEC-013)**
- Specs leídas: SPEC-013-client-adapter-selection.
- Includes/excludes verificados: SC-001..004 confirmados (los tres primeros por suite automatizada, SC-004 por OK explícito del usuario); sin cambios de comportamiento.
- SSOTs afectados: specs/SPEC-013-client-adapter-selection.md (active), specs/SPECS_REGISTRY.md, historial/sdd.md.

---

## 2026-07-07 — Refactor de capas (ADR-005): sin orquestación duplicada ni conocimiento de formato en los composition roots

**Scope:** auditoría de capas sobre `dashboard/` y `runner.py` (pedido del usuario) detectó dos violaciones semánticas de ADR-005 (los imports estaban limpios; import-linter no las ve porque los composition roots pueden importar de todo) y una duplicación SSOT menor. Se corrigieron las tres:

1. **SPEC-003** — `_send_and_evaluate` (dashboard, flujo simple) duplicaba paso a paso la orquestación de `application.run_one` (send → wait → get_final_response → evaluate → traza). Ahora invoca `run_one` con el nuevo callback opcional `on_phase: PhaseCallback` (fases `"enviando"` / `"esperando_flow"`, traducidas a `ui.status`); `is_execution_failure()` (nuevo, `application/`) preserva el comportamiento previo ante fallos de ejecución (error en pantalla, sin persistir). Colaterales: la captura de traza del modo simple pasa por `_capture_trace` (un fallo de `get_trace` ya no aborta el flujo) y la traza queda adjunta al `TestResult` persistido, como en batch.
2. **SPEC-004 FR-007** — la detección/inyección de `clasificacion_esperada` (conocimiento del formato del archivo, con `import json`) vivía en `dashboard/app.py`; se movió a `build/case_loader.py` como `needs_expected_classification` / `with_expected_classification`. El dashboard conserva solo el selectbox. Tests renombrados: `test_dashboard_file_load.py` → `test_expected_classification.py`.
3. **SPEC-008 FR-010** — el título «Matriz de confusión — total (N corrida(s), M caso(s))» se construía idéntico en `runner.py` y `dashboard/app.py`; centralizado en `total_metrics_title(runs)` (`application/generate_metrics_report.py`).

**Decisiones:** se eligió el callback de fase (Opción B discutida con el usuario) sobre el spinner único, porque `wait_for_completion` puede tardar hasta 300 s y el feedback de fase es valioso; sigue el precedente de `ProgressCallback`. Los fallos de ejecución del modo simple se siguen mostrando sin persistir (sin cambio de comportamiento); la distinción se hace con `is_execution_failure`, no con string-matching en la UI.

**Deuda arrastrada:** ninguna nueva. Pendiente el OK funcional del usuario en la app real (dashboard: envío simple con y sin traza, carga de archivo sin `clasificacion_esperada`, botón de estadística; runner: `--estadistica`).

**[SDD-Check] — 2026-07-07**
- Specs leídas: SPEC-003-classification-evaluator, SPEC-004-single-case-file, SPEC-008-suite-metrics, SPEC-005-run-persistence, SPEC-006-batch-suite, SPEC-010-batch-trace, SPEC-000-naming, CONSTITUTION.md, docs/ARCHITECTURE.md (ADR-005).
- Includes/excludes verificados: sin cambio de comportamiento observable (mismos veredictos, misma persistencia, misma UX de error); naming agnóstico en identificadores nuevos (`needs_expected_classification`, `with_expected_classification`, `PhaseCallback`, `total_metrics_title`); `application/` sigue sin importar adapters/dashboard/runner; pipeline local VERDE 10/10 (290 tests).
- SSOTs afectados: specs/SPEC-003, SPEC-004, SPEC-008, specs/SPECS_REGISTRY.md, docs/ARCHITECTURE.md (ADR-005), historial/sdd.md.

---

## 2026-07-07 — Bootstrap automático de los hooks git (cambio de método, sin spec)

**Scope:** se detectó que en este clon nunca se había corrido `pre-commit install`, por lo que la capa git del enforcement (gate sdd en commit, linters, `sdd-reset` post-commit) estaba caída en silencio: `.sdd/current-spec` no se limpiaba tras el commit y ningún hook corría al commitear. git no permite auto-instalar hooks al clonar (por diseño), así que se enforza en el primer punto de contacto garantizado del tooling.

**Cambios:** (1) instalación manual inmediata (`python -m pre_commit install --hook-type pre-commit --hook-type post-commit`) + `python tools/sdd_reset.py` para limpiar la declaración pendiente; (2) `tools/bootstrap_hooks.py` nuevo — idempotente, verifica primero si los hooks existen y solo instala los que faltan; no-op sin git; falla accionable sin el paquete `pre-commit`; usa `sys.executable -m pre_commit` (el binario no está en el PATH de este entorno); (3) cableado como **paso 0** de `tools/pipeline_local.sh` (`step "hooks git instalados"`, pipeline ahora 11 pasos): como el protocolo obliga a correr el pipeline en cada cierre, un clon nuevo queda reparado a más tardar en su primer pipeline, antes del primer commit; (4) documentado en `docs/SDD-ENFORCEMENT.md` §Mecanismo de "spec vigente".

**Decisiones:** se analizaron alternativas (hook SessionStart de Claude, chequeo dentro de `sdd_gate.py`, `core.hooksPath` versionado) y el usuario eligió solo la capa pipeline (opción A) con verificación previa de existencia. Auto-instalar en vez de fallar en rojo: el remedio es determinista, local e idempotente.

**Deuda arrastrada:** ninguna. Es cambio de framework/método (no toca `src/`): no requiere spec ni declaración en `.sdd/current-spec` (Principio V, ver SDD-ENFORCEMENT).

**[SDD-Check] — 2026-07-07 (bootstrap hooks)**
- Specs leídas: n/a (cambio de método; CONSTITUTION.md Principio V, docs/SDD-ENFORCEMENT.md).
- Includes/excludes verificados: idempotencia probada (no-op con hooks presentes; instala con hook faltante); pipeline local VERDE 11/11.
- SSOTs afectados: docs/SDD-ENFORCEMENT.md, tools/bootstrap_hooks.py (nuevo), tools/pipeline_local.sh, historial/sdd.md.

---

## 2026-07-07 — Cobertura del runner headless + PoC de tests de flujo del dashboard (AppTest vía driver agnóstico)

**Scope:** dos mejoras de cobertura de tests, sin tocar `src/`:

1. **`runner.py` de 66% → 99%** (`tests/unit/test_runner.py`, 8 tests nuevos): camino completo de `main` con config y factory stubeados (happy path con persistencia y `endpoint_url`, filas inválidas reportadas sin abortar, batch sin casos válidos, `MissingConfigError`, Ctrl+C con persistencia parcial y con cero casos), más las ramas de error de persistencia de `--estadistica` (corridas ilegibles; fallo al escribir el CSV sin perder el reporte a pantalla). Solo queda sin cubrir el guard `if __name__ == "__main__"`.
2. **PoC de tests de flujo del dashboard** (`tests/integration/`): `ui_driver.py` — driver agnóstico que maneja la app headless por labels visibles (`fill`/`mark`/`choose`/`press` + lecturas de errores/éxitos/estado); su único acople al framework web es el import de `AppTest`, misma estrategia que `import streamlit as ui` en `app.py`. `test_dashboard_flows.py` — 4 flujos del modo simple (SPEC-001/SPEC-003): formulario incompleto → error de validación; formulario válido → caso listo; config incompleta → error sin llamar al agente; camino feliz con runtime stubeado → PASS + corrida persistida.
3. **Fix de test desactualizado** (preexistente, detectado al correr `tests/integration` completo): `test_run_one_captura_traza_vacia_sin_fallar` esperaba `trace.steps == ()`, anterior a la síntesis de traza del pipeline síncrono (SPEC-013 FR-US3). Renombrado a `test_run_one_captura_la_traza_sintetizada_del_pipeline` y actualizado al contrato vigente (5 pasos en orden fijo, `overall_status == "completed"`).

**Decisiones:** los tests del dashboard van en `tests/integration` (arrancan la app completa) y no entran al pipeline (que corre solo `tests/unit`) — pendiente decidir si se agregan como paso. Prioridad a la agnosticidad (pedido del usuario): los tests localizan widgets por label visible, nunca por keys internas; un cambio de framework solo reescribe `ui_driver.py`. Limitación documentada: `AppTest` no simula `file_uploader`, así que el flujo batch de la UI queda cubierto por helpers puros + prueba funcional manual. No se persigue cobertura de rendering puro (sería cobertura vacía).

**Deuda arrastrada:** el test desactualizado evidenció que `tests/integration` no corre en ningún gate; decidir si entra al pipeline local.

**[SDD-Check] — 2026-07-07 (cobertura runner + PoC dashboard)**
- Specs leídas: SPEC-006-batch-suite, SPEC-008-suite-metrics, SPEC-001-single-case-input, SPEC-003-classification-evaluator, SPEC-013-client-adapter-selection, SPEC-000-naming.
- Includes/excludes verificados: solo tests (sin cambio de comportamiento en `src/`); naming agnóstico en identificadores nuevos del driver; pipeline local VERDE 11/11 (298 tests unit) y `tests/integration` 9/9.
- SSOTs afectados: historial/sdd.md (SPECS_REGISTRY sin cambios: ninguna spec cambió de estado).
