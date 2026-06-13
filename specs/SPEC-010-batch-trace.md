# SPEC-010-batch-trace — Traza de ejecución por caso en corridas batch

**Estado:** active
**Iter:** 10 impl.2026-05-27
**Formato:** Híbrido
**Depende de:** [[SPEC-007-agent-trace]], [[SPEC-006-batch-suite]], [[SPEC-005-run-persistence]]
**Relacionada con:** [[SPEC-008-suite-metrics]]

---

## Hallazgo de correlación (2026-05-27) — base de diseño de esta spec

Verificación empírica ligada al `[NEEDS CLARIFICATION]` de FR-008 de [[SPEC-007-agent-trace]] y documentada en `docs/AGENT-INVOCATION.md` (§3, §6):

- El `conversation_id` que el detalle batch persiste por caso **es el `thread_id` del cliente**, y ese identificador **no aparece en `/flows`** (el flow usa `agent_thread_id`/`wxo_thread_id`, UUIDs distintos para la misma ejecución).
- `get_trace(thread_id)` (SPEC-007 FR-008) **no correlaciona por `thread_id`**: selecciona el flow `flow_async_chat` del `agent_id` **más reciente por timestamp**.

**Consecuencia:** obtener la traza **a pedido, post-corrida** sobre un run ya guardado **no es confiable** — devolvería el flow más reciente del agente *en ese momento*, no el del caso. La heurística por recencia sólo es válida **en vivo**, inmediatamente después de ejecutar el caso (corrida secuencial: el flow más reciente del agente es el del caso recién corrido). Por eso esta spec invierte el supuesto original: la traza por caso se **captura en vivo durante la corrida y se persiste** (User Story 2), y la vista (User Story 1) la **lee del run persistido**, no la re-consulta al agente.

---

## Clarifications

### Session 2026-06-07

- Q: FR-US2-002 y Coverage nombran `src/runner` para la captura, pero el código y ADR-005 la movieron a `src/application/run_suite.py`, y el Historial 2026-06-07 la marcaba "pendiente" pese a estar hecha. ¿Cómo se reconcilia? → A: Actualizar la spec al estado real: FR-US2-002 y Coverage apuntan a `src/application/run_suite.py` (`run_one`/`_capture_trace`); el Historial corrige que la migración ADR-005 ya está implementada. Sin cambio de comportamiento (captura única en vivo, secuencial, tras `wait_for_completion`).
- Q: Con `concurrency>1` (SPEC-009) la captura por recencia atribuiría trazas a casos equivocados sin error. ¿Se agrega un FR-guard que la desactive/falle? → A: No por ahora — se mantiene como Assumption (status quo). El riesgo de trazas mal atribuidas bajo paralelismo queda como deuda conocida: habilitar `concurrency>1` exige antes resolver la correlación exacta `run_id→flow_id` (deuda de SPEC-007 FR-008) o introducir el guard en ese momento. Decisión consciente de no anticipar el invariante hasta implementar SPEC-009.

---

## User Story 1 — Ver la traza por caso de una corrida batch (Priority: P3)

Como evaluador de calidad, quiero ver la traza de ejecución de cualquier caso de una corrida batch **igual que en el modo simple**, para diagnosticar una clasificación inesperada sin volver a ejecutar el caso por separado, y poder abrir el flow correspondiente en la plataforma con su identificador.

**Why this priority:** extiende al flujo batch el valor diagnóstico de [[SPEC-007-agent-trace]] (hoy disponible sólo para un caso simple). No bloquea la ejecución batch (SPEC-006) ni las métricas (SPEC-008), que son el valor central; evita tener que reproducir manualmente en modo simple los casos sospechosos del lote. En batch, la traza por caso **depende de la captura+persistencia de User Story 2**, porque la traza no es recuperable de forma confiable a posteriori (ver "Hallazgo de correlación").

**Independent Test:** sobre una corrida batch persistida **con su traza por caso** (capturada por US2), seleccionar un caso y ver su sección "Traza de ejecución" con al menos un paso (o "Traza no disponible"), reutilizando el panel de SPEC-007, sin recomputar métricas ni re-ejecutar el batch.

### Acceptance Scenarios

1. **Given** una corrida batch con traza persistida por caso, **When** selecciono un caso y expando "Traza de ejecución", **Then** veo los pasos leídos del run (capturados en vivo) renderizados por el panel de SPEC-007, junto con el `flow_id` para localizar el flow en la plataforma.
2. **Given** un caso cuya traza persistida no tiene pasos (`AgentTrace(steps=())`), **When** lo reviso, **Then** veo "Traza no disponible" sin que se interrumpa la navegación entre casos del batch.
3. **Given** un caso del run sin traza persistida (run anterior a esta capacidad o caso cuya captura falló), **When** intento ver su traza, **Then** la sección informa que la traza no está disponible para ese caso, sin error en consola ni en UI.
4. **Given** la revisión de una corrida batch ya persistida, **When** expando la traza de cualquier caso, **Then** la traza se muestra **desde el run en disco sin invocar al agente** (la captura ocurrió en vivo durante la corrida, no en la revisión).

### Functional Requirements

- **FR-US1-001**: MUST: La traza por caso en batch reutiliza el modelo `AgentTrace`/`TraceStep` definido en SPEC-007; esta historia no define un modelo de traza propio.
- **FR-US1-002**: MUST: El render de la traza por caso reutiliza `src/dashboard/trace_panel.py` (SPEC-007); la vista de suite no duplica la lógica de presentación de la traza.
- **FR-US1-003**: MUST: La vista de resultados batch permite seleccionar un caso y ver, **a pedido**, su sección "Traza de ejecución" debajo del detalle del caso (esperado/detectado/veredicto/respuesta cruda ya provistos por SPEC-006), colapsada por defecto.
- **FR-US1-004**: MUST: La fuente de la traza por caso es la **traza persistida en el run** (User Story 2), no un fetch a pedido al agente. **Decisión (resuelve el `[NEEDS CLARIFICATION]` previo, 2026-05-27):** verificación empírica confirmó que el `conversation_id` persistido es el `thread_id` del cliente, que **no aparece en `/flows`**, y que `get_trace()` selecciona por recencia, no por `thread_id` (ver "Hallazgo de correlación" y SPEC-007 FR-008). Por lo tanto **un fetch a pedido post-corrida no recupera de forma confiable la traza del caso** y queda descartado como mecanismo en batch. El `conversation_id` se conserva en el detalle como ancla del caso; la traza correcta se obtiene de la captura en vivo (US2).
- **FR-US1-005**: MUST: Si la traza persistida no tiene pasos, o el caso no tiene traza persistida, la sección muestra "Traza no disponible" sin propagar excepción ni interrumpir la navegación entre casos del batch (consistente con FR-009 de SPEC-007).
- **FR-US1-006**: MUST: La obtención de la traza para la vista ocurre **leyendo el run persistido** al expandir el caso (post-corrida); la revisión **no invoca al agente**. La captura efectiva de la traza ocurre en vivo durante la corrida (User Story 2 / FR-US2-003), no en la revisión.
- **FR-US1-007**: MUST: La vista muestra el `flow_id` del caso como **ancla para abrir el flow en la plataforma**. Si la traza persistida quedó en estado no terminal (`overall_status` distinto de `completed`/`failed`), la sección informa que el flow seguía cerrando tareas al capturarse y que el cierre completo se consulta por `flow_id` en la plataforma —**sin** ofrecer un botón de refresco (el re-fetch por recencia no es válido en batch, ver FR-US2-007).

### Key Entities

- **AgentTrace / TraceStep** (de SPEC-007): modelo de traza reutilizado; no se redefine.
- **`trace_panel`** (de SPEC-007, `src/dashboard/trace_panel.py`): componente de render reutilizado para mostrar la traza por caso.
- **Detalle batch `run-<ts>.json`** (de SPEC-005/006, extendido por US2): fuente del `case_id` + `conversation_id` + traza persistida por caso.

### Success Criteria

- [x] **SC-US1-001**: sobre una corrida batch persistida con traza por caso, la traza de un caso se muestra reutilizando el panel de SPEC-007, con al menos un paso o el mensaje "Traza no disponible". Verificado funcionalmente por el usuario (2026-05-27).
- [x] **SC-US1-002**: la **revisión** de la traza por caso (post-corrida) se sirve desde el run en disco y **no genera ninguna llamada al agente**; expandir un caso no consulta `/flows` ni `/threads`. Cubierto por construcción (`_render_case_trace` lee `r.trace`, no invoca al cliente) + verificación funcional.
- [x] **SC-US1-003**: verificación funcional en la app real — abro una corrida batch, expando un caso y veo su traza (o "Traza no disponible") y su `flow_id`, sin error en consola ni en UI. Confirmado por el usuario (2026-05-27).

### Assumptions

- SPEC-007 está implementada y estable (modelo `AgentTrace`/`TraceStep`, puerto `get_trace`, panel `trace_panel`): esta historia la reutiliza, no la reimplementa.
- User Story 2 está entregada: el run persiste la traza por caso. En batch no hay fetch a pedido confiable (ver "Hallazgo de correlación"), por lo que US1 depende de US2 para tener datos.
- La traza es diagnóstica: no altera el veredicto determinista (Constitución III), ni el accuracy, ni las métricas de suite (SPEC-008).

### Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-US1-001, FR-US1-005 | reutiliza modelo `AgentTrace`/`TraceStep` (SPEC-007); render de la vista batch (incl. traza vacía/ausente → "Traza no disponible") **verificado funcionalmente** (SC-US1-001/003), sin test unitario del render (UI, consistente con SPEC-007) |
| FR-US1-002 | reutiliza `src/dashboard/trace_panel.py` (SPEC-007) + verificación funcional |
| FR-US1-003 | integración en la vista de resultados batch de `src/dashboard/` + verificación funcional |
| FR-US1-004, FR-US1-006 | la revisión lee la traza persistida del run (US2); que **no invoca al agente** se garantiza **por construcción** (`_render_case_trace` lee `r.trace`, no recibe ni usa el cliente) + verificación funcional — no hay test automatizado dedicado |
| FR-US1-007 | render del `flow_id` + nota de estado no terminal (sin botón de refresco) en la vista batch + verificación funcional |
| SC-US1-001 | verificación funcional en la app real (render del panel de traza de SPEC-007 sobre un caso del run batch) |
| SC-US1-002 | por construcción (`_render_case_trace` no recibe el cliente) + verificación funcional — no hay test automatizado que cuente llamadas al agente |
| SC-US1-003 | verificación funcional en la app real |

### Fuera de alcance

- Modelo y panel de la traza → definidos en [[SPEC-007-agent-trace]]; aquí se **reutilizan**, no se redefinen.
- Captura y persistencia de la traza junto al run → User Story 2 de esta spec.
- Métricas y agregados de suite (matriz de confusión, accuracy por clase) → [[SPEC-008-suite-metrics]].
- Comparación de trazas del mismo caso entre runs y replay de pasos → fuera (consistente con SPEC-007).

---

## User Story 2 — Capturar y persistir la traza por caso en el batch (Priority: P3, prerequisito de US1 en batch)

Como evaluador, quiero que la traza de cada caso de una corrida batch se **capture en vivo durante la corrida y quede registrada junto al run**, para poder revisarla a posteriori —y abrir el flow en la plataforma por su `flow_id`— aunque el agente remoto ya no la exponga o ya no se pueda correlacionar.

**Why this priority:** dado el "Hallazgo de correlación", la traza por caso en batch **sólo** es obtenible de forma confiable en vivo; un fetch a posteriori no correlaciona. Por eso esta historia deja de ser "deseable independiente" y pasa a ser **prerequisito** de la traza batch (US1). Es una extensión de [[SPEC-005-run-persistence]] y de la captura en `src/runner` (SPEC-006).

**Independent Test:** ejecutado un batch, recargar el run desde disco y ver la traza de un caso (y su `flow_id`) sin invocar al agente.

### Acceptance Scenarios

1. **Given** un batch en ejecución, **When** termina cada caso, **Then** el runner captura la traza con `client.get_trace(thread_id)` inmediatamente (mientras el flow del caso es el más reciente) y la asocia al resultado del caso.
2. **Given** un batch ejecutado, **When** recargo el run desde disco, **Then** la traza de cada caso (con su `flow_id`) está disponible sin llamar al agente.
3. **Given** una traza persistida y el agente remoto fuera de línea, **When** reviso el caso, **Then** la traza histórica se muestra desde el run.
4. **Given** un caso cuya captura de traza falló o devolvió `AgentTrace(steps=())`, **When** se persiste el run, **Then** el caso se guarda igual (traza nula/vacía) sin abortar la corrida ni los demás casos (consistente con SPEC-006 FR-006 y SPEC-007 FR-009).

### Functional Requirements

- **FR-US2-001**: MUST: La traza por caso se **embebe en el detalle del caso** dentro de `run-<ts>.json`, reutilizando `AgentTrace`/`TraceStep` como estructura. **Decisión (resuelve el `[NEEDS CLARIFICATION]` previo, 2026-05-27):** traza **embebida** (no artefacto separado), porque la traza se correlaciona con su caso **por contención** (es un campo del `TestResult` del caso, junto a su `case_id`/`conversation_id`), no por un join externo; un artefacto aparte agregaría ese join sin beneficio. La serialización a `dict` puede vivir en `domain/` (código puro, sin I/O); la escritura a disco vive en `adapters/` (`FileRunRepository`).
- **FR-US2-002**: MUST: La captura de la traza ocurre en el use-case de orquestación (`src/application/run_suite.py`, `run_one`/`_capture_trace`) **en vivo**, tras `wait_for_completion` de cada caso, con `client.get_trace(thread_id)`; el use-case recibe el puerto `AgentClient` por parámetro (no cablea adapters concretos) y `domain/` no realiza I/O ni conoce el shape del proveedor (Principio II — capas limpias; ADR-005). El composition root (`src/runner.py`) invoca el use-case pero no contiene la captura.
- **FR-US2-007**: MUST: La captura es un **único** `get_trace(thread_id)` por caso; no se hace poll hasta estado terminal ni un segundo fetch de cierre. **Decisión (cierre del flow, 2026-05-27):** por el timing de SPEC-007 FR-012, ese fetch puede registrar el flow en estado no terminal (`interrupted`/`in_progress`) porque la cola final (`actualizar_iniciativa`, `send_mail`, `__flow_end__`) cierra después de depositar la clasificación. La traza se persiste **tal cual** (incluido el estado no terminal). El mecanismo de "dos pasos" del dashboard (botón "Actualizar traza" → re-`get_trace(thread_id)`) **no se replica en batch**, porque su refresh se apoya en la recencia de `/flows` y deja de ser válido al avanzar al caso siguiente (ver "Hallazgo de correlación"). El `flow_id` capturado es el **ancla confiable**: el estado/cierre completo del flow se consulta abriendo ese `flow_id` en la plataforma, no re-consultando desde la suite.
- **FR-US2-003**: MUST: El resultado por caso (`TestResult`, SPEC-005) se extiende para portar la traza capturada (campo opcional con default, sin romper el round-trip `save→load` ni los llamadores existentes); `to_dict()`/`from_dict()` serializan y reconstruyen la traza embebida.
- **FR-US2-004**: MUST: La revisión a posteriori lee la traza del run y **no** re-consulta al agente (la fuente de FR-US1-004); no hay fallback de fetch a pedido en batch.
- **FR-US2-005**: MUST: Un fallo o vacío al capturar la traza de un caso no aborta la corrida ni los demás casos; el caso se persiste con traza nula/vacía (consistente con SPEC-006 FR-006 y SPEC-007 FR-009).
- **FR-US2-006**: MUST: Ningún identificador de código nombra el formato de serialización (`json`, `csv`) ni el framework de UI ni el proveedor (SPEC-000-naming). `flow_id`, `trace`, `agent_trace` son nombres agnósticos válidos.

### Key Entities

- **AgentTrace / TraceStep** (de SPEC-007): modelo reutilizado como estructura capturada y persistida; no se redefine.
- **`TestResult`** (de SPEC-005, `src/domain/result.py`): extendido con la traza por caso (campo opcional).
- **Detalle batch `run-<ts>.json`** (de SPEC-005/006): extendido con la traza por caso embebida en cada caso.

### Success Criteria

- [x] **SC-US2-001**: con la captura activa, la traza de un caso se recupera desde un run en disco sin invocar al agente (round-trip `save→load` de la traza, incluido el `flow_id`). Cubierto por `test_round_trip_preserves_trace_on_disk`.
- [x] **SC-US2-002**: el round-trip `save→load` de runs **sin** traza (anteriores a esta capacidad, o casos con traza nula) sigue funcionando sin romperse. Cubierto por `test_result_without_trace_serializes_none` + regresión de runs existentes.
- [x] **SC-US2-003**: verificación funcional en la app real — ejecuto un batch, recargo el run desde disco y veo la traza histórica de un caso (y su `flow_id`) sin que se llame al agente. Confirmado por el usuario (2026-05-27).

### Assumptions

- SPEC-007 está implementada y estable: la captura usa el puerto `get_trace` y el modelo existentes.
- La extensión del esquema de run (SPEC-005) se hace sin romper el round-trip `save→load` existente de los runs sin traza.
- La captura en vivo agrega una llamada `/flows` por caso durante el batch (costo aceptado deliberadamente a cambio de un `flow_id` correlacionado de forma correcta); este costo se concentra en la corrida, no en la revisión.
- La captura en vivo por recencia (FR-US2-007) asume ejecución **secuencial** (`concurrency=1`): hoy `run_batch` es secuencial y el flow más reciente del agente al terminar un caso es el de ese caso. Bajo [[SPEC-009-parallel-execution]] con `concurrency>1`, la selección por recencia de `/flows` deja de correlacionar el flow con su caso; habilitar paralelismo requiere antes resolver la correlación exacta `run_id → flow_id` (deuda de SPEC-007 FR-008).

### Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-US2-001, FR-US2-003 | extensión de `TestResult` (`src/domain/result.py`) + `to_dict`/`from_dict` + extensión de `FileRunRepository` (SPEC-005) + test round-trip de la traza persistida |
| FR-US2-002 | captura en `src/application/run_suite.py` (`run_one`/`_capture_trace`) tras `wait_for_completion`, ejercitada vía la fachada `runner.run_batch` en `tests/unit/test_runner.py` (`test_run_batch_captures_trace_per_case`) + `import-linter` (domain/application no hacen I/O ni importan adapters concretos) |
| FR-US2-007 | test: un único `get_trace` por caso (sin poll); traza no terminal se persiste tal cual |
| FR-US2-004 | test que recarga un run con traza persistida y la muestra sin invocar al agente |
| FR-US2-005 | test: `get_trace` que falla/vacío → caso persistido con traza nula, corrida no abortada |
| FR-US2-006 | `tools/check_naming.py` |
| SC-US2-001, SC-US2-002 | test round-trip (save→load) con y sin traza por caso |
| SC-US2-003 | verificación funcional en la app real |

### Fuera de alcance

- Modelo y panel de la traza → definidos en [[SPEC-007-agent-trace]]; aquí se **reutilizan**.
- Re-correlación exacta `run_id → flow instance_id` (estrechar el fallback de SPEC-007 FR-008) → sigue siendo deuda de SPEC-007; esta spec se apoya en la captura en vivo por recencia.
- Comparación de trazas del mismo caso entre runs y replay de pasos → fuera (consistente con SPEC-007).
- Métricas y agregados de suite → [[SPEC-008-suite-metrics]].

---

## Historial

- **2026-05-27** — Spec creada. Motivación: dar **paridad** a la traza entre el modo simple (SPEC-007) y las corridas batch, sin recargar el scope de SPEC-007 (deliberadamente "un caso") ni el de SPEC-008 (métricas). Decisión del usuario: spec dedicada en vez de historias dentro de 007/008, con cada HU encapsulada de inicio a fin (Acceptance/FR/Key Entities/SC/Assumptions/Coverage/Fuera de alcance propios) y numeración de FR/SC prefijada por HU. US1 (P3) traza por caso a pedido reutilizando modelo, puerto y panel de SPEC-007; US2 (P4, deseable) persistencia de la traza como extensión de SPEC-005. `[NEEDS CLARIFICATION]` en FR-US1-004 (correlación `conversation_id` ↔ `thread_id`) y FR-US2-001 (estructura de persistencia), a resolver al implementar.
- **2026-05-27** — Revisión de diseño (rev.2026-05-27). Resueltos ambos `[NEEDS CLARIFICATION]` con verificación empírica (ver "Hallazgo de correlación" y `docs/AGENT-INVOCATION.md` §3/§6): (1) el `conversation_id` persistido es el `thread_id` del cliente, que **no aparece en `/flows`**, y `get_trace()` correlaciona por recencia, no por `thread_id` → un fetch a pedido post-corrida **no es confiable**; (2) la traza se persiste **embebida** en el detalle del caso, no como artefacto separado. Consecuencia: **se invirtió el supuesto original** — la traza por caso se **captura en vivo durante la corrida y se persiste** (US2, ahora prerequisito), y US1 la **lee del run** sin invocar al agente. Cambios: US1 FR-US1-004/FR-US1-006 y SC-US1-002 reescritos (revisión sin llamadas al agente; la captura es en vivo); Acceptance Scenarios de US1 actualizados; US2 sube a P3 (prerequisito), agrega captura en `src/runner` (FR-US2-002), extensión de `TestResult` (FR-US2-003) y manejo de fallo/vacío (FR-US2-005). Motivación de usuario: persistir el `flow_id` por caso para abrir el flow en la plataforma; el backfill retroactivo de runs ya guardados se descartó por el mismo hallazgo de correlación. Pendiente: implementación (TestResult + runner + FileRunRepository + vista batch) y SC funcionales.
- **2026-05-27** — Implementada y cerrada (`draft`→`active`). US2 (captura+persistencia) y US1 (vista) entregadas: `from_dict` en `agent_trace`, `TestResult.trace`/`flow_id` + round-trip en `result`, captura única en vivo en `runner.run_one` (`_capture_trace`, resiliente), vista batch en `dashboard/app.py` (`flow_id` + traza a pedido sin expander anidado ni botón de refresco). Tests unitarios verdes (pipeline local 8/8, 188 tests). **Verificación funcional confirmada por el usuario (2026-05-27):** corrida batch real y dashboard OK — el `flow_id` por caso y la traza se ven correctamente; esto confirma además empíricamente el supuesto de la opción C (en batch secuencial la recencia de `/flows` trae el flow del caso recién corrido). SC-US1-001..003 y SC-US2-001..003 completos. Deuda no bloqueante: incompatibilidad con SPEC-009 (paralelo) documentada en Assumptions; el modo simple (SPEC-007) sigue sin persistir la traza.
- **2026-05-27** — Decisión de cierre del flow ("dos pasos") — opción **C** elegida por el usuario. La pregunta era cómo replicar en batch el mecanismo de dos pasos del dashboard (primer `get_trace` automático + botón "Actualizar traza"). Se constató que ese refresh se apoya en la recencia de `/flows` y **no es válido en batch** una vez que se avanza al caso siguiente. Decisión: **captura única** en vivo por caso (sin poll ni segundo fetch); la traza se persiste tal cual aunque el `overall_status` quede no terminal; el `flow_id` es el **ancla** y el cierre completo se consulta abriendo ese flow en la plataforma. Cambios: nuevo FR-US2-007 (captura única, traza tal cual, sin replicar el botón) y FR-US1-007 (mostrar `flow_id` + nota de estado no terminal, sin botón de refresco); coverage actualizado. Descartadas opción A (poll hasta terminal — alarga la corrida) y opción B (refresh post-corrida por `flow_id` — requiere método nuevo y falla con lotes >~50 por la ventana de `/flows`).
- **2026-06-07** — Por [ADR-005](../docs/ARCHITECTURE.md) la captura en vivo `run_one`/`_capture_trace` se mueve de `src/runner` a `src/application/run_suite.py` (FR-US2-002/FR-US2-007 sin cambio de comportamiento: sigue siendo captura única en vivo, secuencial, tras `wait_for_completion`; sólo cambia el módulo). `domain/` sigue sin hacer I/O ni conocer el shape del proveedor.
- **2026-06-07** — `/clarify`: reconciliación spec↔código (Principio V). El movimiento ADR-005 **ya está implementado** (`_capture_trace`/`run_one`/`run_batch` viven en `src/application/run_suite.py`; `runner.py` sólo importa), no pendiente como decía la entrada previa. Se actualizó FR-US2-002 y la fila de Coverage de `src/runner` → `src/application/run_suite.py`; sin cambio de comportamiento. Ver «Clarifications».
- **2026-06-07** — `/analyze`: corrección de exactitud del Coverage mapping (sin cambio de comportamiento ni de código). (B1) Las filas de `FR-US1-004/006` y `SC-US1-002` citaban un "test que verifica que la revisión no invoca al agente" inexistente; se corrigió a **por construcción** (`_render_case_trace` no recibe el cliente) + verificación funcional. (B2) `FR-US1-001/005` y `SC-US1-001` citaban un "test de integración" de render inexistente; se aclaró que el render UI se verifica **funcionalmente** (sin unit test, consistente con SPEC-007). (B3) `FR-US2-002` ahora indica que se ejercita vía la fachada `runner.run_batch` en `test_runner.py`. (B5) FR-US2-001: "correlación por posición" → "por contención" (la traza es un campo del `TestResult`, no un join posicional). Deuda viva señalada: B4 (guard de concurrencia para `concurrency>1`) a anclar en [[SPEC-009-parallel-execution]].
