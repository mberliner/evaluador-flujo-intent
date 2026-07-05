# SPEC-013-client-adapter-selection — Selección de adaptador de cliente para plataformas alternativas

**Estado:** active
**Iter:** 13 impl.2026-07-03 (US1, US2, US3 cerradas)
**Formato:** Híbrido
**Depende de:** [[SPEC-000-naming]], [[SPEC-002-agent-client]]
**Relacionada con:** [[SPEC-005-run-persistence]], [[SPEC-006-batch-suite]], [[SPEC-008-suite-metrics]], [[SPEC-007-agent-trace]], [[SPEC-010-batch-trace]]

**Resumen:** La suite puede ejecutarse contra plataformas tecnológicas alternativas seleccionando el adaptador de cliente por entorno (`AGENT_CLIENT_TYPE`), sin tocar el dominio ni los consumidores. Entrega tres cortes: **US1** selección de adaptador vía factory (P2), **US2** trazabilidad de la URL bajo test (P3), **US3** traza sintetizada del pipeline síncrono (P3). Las tres cerradas con prueba funcional el 2026-07-03.

---

## Contrato verificado de la plataforma síncrona

Referencia única del contrato real del adaptador `sync_http` (REST síncrono, auth por header `x-api-key`, sin `thread_id` nativo). Sondeado el 2026-07-02 y reconciliado con el primer envío real el 2026-07-03. Los FR referencian esta sección en vez de repetir el detalle.

- **Entrada:** el contenido del `form` de `MessageBuilder` viaja **plano en la raíz del body** (sin envoltorio `form` ni `id` del caso). Mapeo identidad 1:1 con `schemas/FI_Orquestador_Input.schema.json` (12 campos top-level y sus objetos anidados `tipo_intent.*`, `datos_requeridos.*`); el adaptador no transforma nombres ni tipos.
- **Respuesta `200`:** pipeline con corto-circuito `integridad → impacto → factibilidad → fastgate → redactor_mail`; las claves reales llevan prefijo `output_`. El color viene en `output_fastgate.clasificacion` en mayúsculas (ej. `"VERDE"`).
- **Discriminador de rechazo:** `output_fastgate` **presente con valor `null`** (un gate previo resolvió `false` y cortó el pipeline) → rechazo de negocio. La clave existe en ambas ramas; el bloque de mail también existe en ambas, por eso **no** sirve como discriminador.
- **Forma inesperada:** un `200` **sin la clave** `output_fastgate`, o con bloque sin color legible, no pertenece a ninguna rama → fallo técnico, nunca rechazo.
- **No sondeado:** la forma interna de los bloques distintos de `output_fastgate` (ej. si un gate trae `{"resultado": bool}`). Todo tratamiento de esos bloques es agnóstico a su forma interna (FR-US3-004/005); el shape real se verifica en envíos funcionales y puede refinar esta sección.

---

## User Story 1 — Selección de plataforma tecnológica (Priority: P2)

Como operador de la suite, quiero configurar contra qué plataforma tecnológica se ejecuta mi perfil de pruebas, para evaluar al mismo agente cuando sea migrado a otro proveedor, sin modificar el código interno de la suite ni alterar sus métricas.

**Why this priority:** sin esta capacidad la suite queda rígidamente acoplada al transporte, autenticación y empaquetado de payload del proveedor original.

**Independent Test:** levantar el sistema configurando un adaptador alternativo hacia un mock local y enviar un caso; verificar que la solicitud HTTP y el payload cumplen el contrato de la plataforma alternativa y que el dominio procesa la respuesta.

### Clarifications

- **2026-06-24** — Credenciales: variables de entorno genéricas `ALT_CLIENT_*` leídas solo por `PlatformConfig` (FR-US1-009). SDKs de terceros permitidos, confinados a `adapters/` (FR-US1-007). El condicional de creación vive en `AgentClientFactory` (FR-US1-005).
- **2026-07-02** — Sondeo empírico del contrato real → ver «Contrato verificado de la plataforma síncrona» (FR-US1-010/011). Se desacopla de SPEC-011 adoptando la firma vigente `send(form: dict)` (FR-US1-002). La asimetría sync/async se encapsula en el adaptador para no tocar consumidores (FR-US1-012). Fallos de transporte → Indeterminado, como el cliente original (FR-US1-013).

### Acceptance Scenarios

1. **Given** que no se especifica una variable de selección de cliente, **When** el sistema se inicializa, **Then** usa por defecto el adaptador asincrónico original (`RemoteAgentClient`), asegurando retrocompatibilidad total.
2. **Given** un tipo de cliente alternativo configurado en el entorno con sus credenciales, **When** se envía un caso, **Then** la suite instancia el nuevo adaptador (cumple el puerto `AgentClient`), delega la invocación con su propio protocolo y entrega el resultado al evaluador del perfil actual.
3. **Given** un tipo de cliente que no existe, **When** la aplicación arranca, **Then** falla inmediatamente con un error de configuración detallado, antes de cualquier petición de red.

### Functional Requirements

- **FR-US1-001**: MUST: `PlatformConfig` (`adapters/platform_config.py`) lee `AGENT_CLIENT_TYPE` para determinar el adaptador. Valores registrados: `remote_async` (default, `RemoteAgentClient`) y `sync_http` (`SyncHttpAgentClient`). Valor fuera del registro → `MissingConfigError` en `from_env()` (SC-US1-003).
- **FR-US1-002**: MUST: todo cliente implementa los 5 métodos del puerto `AgentClient` con la firma **vigente** `send(form: dict, conversation_id=None)` de [[SPEC-002-agent-client]] (la migración a `AgentInput` es alcance de [[SPEC-011-agent-under-test]]). Si la plataforma no soporta historiales nativos, `get_thread_messages` devuelve `[]`.
  > User Story 3 revisa `get_trace` para el cliente síncrono: de estructura vacía a traza sintetizada (FR-US3-002).
- **FR-US1-003**: MUST: la construcción del payload específico del proveedor ocurre íntegramente en el adaptador concreto, que recibe el `form: dict` de `MessageBuilder`, lo rinde al formato de su plataforma y desempaqueta la respuesta (FR-US1-010/011).
- **FR-US1-004**: MUST: invariante [[SPEC-000-naming]] — identificadores agnósticos, sufijos por mecanismo (ej. `SyncHttpAgentClient`), nunca nombres comerciales.
- **FR-US1-005**: MUST: un `AgentClientFactory` en `adapters/` con firma `create(config: PlatformConfig) -> AgentClient` encapsula el condicional de creación y resuelve el `CredentialProvider`, evitando duplicar cableado en los composition roots.
- **FR-US1-006**: MUST: la exigencia de variables en `PlatformConfig.from_env()` es condicional al `AGENT_CLIENT_TYPE` activo (`ES_*` vs `ALT_CLIENT_*`); no fallan inicializaciones por variables ajenas al cliente elegido.
- **FR-US1-007**: MAY: los clientes alternativos pueden agregar SDKs a `requirements.txt`; su importación se confina a `src/adapters/`.
- **FR-US1-008**: MUST: las anotaciones concretas en los composition roots (`dashboard/app.py`) se relajan al puerto abstracto `AgentClient` para que `mypy --strict` acepte cualquier adaptador del factory.
- **FR-US1-009**: MUST: credenciales y endpoints alternativos como variables genéricas (`ALT_CLIENT_URL`, `ALT_CLIENT_API_KEY`), leídas solo por `PlatformConfig` (único lector de `os.environ`); su requeridad la gobierna FR-US1-006.
- **FR-US1-010**: MUST: el adaptador envía la **entrada** según «Contrato verificado»: `form` plano en la raíz del body, sin envoltorio ni `id`, mapeo identidad sin transformar nombres ni tipos.
  > La plataforma puede exigir campos que el schema declara con `default` (ej. `restricciones`); no impacta porque `TestCase` ya garantiza su presencia no vacía.
- **FR-US1-011**: MUST: el adaptador colapsa la respuesta a un único valor antes de armar `AgentResponse.content`: (a) `output_fastgate` presente → **pass-through genérico** de su `clasificacion`, sin hardcodear colores; (b) `output_fastgate` en `null` → emite `Rechazado`; (c) forma inesperada → fallo técnico (FR-US1-013). La canonización a `PALETA_CLASIFICACION` (title-case, case-insensitive) es de `ClassificationEvaluator.extract`, así cualquier color nuevo se soporta sin tocar el adaptador.
- **FR-US1-012**: MUST: el adaptador honra el contrato conversacional del puerto con independencia del transporte, transparente para `run_one`, dashboard y runner. Para transporte síncrono: `send` ejecuta la invocación completa, cachea el resultado colapsado y devuelve un `conversation_id` **sintético no nulo** (satisface la guarda de `run_one`); `wait_for_completion` → `True`; `get_final_response` → el valor cacheado. El adaptador asíncrono conserva el polling original.
- **FR-US1-013**: MUST: los fallos técnicos (HTTP no-200 —incl. `422`/`5xx`—, timeout, forma inesperada) se mapean a `conversation_id=None` → resultado **Indeterminado** sin abortar la corrida. Un fallo técnico nunca se interpreta como veredicto de negocio: `Rechazado` proviene exclusivamente de un `200` con corto-circuito (Principio III: ante fallo, no se infiere clasificación).

### Key Entities

- **PlatformConfig** (existente, `adapters/platform_config.py`): se extiende para leer `AGENT_CLIENT_TYPE` y las variables genéricas del cliente activo.
- **AgentClientFactory** (nuevo, `adapters/agent_client_factory.py`): resuelve el `CredentialProvider` e instancia el cliente adecuado vía `create(config) -> AgentClient`.
- **SyncHttpAgentClient** (nuevo, `adapters/sync_agent_client.py`): adaptador del puerto para la plataforma síncrona REST, aplica FR-US1-010..013.
- **StaticCredentialProvider** (nuevo, `adapters/token_provider.py`): `CredentialProvider` mínimo que devuelve una llave fija (la plataforma no tiene ciclo de token/refresh).

### Success Criteria

- [x] **SC-US1-001**: la suite sin alterar el `.env` invoca al proveedor original y funciona exactamente igual que antes.
- [x] **SC-US1-002**: al cambiar `AGENT_CLIENT_TYPE` a un adaptador registrado, los envíos se enrutan por dicho cliente con sus endpoints.
- [x] **SC-US1-003**: `AGENT_CLIENT_TYPE` inválido arroja un error entendible antes de lanzar dashboard o runner.
- [x] **SC-US1-004**: prueba funcional manual (condición de cierre): un caso real con `sync_http` devuelve veredicto correcto por el circuito completo, y el camino por defecto sigue operando contra el proveedor original. OK del usuario 2026-07-03.

### Assumptions

- Independiente de [[SPEC-011-agent-under-test]]: adopta la firma vigente `send(form: dict)`; si SPEC-011 introduce `AgentInput`, la reconciliación es responsabilidad de esa spec.
- `AGENT_CLIENT_TYPE` (plataforma/transporte) y el perfil de agente de SPEC-011 (qué se evalúa) son ejes ortogonales.
- La lectura de entorno sigue centralizada en `PlatformConfig`, con exigencia condicional (FR-US1-006).

### Coverage mapping

| Requisito | Cubierto por |
|-----------|-------------|
| FR-US1-001, FR-US1-006, FR-US1-009 | `tests/unit/test_platform_config.py` |
| FR-US1-002, FR-US1-003, FR-US1-010, FR-US1-011, FR-US1-013 | `tests/unit/test_sync_agent_client.py` |
| FR-US1-005 | `tests/unit/test_agent_client_factory.py` |
| FR-US1-012 | `tests/unit/test_sync_agent_client.py` + `tests/integration/test_sync_client_run_one.py` (consumidores sin cambios) |
| FR-US1-004, FR-US1-007, FR-US1-008 | pipeline: `check_naming.py`, `lint-imports`, `mypy --strict` |
| SC-US1-001 | `test_platform_config.py` (default) + `test_remote_agent_client.py` (cliente original intacto) |
| SC-US1-002 | `test_agent_client_factory.py` + `test_sync_client_run_one.py` |
| SC-US1-003 | `test_platform_config.py` + `test_agent_client_factory.py` (tipo inválido → error) |
| SC-US1-004 | prueba funcional manual (no automatizable; OK en Historial) |

### Fuera de alcance

- Soporte simultáneo a múltiples clientes en una misma corrida (cada corrida usa el cliente global).
- Modificación del `MessageBuilder` (solo cambia cómo el cliente concreto serializa el `form`).

---

## User Story 2 — Trazabilidad del endpoint bajo test (Priority: P3)

Como operador de la suite, quiero ver a qué URL concreta se enviaron las pruebas de una corrida —al enviarla y después, en estadísticas y matriz de confusión—, para confirmar sin ambigüedad contra qué plataforma corrí cada evaluación.

**Why this priority:** `agent_id` es solo una etiqueta (UUID del proveedor original o el literal `"sync_http"`) que no identifica la URL real; con múltiples endpoints alternativos futuros deja de alcanzar para auditar. P3: la suite ya es operable sin esto.

**Independent Test:** con cualquiera de los dos clientes configurados, enviar un caso desde el dashboard → ver la URL efectiva junto al resultado; generar estadísticas → la URL aparece en `estadistica-corridas.csv` y en la vista de la última corrida. Sin modificar el contrato de red de ningún adaptador.

### Acceptance Scenarios

1. **Given** un `PlatformConfig` resuelto, **When** el sistema muestra o persiste la URL bajo test, **Then** obtiene un valor único y agnóstico (`effective_endpoint_url`) sin conocer los internos de cada adaptador.
2. **Given** el envío de un caso único desde el dashboard, **When** termina la evaluación, **Then** la URL efectiva se muestra junto al resultado y queda en el detalle de la corrida (`runs/detail/*.json`).
3. **Given** corridas persistidas, **When** genero `estadistica-corridas.csv`, **Then** incluye la URL efectiva de cada corrida.
4. **Given** la vista de la última corrida (estadísticas + matriz), **When** la abro, **Then** veo la URL junto al resto de la metadata (`run_id`, `timestamp`, `agent_id`).
5. **Given** una corrida persistida **antes** de esta User Story, **When** la cargo, **Then** el sistema no falla: el campo se lee vacío (retrocompatibilidad).

### Functional Requirements

- **FR-US2-001**: MUST: `PlatformConfig` expone la property agnóstica `effective_endpoint_url`: para `remote_async` la compone de `chat_url` + `agent_id` (misma construcción que hace `RemoteAgentClient` internamente); para `sync_http` es `alt_client_url`. Ningún adaptador cambia su contrato; la property solo **expone** un valor hoy encapsulado.
- **FR-US2-002**: MUST: el valor se persiste como campo `endpoint_url` de `SuiteResult`, cuyo SSOT de esquema es [[SPEC-005-run-persistence]] (esta spec no lo redeclara). `from_dict` tolera corridas previas sin la clave con default `""`.
- **FR-US2-003**: MUST: `estadistica-corridas.csv` incorpora la columna `endpoint_url` (SSOT de columnas: [[SPEC-006-batch-suite]] US2). La fila `TOTAL` queda vacía.
- **FR-US2-004**: MUST: el dashboard muestra la URL en tres puntos: (a) junto al resultado del caso único; (b) en la vista de la última corrida; (c) junto a la matriz de confusión — impresa en el caller del render, sin que `SuiteMetrics` conozca la URL (separación domain/UI de [[SPEC-008-suite-metrics]]).
- **FR-US2-005**: MUST: invariante [[SPEC-000-naming]] — identificador agnóstico (`endpoint_url`); no se agregan variables de entorno nuevas.

### Key Entities

- **PlatformConfig** (existente): gana la property `effective_endpoint_url`, calculada de campos ya existentes.
- **SuiteResult** (existente, SSOT en [[SPEC-005-run-persistence]]): se extiende **allí** con `endpoint_url: str = ""`; esta User Story lo consume, no lo define.

### Success Criteria

- [x] **SC-US2-001**: la URL mostrada coincide exactamente con la URL de la petición HTTP real, para ambos `client_type`. *(`test_platform_config.py::test_effective_endpoint_url_*`; confirmación visual en SC-US2-004.)*
- [x] **SC-US2-002**: una corrida persistida antes de esta spec carga sin error, con URL vacía. *(`test_result.py::test_endpoint_url_default_and_backward_compatible`.)*
- [x] **SC-US2-003**: el CSV regenerado incluye `endpoint_url` poblada para corridas nuevas y vacía para antiguas. *(`test_file_run_repository.py`, 2 tests.)*
- [x] **SC-US2-004**: prueba funcional manual (condición de cierre): URL correcta visible en envío, estadísticas y matriz para ambos clientes. OK del usuario 2026-07-03.

### Assumptions

- `endpoint_url` es información adicional a `agent_id`, no un sustituto (ambos se muestran).
- Granularidad por **corrida**, no por caso: un único endpoint por corrida (consistente con «Fuera de alcance» de US1); un tercer adaptador deberá extender la property de forma análoga.

### Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-US2-001 | `tests/unit/test_platform_config.py` (resolución por `client_type`) |
| FR-US2-002 | `tests/unit/test_result.py` (round-trip con/sin `endpoint_url`); formal en [[SPEC-005-run-persistence]] |
| FR-US2-003 | `tests/unit/test_file_run_repository.py`; formal en [[SPEC-006-batch-suite]] |
| FR-US2-004 | integración en `src/dashboard/app.py` + verificación funcional (SC-US2-004) |
| FR-US2-005 | `tools/check_naming.py` (pipeline) |

### Fuera de alcance

- Persistir la URL a nivel **caso** (`estadistica-casos.csv`): el endpoint es propiedad de la corrida.
- Historial/comparación de URLs entre corridas más allá del CSV existente.
- Enmascarado de credenciales en URL: los orígenes actuales no las embeben (auth por header/token); el saneamiento de un adaptador futuro que lo hiciera queda fuera.
- Un tercer `client_type` o múltiples endpoints simultáneos («Fuera de alcance» de US1).

---

## User Story 3 — Traza sintetizada del pipeline síncrono (Priority: P3)

Como evaluador de calidad, quiero ver las etapas del pipeline que la plataforma síncrona ya devuelve en su respuesta, para entender **por qué** clasificó o rechazó como lo hizo —igual que con la traza del proveedor original—, sin llamadas de red extra.

**Why this priority:** el body `200` ya trae las etapas, pero el adaptador las descarta al colapsar solo el color (FR-US1-011), dejando vacío el visor «Traza de ejecución» ([[SPEC-007-agent-trace]]) con `sync_http`. P3: diagnóstica, no cambia el veredicto.

**Independent Test:** enviar un caso con `sync_http` desde el dashboard y expandir «Traza de ejecución» → ver los pasos del pipeline con su estado; en un caso de corto-circuito, las etapas posteriores aparecen omitidas. Sin llamadas de red adicionales.

### Clarifications

- **2026-07-03** — La síntesis **no puede asumir la forma interna** de los bloques de gate/mail: solo `output_fastgate` y el discriminador `null` están verificados (ver «Contrato verificado», punto «No sondeado»). Por eso el estado del paso se decide por presencia/contenido (FR-US3-004) y el resumen serializa sin asumir claves (FR-US3-005). La verificación del shape real se difiere al primer envío funcional (SC-US3-004), mismo patrón con que se reconcilió el prefijo `output_` en US1.

### Acceptance Scenarios

1. **Given** un `200` con `output_fastgate` presente (pipeline completo), **When** se invoca `get_trace`, **Then** devuelve un `AgentTrace` con un `TraceStep` por etapa presente, todos `completed`, en el orden fijo del pipeline.
2. **Given** un `200` con corto-circuito, **When** se invoca `get_trace`, **Then** las etapas que no ejecutaron por el corte quedan `skipped`; la traza refleja hasta dónde corrió el pipeline.
3. **Given** un fallo técnico o un `thread_id` sin respuesta cacheada, **When** se invoca `get_trace`, **Then** devuelve `AgentTrace(steps=())` sin propagar excepción ([[SPEC-007-agent-trace]] FR-009).

### Functional Requirements

- **FR-US3-001**: MUST: `send` cachea lo necesario para reconstruir la traza (body crudo o pasos derivados) asociado al `conversation_id` sintético, junto al veredicto (FR-US1-012). Sin llamadas de red extra; puerto y consumidores sin cambios.
- **FR-US3-002**: MUST: `get_trace(thread_id)` sintetiza un `AgentTrace` desde lo cacheado, un `TraceStep` por bloque `output_*`, reusando el modelo de [[SPEC-007-agent-trace]] sin modificarlo; el conocimiento del shape del proveedor queda confinado al adaptador (ADR-001). Revisa FR-US1-002 para el cliente síncrono (de vacío a sintetizada); `get_thread_messages` sigue `[]`.
- **FR-US3-003**: MUST: los pasos siguen el orden fijo del pipeline, independiente del orden de claves del body («Contrato verificado»). `agent_name` legible y agnóstico por etapa; `step_id` agnóstico y estable.
- **FR-US3-004**: MUST: el mapeo a `TRACE_STEP_STATUSES` es **agnóstico a la forma interna del bloque**: presente con contenido no vacío → `completed`; ausente, `null` o vacío → `skipped`; nunca `failed`.
  > Consecuencias deliberadas, no defectos: el gate que disparó el corto-circuito queda `completed` (su bloque llegó con contenido: ejecutó); `output_redactor_mail`, presente en ambas ramas, queda `completed` incluso tras etapas `skipped` (en la rama de rechazo se emite el mail de rechazo). Un `false` de negocio no es fallo técnico del paso (Principio III, distinción de FR-US1-013). Mismo discriminador de presencia/`null` que FR-US1-011: no introduce supuestos nuevos.
- **FR-US3-005**: MUST: `input_summary`/`output_summary` llevan un resumen acotado y agnóstico (serialización del bloque tal cual, máx. 800 caracteres, [[SPEC-007-agent-trace]] FR-010), sin asumir claves internas. Campos sin dato nativo (`duration_ms`, `child_flow_id`, `started_at`, `completed_at`) → `None`.
- **FR-US3-006**: MUST: `thread_id` = `conversation_id` sintético del run, `flow_id = None`, `overall_status = "completed"` para un `200`. El botón «Actualizar traza» (SPEC-007 FR-012) es un no-op inofensivo: no hay estado no terminal que refrescar.
- **FR-US3-007**: MUST: ante fallo técnico (FR-US1-013) o `thread_id` sin cache, `get_trace` devuelve `AgentTrace(steps=())` sin excepción ([[SPEC-007-agent-trace]] FR-009). No se infiere traza sin respuesta válida.
- **FR-US3-008**: MUST: invariante [[SPEC-000-naming]] (las claves `output_*` son contrato del proveedor confinado al adaptador, no identificadores expuestos). Sin variables de entorno ni dependencias nuevas; el visor `src/dashboard/trace_panel.py` renderiza la traza sintetizada **sin cambios**.

### Key Entities

- **SyncHttpAgentClient** (existente): extiende su cache (veredicto → veredicto + traza) y `get_trace` deja de devolver vacío.
- **AgentTrace / TraceStep** (existentes, `domain/agent_trace.py`, SSOT en [[SPEC-007-agent-trace]]): se reusan sin modificar.

### Success Criteria

- [x] **SC-US3-001**: un `200` completo produce un paso `completed` por etapa presente, en orden fijo (`test_sync_agent_client.py`).
- [x] **SC-US3-002**: un `200` con corto-circuito produce etapas no ejecutadas `skipped` y la que cortó `completed` (`test_sync_agent_client.py`).
- [x] **SC-US3-003**: fallo técnico o `thread_id` sin cache → `AgentTrace(steps=())` sin excepción (`test_sync_agent_client.py`).
- [x] **SC-US3-004**: prueba funcional manual (condición de cierre): «Traza de ejecución» muestra las etapas del pipeline con `sync_http`, incluido un rechazo con etapas omitidas. OK del usuario 2026-07-03.

### Assumptions

- La traza es **diagnóstica**: el colapso a color de FR-US1-011 sigue siendo la única fuente del veredicto (SPEC-003).
- `get_trace` opera sobre lo cacheado en `send` (a diferencia de `RemoteAgentClient.get_trace`, que consulta `/flows`).
- La captura/persistencia batch de trazas ya la gobierna [[SPEC-010-batch-trace]] vía el round-trip genérico de `AgentTrace`; al poblar `get_trace`, el camino batch funciona sin cambios en `run_batch`.

### Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-US3-001, FR-US3-002, FR-US3-003, FR-US3-004, FR-US3-005, FR-US3-006, FR-US3-007, SC-US3-001, SC-US3-002, SC-US3-003 | `tests/unit/test_sync_agent_client.py` (cache sin red extra; mapeo y orden fijo; presencia→`completed` / corte→`skipped` / nunca `failed`; resúmenes truncados y campos `None`; metadata sintética; fallo/sin-cache → traza vacía) |
| FR-US3-008 | `tools/check_naming.py` (pipeline) + `trace_panel.py` sin cambios (SPEC-007) |
| SC-US3-004 | prueba funcional manual en el dashboard (no automatizable; OK en Historial) |

### Fuera de alcance

- **Duración por etapa** (`duration_ms`): la respuesta síncrona no expone spans de tiempo.
- **`child_flow_id` / sub-flows**: la plataforma síncrona no expone flows anidados.
- **Refresco real de la traza** (SPEC-007 FR-012): innecesario en transporte síncrono; el botón queda no-op.
- **Persistencia batch de la traza**: ya cubierta por [[SPEC-010-batch-trace]].

---

## Historial

- **2026-06-24** — Spec creada: separar el perfil del agente a evaluar de la plataforma tecnológica donde se aloja, soportando plataformas alternativas sin alterar el circuito de evaluación.
- **2026-07-02** — Verificación empírica del contrato de la plataforma alternativa (entrada 1:1 con el schema; pipeline con corto-circuito y colapso por presencia del bloque final). Se agregan FR-US1-010/011 → ver «Contrato verificado».
- **2026-07-02** — Desacople de [[SPEC-011-agent-under-test]]: habilitado por la verificación anterior, FR-US1-002/003 adoptan la firma vigente `send(form: dict)`. SPEC-013 implementable de forma autónoma.
- **2026-07-03** — Implementación de US1 (Iter 13). Reconciliaciones: valores registrados `remote_async`/`sync_http` (FR-US1-001); discriminador de rechazo precisado como bloque presente-con-`null` (FR-US1-011); `AGENT_ID` opcional para `sync_http` (etiqueta de metadata); el factory expone además `resolve_credentials(config)` para la validación anticipada del dashboard; FR-US1-007 no ejercido (usa `requests`, ya presente). Cierre condicionado a SC-US1-004.
- **2026-07-03** — Reconciliación por primer envío real (spec viva): las claves del pipeline llevan prefijo `output_` y el color viene en mayúsculas — corregidos adaptador (`_FINAL_BLOCK_KEY`) y FR-US1-011. La rama de fallo técnico funcionó según lo especificado.
- **2026-07-03** — Cierre de US1: SC-US1-004 con OK del usuario → `active`.
- **2026-07-03** — Migrada al estándar multi-HU (`docs/SPEC-FORMAT.md`): renumeración FR/SC-001.. → FR/SC-US1-.. sin cambio de comportamiento. Añadida **US2** (trazabilidad del endpoint): se expone `PlatformConfig.effective_endpoint_url`; la persistencia se delega como SSOT a [[SPEC-005-run-persistence]] y [[SPEC-006-batch-suite]]. → `draft` hasta SC-US2-004.
- **2026-07-03** — Añadida **US3** (traza sintetizada del pipeline síncrono): sintetizar `AgentTrace` desde la respuesta ya obtenida, reusando modelo y visor de [[SPEC-007-agent-trace]] sin modificarlos. Revisa `get_trace` de FR-US1-002 para el cliente síncrono.
- **2026-07-03** — `/analyze` (7 hallazgos, 0 CRITICAL). Resuelto A1 (HIGH): la síntesis no puede asumir la forma interna de bloques nunca sondeados → FR-US3-004/005 reescritos shape-agnósticos (estado por presencia/contenido; resumen sin asumir claves). De paso A2: el mail `completed` en ambas ramas queda explícito como deliberado. A3–A7 deuda menor de redacción.
- **2026-07-03** — Implementación de US3 (`send` cachea el body; `get_trace` sintetiza en orden fijo; `_has_content` shape-agnóstico; `_summarize` truncado a 800). 8 tests nuevos en `test_sync_agent_client.py`; pipeline VERDE.
- **2026-07-03** — Implementación de US2 (`effective_endpoint_url`; `SuiteResult.endpoint_url` con retrocompat; columna en `estadistica-corridas.csv`; URL como caption en tres puntos del dashboard). Pipeline VERDE.
- **2026-07-03** — Cierre de SPEC-013: SC-US2-004 y SC-US3-004 confirmados por el usuario → `active`.
- **2026-07-05** — Reescritura editorial al formato compacto (piloto de simplificación): se extrae la sección «Contrato verificado de la plataforma síncrona» como referencia única, se separan reglas de justificaciones en los FR (notas indentadas), se agrupa el coverage mapping y se poda el historial. **Sin cambio normativo**: IDs de FR/SC y su semántica intactos.
