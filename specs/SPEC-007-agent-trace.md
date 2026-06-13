# SPEC-007-agent-trace — Visor de traza de ejecución del agente

**Estado:** active
**Iter:** 7
**Formato:** Híbrido
**Depende de:** [[SPEC-002-agent-client]], [[SPEC-003-classification-evaluator]], [[SPEC-005-run-persistence]]
**Relacionada con:** [[SPEC-008-suite-metrics]], [[SPEC-010-batch-trace]]

## User Story (Priority: P2)

Como evaluador de calidad, quiero ver qué sub-agentes invocó el orquestador, en qué orden y con qué resultado parcial, para entender **por qué** el agente clasificó como lo hizo y no solo **qué** clasificó.

**Why this priority:** la traza es diagnóstica — no bloquea el valor de producto (batch + métricas van antes), pero es clave para depurar clasificaciones inesperadas en uso real.

**Independent Test:** se puede testear completamente enviando un caso real desde el dashboard y verificando que aparece la sección "Traza de ejecución" con al menos un paso visible tras el veredicto.

## Acceptance Scenarios

1. **Given** el dashboard acaba de mostrar el veredicto de un caso, **When** el usuario expande "Traza de ejecución", **Then** ve la lista de sub-agentes invocados con su estado, input/output colapsables y duración.
2. **Given** el endpoint `/flows` no devuelve pasos para el run, **When** se renderiza la sección, **Then** aparece el mensaje "Traza no disponible" en lugar de un error.
3. **Given** un `TraceStep` se construye con `status` fuera de `TRACE_STEP_STATUSES`, **When** se instancia, **Then** lanza `ValueError`.
4. **Given** un `TraceStep` se construye con `step_id` o `agent_name` vacío, **When** se instancia, **Then** lanza `ValueError`.

## Clarifications

### Session 2026-06-07

- Q: ¿Cómo se resuelve el `[NEEDS CLARIFICATION]` de FR-008 (correlación exacta `run_id → flow instance_id` sin verificar) en una spec ya `active`? → A: Mantener la verificación pendiente, pero reformularla como deuda explícita en «Fuera de alcance» y quitar el marcador embebido del FR. FR-008 documenta el fallback vigente (`trigger`+`agent_id`+recencia) como contrato de la "traza simple".
- Q: La serialización `to_dict`/`from_dict` de `AgentTrace`/`TraceStep` está implementada y testeada pero sin FR en SPEC-007 (requisito implícito). ¿Se agrega un FR aquí? → A: No. La capacidad ya la gobierna [[SPEC-010-batch-trace]] (FR-US2-001/003 + tests round-trip); agregar un FR en SPEC-007 duplicaría ownership (SSOT). Se añade solo una nota cruzada en Key Entities apuntando a SPEC-010.
- Q: FR-010 condiciona la duración a `started_at`/`completed_at`, pero la implementación la deriva de `duration_ms` y FR-002 califica esos timestamps de "irreales". ¿Cómo se alinea? → A: Reescribir FR-010: la duración mostrada se deriva de `duration_ms` cuando está disponible; los timestamps no se usan para calcularla (consistente con FR-002). No cambia código.
- Q: `overall_status` es string libre sin validación ni conjunto de valores especificado. ¿Cómo se especifica? → A: Declararlo free-form del proveedor en FR-003 (string pasado tal cual, sin enum ni validación, degrada a `"unknown"`), con valores observados como ejemplos no exhaustivos; el predicado terminal `{"completed","failed"}` que usa FR-012 se explicita. No cambia código.

## Functional Requirements

- **FR-001**: MUST: El sistema expone `TraceStep` y `AgentTrace` como dataclasses frozen+slots en `src/domain/agent_trace.py`, sin I/O ni dependencias externas.
- **FR-002**: MUST: `TraceStep` incluye: `step_id`, `agent_name`, `status`, `input_summary`, `output_summary`, `started_at: str | None`, `completed_at: str | None`, `duration_ms: int | None`, `child_flow_id: str | None`. **Decisión (fix 2026-05-27):** se agregó `duration_ms` porque el proveedor expone la duración real en `trace_context.duration_ms` (los timestamps `created_at`/`updated_at` son del registro, no del span de ejecución, y dan deltas irreales). **Decisión (2026-05-27):** se agregó `child_flow_id` porque el proveedor expone en cada task la clave `child_flow_instance_id` con el `instance_id` del flow anidado que ese paso dispara (ej. `FI - Agente validador de Intents`); los demás tasks lo traen `null`. Es necesario para poder correlacionar un paso con su workflow interno y navegar su traza.
- **FR-003**: MUST: `AgentTrace` incluye: `thread_id`, `flow_id: str | None`, `overall_status`, `steps: tuple[TraceStep, ...]`. **`overall_status` es un string libre** pasado tal cual desde el estado del flow del proveedor (estado del flow en la clave `state`, ver FR-006); el dominio no lo valida ni lo enumera (a diferencia de `TraceStep.status`, que sí se valida contra `TRACE_STEP_STATUSES`), y degrada a `"unknown"` cuando el proveedor no lo informa. Valores observados (no exhaustivos): `"completed"`, `"failed"`, `"interrupted"`, `"in_progress"`, `"unknown"`. A efectos del refresco (FR-012), los estados **terminales** son `"completed"` y `"failed"`; cualquier otro se considera no terminal.
- **FR-004**: MUST: La constante `TRACE_STEP_STATUSES` es pública y contiene los valores válidos de `status`: `"completed"`, `"failed"`, `"in_progress"`, `"skipped"`.
- **FR-005**: MUST: El puerto `AgentClient` en `src/domain/ports.py` incluye `get_trace(self, thread_id: str) -> AgentTrace`.
- **FR-006**: MUST: `RemoteAgentClient.get_trace()` consulta `GET {flows_url}` y mapea la respuesta al modelo de dominio. Todo el mapeo vive en el adapter — el dominio no conoce el shape del proveedor. **Shape real verificado (2026-05-27, ver `docs/AGENT-INVOCATION.md` §6):** estado del flow y de cada paso en la clave **`state`** (no `status`); pasos en **`tasks`** (lista de dicts con `name`, `state`, `task_instance_id`, `input`, `output`, `trace_context.duration_ms`, `child_flow_instance_id`); orden de ejecución en **`sequence.steps`** (lista de grupos de nombres). El adapter ordena `tasks` según `sequence.steps`, descarta tasks sin `name`, normaliza `state` a `TRACE_STEP_STATUSES` y mapea `child_flow_instance_id` → `TraceStep.child_flow_id`.
- **FR-007**: MUST: `RemoteAgentClient.send()` captura y devuelve `run_id` del body de `chat/completions` para permitir la correlación con `/flows`. **Decisión (impl.2026-05-27):** se extendió `AgentResponse` con `run_id: str | None = None` (campo opcional con default, no rompe llamadores existentes) en lugar de crear un dataclass nuevo.
- **FR-008**: MUST: La "traza simple" correlaciona el run con su flow mediante el **fallback documentado** (no verifica `run_id`): `get_trace(thread_id)` toma el flow con `trigger == "flow_async_chat"` y `agent_id == AGENT_ID` más reciente por timestamp; si ninguno matchea, el más reciente de la lista. **Decisión (impl.2026-05-27):** `run_id` ya se captura en FR-007 para ejercitar a futuro la correlación exacta `run_id → flow instance_id`; esa correlación queda como **deuda pendiente de verificación empírica** (ver «Fuera de alcance» y Clarifications 2026-06-07), no como ambigüedad bloqueante de esta spec.
- **FR-009**: MUST: `get_trace()` devuelve `AgentTrace(steps=())` cuando el endpoint no devuelve pasos o falla, sin propagar la excepción.
- **FR-010**: MUST: El módulo `src/dashboard/trace_panel.py` renderiza: header con estado general + `thread_id`/`flow_id`; lista de pasos con ícono de estado, nombre del sub-agente, resumen de input/output y **duración derivada de `duration_ms` cuando está disponible** (los timestamps `started_at`/`completed_at` provienen del registro y no del span de ejecución — ver FR-002 —, por eso no se usan para calcular la duración mostrada); mensaje "Traza no disponible" si `steps` está vacío. **Decisión (impl.2026-05-27):** el panel se invoca **dentro** del expander "Traza de ejecución" (FR-011) y Streamlit no permite expanders anidados, por lo que el input/output se muestra como resumen acotado inline (no en sub-expanders). El resumen lo produce el adapter (`input_summary`/`output_summary`, máx. 800 chars).
- **FR-011**: MUST: La integración en `src/dashboard/app.py` muestra la sección "Traza de ejecución" colapsada por defecto (expander con `expanded=False`), después del veredicto (post SPEC-003), obtenida con `client.get_trace(thread_id)` tras `get_thread_messages()` y persistida en `session_state` junto al resultado.
- **FR-012**: MUST: La sección de traza ofrece "Actualizar traza" (re-`get_trace(thread_id)`). **Motivo (timing, verificado 2026-05-27):** el agente deposita la clasificación en el thread y `wait_for_completion()` retorna **antes** de que el flow externo cierre su cola (`actualizar_iniciativa`, `send_mail`, `__flow_end__`), por lo que el primer fetch puede ver `overall_status == "interrupted"` y una tarea `in_progress`. El veredicto (SPEC-003) no se ve afectado; refrescar muestra el flow ya `completed`. Si el estado no es terminal (`completed`/`failed`) se muestra una nota explicativa.

## Key Entities

- **`TraceStep`**: un paso de ejecución de un sub-agente. Campos: `step_id`, `agent_name`, `status`, `input_summary`, `output_summary`, `started_at`, `completed_at`, `duration_ms`, `child_flow_id`. El campo `child_flow_id` se popula solo en el task que dispara un flow anidado (ej. `FI - Agente validador de Intents`); en los demás es `None`.
- **`AgentTrace`**: la traza completa de un run. Contiene `thread_id`, `flow_id`, `overall_status` y una tupla ordenada de `TraceStep`.

> **Serialización (`to_dict`/`from_dict`):** ambos modelos exponen serialización a/desde `dict` (código puro en `domain/`, sin I/O). Esa capacidad y su round-trip los **gobierna [[SPEC-010-batch-trace]]** (FR-US2-001/FR-US2-003, tests `test_round_trip_preserves_trace_on_disk` y de round-trip en `tests/unit/test_agent_trace.py`); SPEC-007 no la redefine para no duplicar SSOT. La persistencia a disco vive en `adapters/` (`FileRunRepository`, SPEC-005/010).

## Success Criteria

- [x] **SC-001**: `ruff check`, `ruff format --check`, `tools/check_naming.py` sobre `src/`: verde (pipeline local 8/8). Nota: el gate de naming corre sobre `src/` (las violaciones preexistentes con `json`/`csv` en algunos tests son ajenas a esta spec).
- [x] **SC-002**: `tests/unit/test_agent_trace.py` cubre construcción válida de `TraceStep`/`AgentTrace`, `status` inválido, `step_id`/`agent_name` vacíos y `steps=()`; `tests/unit/test_remote_agent_client.py` cubre captura de `run_id`, mapeo del adapter con fixture, selección por recencia y response vacío/error → traza sin pasos.
- [x] **SC-003**: `get_trace()` verificado contra el agente real (2026-05-27): un run real devuelve 9 pasos ordenados, todos con `state` correcto y duración (`duration_ms`). Confirmó la forma real de `/flows` (ver FR-006). Verificación visual en el dashboard confirmada por el usuario (2026-05-27): la sección "Traza de ejecución" renderiza los pasos, el botón "Actualizar traza" refresca el estado y "Traza no disponible" aparece cuando no hay pasos.
- [x] **SC-004**: cubierto por `render_trace` (rama `steps=()` → "Traza no disponible") y test del adapter que produce traza vacía.

## Assumptions

- `flows_url` ya está en `PlatformConfig` (SPEC-002) — no se añaden variables de entorno nuevas.
- La traza no altera la lógica de evaluación (SPEC-003): el veredicto Pass/Fail/Indeterminado no cambia.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|-------------|
| FR-001, FR-002, FR-003, FR-004 | `src/domain/agent_trace.py` + tests unitarios de construcción y validación |
| FR-005 | `src/domain/ports.py` + `import-linter` |
| FR-006, FR-008 | `src/adapters/remote_agent_client.py` (get_trace) + tests con fixture de response del proveedor |
| FR-007 | extensión de `AgentResponse` en adapter + test de correlación |
| FR-009 | test unitario: response vacío/error → `AgentTrace(steps=())` sin excepción |
| FR-010, FR-011 | `src/dashboard/trace_panel.py` + integración en `src/dashboard/app.py` |
| FR-012 | `src/dashboard/app.py` (`_refresh_trace` + botón "Actualizar traza" + nota de estado no terminal) + verificación funcional |
| SC-001 | `tools/check_naming.py` + ruff en CI |
| SC-002 | `tests/unit/test_agent_trace.py` |
| SC-003 | verificación funcional en dashboard real |
| SC-004 | test unitario de render con `steps=()` |

## Fuera de alcance

- Traza por caso en corridas batch y su persistencia → [[SPEC-010-batch-trace]].
- Persistencia de la traza en `runs/*.json` → extensión futura de [[SPEC-005-run-persistence]] (ejercitada por [[SPEC-010-batch-trace]] US2).
- Visualización de trazas históricas / métricas agregadas → [[SPEC-008-suite-metrics]].
- Comparación de trazas entre runs y replay de pasos.
- **Correlación exacta `run_id → flow instance_id`** en `/flows`: pendiente de verificación empírica (ejecutar `tools/list_orchestrate_instances.py` con un run real para confirmar si el `run_id` del body coincide con `instance_id`/`wxo_run_id`; recién entonces estrechar el fallback de FR-008). Relevante sobre todo ante runs concurrentes (SPEC-009), donde la selección por recencia podría traer el flow equivocado. Mientras tanto rige el fallback de FR-008.

## Historial

- **2026-05-24** — Spec creada en formato casero. Motivación: entender el razonamiento interno del agente por caso. Arquitectura: modelo en `domain/`, fetching en `adapters/`, rendering en `dashboard/`. Correlación `run_id → flow instance_id` pendiente de verificación empírica.
- **2026-05-25** — Reescrita a formato híbrido. Estado cambiado de `notas` a `draft`. Contenido técnico preservado íntegro; `[NEEDS CLARIFICATION]` embebidos en FR-007 y FR-008.
- **2026-05-26** — Correcciones de estilo: `Acceptance Scenarios` separada de `User Story`; `Key Entities` movida a sección propia; `Coverage mapping` agregado; `Fuera de alcance` separado de `Assumptions`; separadores `---` eliminados; campo `Formato` normalizado.
- **2026-05-27** — Implementada ("traza simple"). Estado `draft`→`active`. Resueltos los `[NEEDS CLARIFICATION]`: FR-007 extiende `AgentResponse` con `run_id`; FR-008 usa el fallback por `trigger`+`agent_id`+recencia (correlación exacta por `run_id` aún pendiente de verificación empírica). FR-010 ajustado al límite de expanders anidados de Streamlit (input/output inline acotado). Archivos: `src/domain/agent_trace.py`, `src/domain/ports.py` (puerto `get_trace` + `run_id`), `src/adapters/remote_agent_client.py` (`get_trace` + captura `run_id`), `src/dashboard/trace_panel.py`, integración en `src/dashboard/app.py`, tests en `tests/unit/`. Pipeline local verde 8/8. Pendiente SC-003 (verificación funcional contra agente real).
- **2026-05-27** — Cerrada. Verificación visual en el dashboard confirmada por el usuario: SC-001..SC-004 completos. Pipeline local verde 8/8 (175 tests). Deuda residual no bloqueante: correlación exacta `run_id → flow instance_id` (`run_id` ya se captura en FR-007; estrechar el fallback de FR-008 cuando se ejercite empíricamente).
- **2026-05-27** — Iter 8: agregado `child_flow_id: str | None` a `TraceStep` (FR-002, FR-006). Verificado empíricamente que la clave `child_flow_instance_id` en `/flows → tasks` trae el `instance_id` del flow anidado en el task `FI - Agente validador de Intents`; los demás tasks lo traen `null`. Se actualiza dominio, adapter y `to_dict()`. Tests a extender en SC-002.
- **2026-06-06** — Reconciliación de cobertura: FR-012 estaba implementado (`_refresh_trace` + botón "Actualizar traza" en `src/dashboard/app.py`) pero omitido en el Coverage mapping. Agregada su fila. Gap detectado por `tools/check_traceability.py` (Principio V).
- **2026-06-07** — `/clarify` (4 ambigüedades de `/analyze`, sin tocar `src/`): (1) FR-008 — se quitó el `[NEEDS CLARIFICATION]` embebido; el fallback `trigger`+`agent_id`+recencia queda como contrato y la correlación exacta `run_id → flow instance_id` pasa a «Fuera de alcance» como deuda pendiente de verificación. (2) Serialización `to_dict`/`from_dict` — no se agrega FR (evita duplicar SSOT); nota cruzada en Key Entities señalando a [[SPEC-010-batch-trace]] (FR-US2-001/003) como gobernante. (3) FR-010 — reescrito: la duración se deriva de `duration_ms`, no de los timestamps `started_at`/`completed_at` (consistente con FR-002). (4) FR-003 — `overall_status` declarado free-form del proveedor (sin enum/validación, degrada a `"unknown"`), con predicado terminal `{"completed","failed"}` explícito para FR-012. Ver sección «Clarifications».
