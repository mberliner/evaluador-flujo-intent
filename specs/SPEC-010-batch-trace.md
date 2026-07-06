# SPEC-010-batch-trace — Traza de ejecución por caso en corridas batch

**Estado:** active
**Iter:** 10 impl.2026-05-27
**Formato:** Híbrido
**Depende de:** [[SPEC-007-agent-trace]], [[SPEC-006-batch-suite]], [[SPEC-005-run-persistence]]
**Relacionada con:** [[SPEC-008-suite-metrics]]

**Resumen:** Da paridad de traza entre el modo simple ([[SPEC-007-agent-trace]]) y las corridas batch. Dos cortes: **US2** captura la traza en vivo durante la corrida y la persiste embebida en el run (P3, prerequisito); **US1** la muestra por caso en la revisión del run, sin invocar al agente (P3). El orden invertido lo impone el «Hallazgo de correlación»: la traza no es recuperable de forma confiable a posteriori. Ambas cerradas con verificación funcional (2026-05-27).

---

## Hallazgo de correlación (2026-05-27) — base de diseño de esta spec

Verificación empírica ligada al `[NEEDS CLARIFICATION]` de FR-008 de [[SPEC-007-agent-trace]] y documentada en `docs/AGENT-INVOCATION.md` (§3, §6). Los FR referencian esta sección en vez de repetir el detalle.

- El `conversation_id` que el detalle batch persiste por caso **es el `thread_id` del cliente**, y ese identificador **no aparece en `/flows`** (el flow usa `agent_thread_id`/`wxo_thread_id`, UUIDs distintos para la misma ejecución).
- `get_trace(thread_id)` (SPEC-007 FR-008) **no correlaciona por `thread_id`**: selecciona el flow `flow_async_chat` del `agent_id` **más reciente por timestamp**.
- **Consecuencia:** obtener la traza **a pedido, post-corrida** sobre un run ya guardado **no es confiable** — devolvería el flow más reciente del agente *en ese momento*, no el del caso. La heurística por recencia sólo es válida **en vivo**, inmediatamente después de ejecutar el caso (corrida secuencial). Por eso la traza por caso se **captura en vivo durante la corrida y se persiste** (User Story 2), y la vista (User Story 1) la **lee del run persistido**.
- El mismo hallazgo descarta el **backfill retroactivo** de runs ya guardados y el **re-fetch de refresco** en batch (el mecanismo de dos pasos del dashboard de SPEC-007 FR-012 se apoya en la recencia y deja de ser válido al avanzar al caso siguiente).

---

## Clarifications

### Session 2026-06-07

- Q: FR-US2-002 y Coverage nombraban `src/runner` para la captura, pero ADR-005 la movió a `src/application/run_suite.py`. → A: Spec actualizada al estado real (`run_one`/`_capture_trace` en `application/`); sin cambio de comportamiento. (FR-US2-002)
- Q: Con `concurrency>1` (SPEC-009) la captura por recencia atribuiría trazas a casos equivocados sin error. ¿FR-guard? → A: No por ahora — queda como Assumption (status quo). Habilitar `concurrency>1` exige antes resolver la correlación exacta `run_id→flow_id` (deuda de SPEC-007 FR-008) o introducir el guard en ese momento.

---

## User Story 1 — Ver la traza por caso de una corrida batch (Priority: P3)

Como evaluador de calidad, quiero ver la traza de ejecución de cualquier caso de una corrida batch **igual que en el modo simple**, para diagnosticar una clasificación inesperada sin volver a ejecutar el caso por separado, y poder abrir el flow correspondiente en la plataforma con su identificador.

**Why this priority:** extiende al flujo batch el valor diagnóstico de [[SPEC-007-agent-trace]]. No bloquea la ejecución batch (SPEC-006) ni las métricas (SPEC-008); evita reproducir manualmente en modo simple los casos sospechosos del lote. Depende de User Story 2 (ver «Hallazgo de correlación»).

**Independent Test:** sobre una corrida batch persistida **con su traza por caso** (capturada por US2), seleccionar un caso y ver su sección "Traza de ejecución" con al menos un paso (o "Traza no disponible"), reutilizando el panel de SPEC-007, sin recomputar métricas ni re-ejecutar el batch.

### Acceptance Scenarios

1. **Given** una corrida batch con traza persistida por caso, **When** selecciono un caso y expando "Traza de ejecución", **Then** veo los pasos leídos del run (capturados en vivo) renderizados por el panel de SPEC-007, junto con el `flow_id` para localizar el flow en la plataforma.
2. **Given** un caso cuya traza persistida no tiene pasos (`AgentTrace(steps=())`), **When** lo reviso, **Then** veo "Traza no disponible" sin que se interrumpa la navegación entre casos del batch.
3. **Given** un caso del run sin traza persistida (run anterior a esta capacidad o caso cuya captura falló), **When** intento ver su traza, **Then** la sección informa que la traza no está disponible, sin error en consola ni en UI.
4. **Given** la revisión de una corrida batch ya persistida, **When** expando la traza de cualquier caso, **Then** la traza se muestra **desde el run en disco sin invocar al agente**.

### Functional Requirements

- **FR-US1-001**: MUST: La traza por caso en batch reutiliza el modelo `AgentTrace`/`TraceStep` definido en SPEC-007; esta historia no define un modelo de traza propio.
- **FR-US1-002**: MUST: El render de la traza por caso reutiliza `src/dashboard/trace_panel.py` (SPEC-007); la vista de suite no duplica la lógica de presentación.
- **FR-US1-003**: MUST: La vista de resultados batch permite seleccionar un caso y ver, **a pedido**, su sección "Traza de ejecución" debajo del detalle del caso (SPEC-006), colapsada por defecto.
- **FR-US1-004**: MUST: La fuente de la traza por caso es la **traza persistida en el run** (User Story 2), no un fetch a pedido al agente; el `conversation_id` se conserva en el detalle como ancla del caso.
  > Resuelve el `[NEEDS CLARIFICATION]` original (2026-05-27): el fetch a pedido post-corrida quedó descartado por el «Hallazgo de correlación».
- **FR-US1-005**: MUST: Si la traza persistida no tiene pasos, o el caso no tiene traza persistida, la sección muestra "Traza no disponible" sin propagar excepción ni interrumpir la navegación (consistente con FR-009 de SPEC-007).
- **FR-US1-006**: MUST: La obtención de la traza para la vista ocurre **leyendo el run persistido** al expandir el caso; la revisión **no invoca al agente**. La captura efectiva ocurre en vivo durante la corrida (FR-US2-003).
- **FR-US1-007**: MUST: La vista muestra el `flow_id` del caso como **ancla para abrir el flow en la plataforma**. Si la traza persistida quedó en estado no terminal, la sección informa que el flow seguía cerrando tareas al capturarse y que el cierre completo se consulta por `flow_id` en la plataforma — **sin** botón de refresco (el re-fetch por recencia no es válido en batch, FR-US2-007).

### Key Entities

- **AgentTrace / TraceStep** (de SPEC-007): modelo de traza reutilizado; no se redefine.
- **`trace_panel`** (de SPEC-007, `src/dashboard/trace_panel.py`): componente de render reutilizado.
- **Detalle batch `run-<ts>.json`** (de SPEC-005/006, extendido por US2): fuente del `case_id` + `conversation_id` + traza persistida por caso.

### Success Criteria

- [x] **SC-US1-001**: sobre una corrida batch persistida con traza por caso, la traza de un caso se muestra reutilizando el panel de SPEC-007, con al menos un paso o el mensaje "Traza no disponible". Verificado funcionalmente por el usuario (2026-05-27).
- [x] **SC-US1-002**: la **revisión** de la traza por caso (post-corrida) se sirve desde el run en disco y **no genera ninguna llamada al agente**. Cubierto por construcción (`_render_case_trace` lee `r.trace`, no invoca al cliente) + verificación funcional.
- [x] **SC-US1-003**: verificación funcional en la app real — abro una corrida batch, expando un caso y veo su traza (o "Traza no disponible") y su `flow_id`, sin error en consola ni en UI. Confirmado por el usuario (2026-05-27).

### Assumptions

- SPEC-007 está implementada y estable (modelo, puerto `get_trace`, panel): esta historia la reutiliza, no la reimplementa.
- User Story 2 está entregada: el run persiste la traza por caso; sin ella US1 no tiene datos («Hallazgo de correlación»).
- La traza es diagnóstica: no altera el veredicto determinista (Constitución III), ni el accuracy, ni las métricas de suite (SPEC-008).

### Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-US1-001, FR-US1-005, SC-US1-001 | reutiliza modelo `AgentTrace`/`TraceStep` (SPEC-007); render de la vista batch (incl. traza vacía/ausente → "Traza no disponible") verificado **funcionalmente**, sin test unitario del render (UI, consistente con SPEC-007) |
| FR-US1-002 | reutiliza `src/dashboard/trace_panel.py` (SPEC-007) + verificación funcional |
| FR-US1-003 | integración en la vista de resultados batch de `src/dashboard/` + verificación funcional |
| FR-US1-004, FR-US1-006, SC-US1-002 | la revisión lee la traza persistida del run (US2); que no invoca al agente se garantiza **por construcción** (`_render_case_trace` lee `r.trace`, no recibe ni usa el cliente) + verificación funcional — sin test automatizado dedicado |
| FR-US1-007 | render del `flow_id` + nota de estado no terminal (sin botón de refresco) en la vista batch + verificación funcional |
| SC-US1-003 | verificación funcional en la app real |

### Fuera de alcance

- Modelo y panel de la traza → definidos en [[SPEC-007-agent-trace]]; aquí se **reutilizan**.
- Captura y persistencia de la traza junto al run → User Story 2 de esta spec.
- Métricas y agregados de suite → [[SPEC-008-suite-metrics]].
- Comparación de trazas del mismo caso entre runs y replay de pasos → fuera (consistente con SPEC-007).

---

## User Story 2 — Capturar y persistir la traza por caso en el batch (Priority: P3, prerequisito de US1 en batch)

Como evaluador, quiero que la traza de cada caso de una corrida batch se **capture en vivo durante la corrida y quede registrada junto al run**, para poder revisarla a posteriori —y abrir el flow en la plataforma por su `flow_id`— aunque el agente remoto ya no la exponga o ya no se pueda correlacionar.

**Why this priority:** por el «Hallazgo de correlación», la traza por caso en batch **sólo** es obtenible de forma confiable en vivo; por eso esta historia es **prerequisito** de US1. Es una extensión de [[SPEC-005-run-persistence]] y de la orquestación batch (SPEC-006).

**Independent Test:** ejecutado un batch, recargar el run desde disco y ver la traza de un caso (y su `flow_id`) sin invocar al agente.

### Acceptance Scenarios

1. **Given** un batch en ejecución, **When** termina cada caso, **Then** el runner captura la traza con `client.get_trace(thread_id)` inmediatamente (mientras el flow del caso es el más reciente) y la asocia al resultado del caso.
2. **Given** un batch ejecutado, **When** recargo el run desde disco, **Then** la traza de cada caso (con su `flow_id`) está disponible sin llamar al agente.
3. **Given** una traza persistida y el agente remoto fuera de línea, **When** reviso el caso, **Then** la traza histórica se muestra desde el run.
4. **Given** un caso cuya captura de traza falló o devolvió `AgentTrace(steps=())`, **When** se persiste el run, **Then** el caso se guarda igual (traza nula/vacía) sin abortar la corrida ni los demás casos (consistente con SPEC-006 FR-006 y SPEC-007 FR-009).

### Functional Requirements

- **FR-US2-001**: MUST: La traza por caso se **embebe en el detalle del caso** dentro de `run-<ts>.json`, reutilizando `AgentTrace`/`TraceStep` como estructura. La serialización a `dict` puede vivir en `domain/` (código puro); la escritura a disco vive en `adapters/` (`FileRunRepository`).
  > Decisión 2026-05-27 (resuelve el `[NEEDS CLARIFICATION]` de estructura): traza **embebida**, no artefacto separado — se correlaciona con su caso **por contención** (es un campo del `TestResult`, junto a su `case_id`/`conversation_id`); un artefacto aparte agregaría un join externo sin beneficio.
- **FR-US2-002**: MUST: La captura ocurre en el use-case de orquestación (`src/application/run_suite.py`, `run_one`/`_capture_trace`) **en vivo**, tras `wait_for_completion` de cada caso, con `client.get_trace(thread_id)`; el use-case recibe el puerto `AgentClient` por parámetro y `domain/` no realiza I/O ni conoce el shape del proveedor (Principio II; ADR-005). El composition root (`src/runner.py`) invoca el use-case pero no contiene la captura.
- **FR-US2-007**: MUST: La captura es un **único** `get_trace(thread_id)` por caso: sin poll hasta estado terminal ni segundo fetch de cierre; la traza se persiste **tal cual**, incluido un `overall_status` no terminal. El `flow_id` capturado es el **ancla confiable**: el cierre completo del flow se consulta abriendo ese `flow_id` en la plataforma, no re-consultando desde la suite.
  > Decisión «cierre del flow» 2026-05-27 (opción C): por el timing de SPEC-007 FR-012, el fetch puede registrar el flow no terminal porque la cola final cierra después de depositar la clasificación. El botón "Actualizar traza" del dashboard no se replica en batch: su refresh se apoya en la recencia de `/flows` («Hallazgo de correlación»). Descartadas: A (poll hasta terminal — alarga la corrida) y B (refresh post-corrida por `flow_id` — requiere método nuevo y falla con lotes >~50 por la ventana de `/flows`).
- **FR-US2-003**: MUST: El resultado por caso (`TestResult`, SPEC-005) se extiende para portar la traza capturada (campo opcional con default, sin romper el round-trip `save→load` ni los llamadores existentes); `to_dict()`/`from_dict()` serializan y reconstruyen la traza embebida.
- **FR-US2-004**: MUST: La revisión a posteriori lee la traza del run y **no** re-consulta al agente (la fuente de FR-US1-004); no hay fallback de fetch a pedido en batch.
- **FR-US2-005**: MUST: Un fallo o vacío al capturar la traza de un caso no aborta la corrida ni los demás casos; el caso se persiste con traza nula/vacía (consistente con SPEC-006 FR-006 y SPEC-007 FR-009).
- **FR-US2-006**: MUST: invariante [[SPEC-000-naming]] — `flow_id`, `trace`, `agent_trace` son nombres agnósticos válidos.

### Key Entities

- **AgentTrace / TraceStep** (de SPEC-007): modelo reutilizado como estructura capturada y persistida.
- **`TestResult`** (de SPEC-005, `src/domain/result.py`): extendido con la traza por caso (campo opcional).
- **Detalle batch `run-<ts>.json`** (de SPEC-005/006): extendido con la traza por caso embebida en cada caso.

### Success Criteria

- [x] **SC-US2-001**: con la captura activa, la traza de un caso se recupera desde un run en disco sin invocar al agente (round-trip `save→load` de la traza, incluido el `flow_id`). Cubierto por `test_round_trip_preserves_trace_on_disk`.
- [x] **SC-US2-002**: el round-trip `save→load` de runs **sin** traza (anteriores a esta capacidad, o casos con traza nula) sigue funcionando. Cubierto por `test_result_without_trace_serializes_none` + regresión de runs existentes.
- [x] **SC-US2-003**: verificación funcional en la app real — ejecuto un batch, recargo el run desde disco y veo la traza histórica de un caso (y su `flow_id`) sin que se llame al agente. Confirmado por el usuario (2026-05-27).

### Assumptions

- SPEC-007 está implementada y estable: la captura usa el puerto `get_trace` y el modelo existentes.
- La extensión del esquema de run (SPEC-005) no rompe el round-trip `save→load` de los runs sin traza.
- La captura en vivo agrega una llamada `/flows` por caso durante el batch — costo aceptado deliberadamente a cambio de un `flow_id` correlacionado correcto; se concentra en la corrida, no en la revisión.
- La captura por recencia (FR-US2-007) asume ejecución **secuencial** (`concurrency=1`). Bajo [[SPEC-009-parallel-execution]] con `concurrency>1` deja de correlacionar; habilitar paralelismo requiere antes resolver la correlación exacta `run_id → flow_id` (deuda de SPEC-007 FR-008) o un guard (ver Clarifications).

### Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-US2-001, FR-US2-003, SC-US2-001, SC-US2-002 | extensión de `TestResult` (`src/domain/result.py`) + `to_dict`/`from_dict` + extensión de `FileRunRepository` (SPEC-005) + tests round-trip (save→load) con y sin traza por caso |
| FR-US2-002 | captura en `src/application/run_suite.py` (`run_one`/`_capture_trace`) tras `wait_for_completion`, ejercitada vía la fachada `runner.run_batch` en `tests/unit/test_runner.py` (`test_run_batch_captures_trace_per_case`) + `import-linter` |
| FR-US2-007 | test: un único `get_trace` por caso (sin poll); traza no terminal se persiste tal cual |
| FR-US2-004 | test que recarga un run con traza persistida y la muestra sin invocar al agente |
| FR-US2-005 | test: `get_trace` que falla/vacío → caso persistido con traza nula, corrida no abortada |
| FR-US2-006 | `tools/check_naming.py` |
| SC-US2-003 | verificación funcional en la app real |

### Fuera de alcance

- Modelo y panel de la traza → definidos en [[SPEC-007-agent-trace]]; aquí se **reutilizan**.
- Re-correlación exacta `run_id → flow instance_id` (estrechar el fallback de SPEC-007 FR-008) → sigue siendo deuda de SPEC-007.
- Comparación de trazas del mismo caso entre runs y replay de pasos → fuera (consistente con SPEC-007).
- Métricas y agregados de suite → [[SPEC-008-suite-metrics]].

---

## Historial

- **2026-05-27** — Spec creada para dar paridad de traza entre modo simple (SPEC-007) y batch, como spec dedicada (decisión del usuario) en vez de historias dentro de 007/008. US1 vista por caso; US2 persistencia (entonces P4, deseable). `[NEEDS CLARIFICATION]` en correlación (FR-US1-004) y estructura de persistencia (FR-US2-001).
- **2026-05-27** — Revisión de diseño: resueltos ambos `[NEEDS CLARIFICATION]` con verificación empírica → «Hallazgo de correlación». **Se invirtió el supuesto original**: la traza se captura en vivo y se persiste (US2 sube a P3, prerequisito); US1 la lee del run. Traza embebida en el detalle del caso; backfill retroactivo descartado. Motivación de usuario: persistir el `flow_id` por caso para abrir el flow en la plataforma.
- **2026-05-27** — Decisión de cierre del flow: **captura única** en vivo por caso, traza persistida tal cual aunque quede no terminal, `flow_id` como ancla (opción C del usuario; ver nota de FR-US2-007). Nuevos FR-US2-007 y FR-US1-007.
- **2026-05-27** — Implementada y cerrada (`draft`→`active`): `TestResult.trace`/`flow_id` + round-trip, captura resiliente `_capture_trace`, vista batch con `flow_id` y traza a pedido. Pipeline 8/8 (188 tests); verificación funcional del usuario OK — confirma empíricamente que en batch secuencial la recencia de `/flows` trae el flow del caso recién corrido. Deuda no bloqueante: incompatibilidad con SPEC-009 (paralelo) en Assumptions; el modo simple (SPEC-007) sigue sin persistir la traza.
- **2026-06-07** — Por [ADR-005](../docs/ARCHITECTURE.md) la captura `run_one`/`_capture_trace` se movió de `src/runner` a `src/application/run_suite.py`; FR-US2-002 y Coverage actualizados. Sin cambio de comportamiento (ver Clarifications).
- **2026-06-07** — `/analyze`: exactitud del Coverage mapping — filas que citaban tests inexistentes se corrigieron a "por construcción + verificación funcional" (FR-US1-004/006, SC-US1-002) y "verificación funcional sin unit test de render" (FR-US1-001/005, SC-US1-001); FR-US2-001 "por posición" → "por contención". Deuda viva: guard de concurrencia a anclar en [[SPEC-009-parallel-execution]].
- **2026-07-05** — Reescritura editorial al formato compacto (convenciones de `docs/SPEC-FORMAT.md`): el «Hallazgo de correlación» queda como referencia única (antes re-explicado en FR-US1-004, Why-priority, Assumptions e Historial), decisiones movidas a notas `>`, coverage agrupado, historial podado. **Sin cambio normativo**: IDs de FR/SC y su semántica intactos.
