# SPEC-013-client-adapter-selection — Selección de adaptador de cliente para plataformas alternativas

**Estado:** active
**Iter:** 13 impl.2026-07-03 (US1, US2, US3 cerradas)
**Formato:** Híbrido
**Depende de:** [[SPEC-000-naming]], [[SPEC-002-agent-client]]
**Relacionada con:** [[SPEC-005-run-persistence]], [[SPEC-006-batch-suite]], [[SPEC-008-suite-metrics]], [[SPEC-007-agent-trace]], [[SPEC-010-batch-trace]]

---

## User Story 1 — Selección de plataforma tecnológica (Priority: P2)

Como operador de la suite, quiero poder configurar contra qué plataforma tecnológica se ejecuta mi perfil de pruebas, para poder evaluar al mismo agente (ej. el clasificador original) cuando este sea migrado a un proveedor diferente, sin modificar el código interno de la suite ni alterar sus métricas.

**Why this priority:** El negocio requiere flexibilidad para evaluar la precisión del modelo en distintas plataformas en la nube. Sin esta capacidad, la suite está rígidamente acoplada a la forma de comunicación (transporte, autenticación y empaquetado de payload) del proveedor original.

**Independent Test:** Levantar el sistema configurando un adaptador de cliente alternativo hacia un mock local y enviar un caso. Verificar que la solicitud HTTP y el payload resultante corresponden al contrato esperado por la plataforma alternativa, y que la respuesta es procesada correctamente por el dominio.

### Clarifications

#### Session 2026-06-24

- Q: ¿Cómo deberían definirse y gestionarse las credenciales para los clientes alternativos en el entorno? → A: Añadir variables de entorno genéricas (ej. `ALT_CLIENT_URL`, `ALT_CLIENT_API_KEY`) a `PlatformConfig`, manteniéndolo como único lector del entorno (FR-US1-009).
- Q: ¿Se permite incorporar SDKs de terceros como dependencias del proyecto para implementar los clientes alternativos? → A: Sí, se permite añadir SDKs en `requirements.txt`, confinando su importación estricta a la capa de adaptadores (FR-US1-007).
- Q: ¿Dónde debería residir la lógica condicional que decide instanciar uno u otro adaptador de cliente alternativo? → A: En un nuevo `AgentClientFactory` dentro de la capa `adapters/` para centralizar la lógica de creación y evitar duplicación en los composition roots (FR-US1-005).

#### Session 2026-07-02

Verificación empírica contra una plataforma alternativa concreta de flujo de intents (adaptador síncrono REST con auth por header `x-api-key`), sondeando su contrato real.

- Q: ¿El formulario de entrada que exige la plataforma alternativa requiere transformación respecto del schema actual? → A: No. Los 12 campos top-level y sus objetos anidados (`tipo_intent`, `datos_requeridos.otros`) coinciden **1:1** con `schemas/FI_Orquestador_Input.schema.json` y con lo que produce `MessageBuilder`. El adaptador sólo desenvuelve la clave `form` y postea su contenido **plano** en la raíz del body (descartando `id`); no incrusta el payload como texto en un bloque `messages` (FR-US1-010).
- Q: ¿Cómo se mapea la respuesta multi-etapa de la plataforma a la paleta única del dominio (`PALETA_CLASIFICACION`)? → A: La respuesta es un pipeline con corto-circuito: `integridad → impacto → factibilidad → fastgate`. Regla de colapso confirmada con datos: si `fastgate` viene presente → se usa su `clasificacion` (color); si `fastgate` viene `null` (algún gate previo dio `false`) → se emite `Rechazado`. El discriminador es `fastgate is null`, no el mail de salida (que existe en ambas ramas) (FR-US1-011).
- Q: ¿SPEC-013 debe esperar a SPEC-011 (`AgentInput`) para implementarse? → A: No. Se desacopla: la spec adopta la firma vigente `send(form: dict)` porque el `form` de `MessageBuilder` ya coincide 1:1 con la entrada de la plataforma. Se elimina la dependencia y el "riesgo de orden"; la migración a `AgentInput` queda a cargo de SPEC-011 (FR-US1-002, FR-US1-003).
- Q: El orquestador `run_one` es asíncrono (exige `conversation_id` de `send` y lee el veredicto de `get_final_response`), pero `/intents` es síncrona y sin `thread_id`. ¿Cómo se resuelve? → A: Se **encapsula la comunicación en el adaptador** para no depender de sync/async y mantener el flujo conversacional transparente: el adaptador síncrono simula el ciclo (conversation_id sintético + cache en `send`, `wait_for_completion`→True, `get_final_response`→valor cacheado). No se modifican los consumidores ni el puerto (FR-US1-012).
- Q: ¿Cómo se mapean los fallos de transporte (no-200, timeout, forma inesperada)? → A: Igual que el cliente original: fallo técnico → `conversation_id=None` → Indeterminado, sin abortar la corrida. Un `422` es defecto de serialización, no `Rechazado`; el rechazo de negocio es siempre un `200` con `fastgate=null` (FR-US1-013).

### Acceptance Scenarios

1. **Given** que no se especifica una variable de selección de cliente de agente, **When** el sistema se inicializa, **Then** utiliza por defecto el adaptador asincrónico original (`RemoteAgentClient`), asegurando retrocompatibilidad total.
2. **Given** que se especifica un tipo de cliente de agente alternativo en el entorno y sus respectivas credenciales, **When** se envía un caso de prueba, **Then** la suite instancia el nuevo adaptador (que cumple el puerto `AgentClient`), delega la invocación usando su propio protocolo de comunicación y entrega el resultado al evaluador del perfil actual.
3. **Given** un tipo de cliente configurado que no existe en el sistema, **When** la aplicación arranca, **Then** falla inmediatamente con un error de configuración detallado antes de realizar cualquier petición de red.

### Functional Requirements

- **FR-US1-001**: MUST: El sistema lee la variable de entorno `AGENT_CLIENT_TYPE` desde `adapters/platform_config.py` para determinar el tipo de adaptador a instanciar. Valores registrados: `remote_async` (cliente original, `RemoteAgentClient`) y `sync_http` (adaptador síncrono REST, `SyncHttpAgentClient`). Si la variable no está presente, su valor por defecto es `remote_async`. Un valor fuera del registro produce `MissingConfigError` en `from_env()` (SC-US1-003).
- **FR-US1-002**: MUST: Todo nuevo cliente de agente implementa los 5 métodos del puerto `AgentClient` (`send`, `wait_for_completion`, `get_thread_messages`, `get_final_response`, `get_trace`). Esta spec adopta la firma **actual** del puerto, `send(form: dict, conversation_id=None)` de [[SPEC-002-agent-client]], sin modificarla: el `form` que produce `MessageBuilder` ya es el contrato de entrada suficiente (ver FR-US1-010). La eventual migración a `send(input: AgentInput)` queda fuera de alcance y a cargo de [[SPEC-011-agent-under-test]]. Si la plataforma alternativa no soporta historiales o trazas nativas, los métodos `get_thread_messages` y `get_trace` MUST devolver estructuras vacías (ej. `[]` y `AgentTrace` vacío) para satisfacer el protocolo sin romper consumidores. *(Nota: **User Story 3** revisa la conducta de `get_trace` para el cliente síncrono — de vacío a una traza sintetizada desde las etapas del pipeline que la respuesta ya trae; `get_thread_messages` sigue vacío.)*
- **FR-US1-003**: MUST: La construcción del payload específico del proveedor ocurre íntegramente en el adaptador concreto, que recibe el `form: dict` (payload de `MessageBuilder`, `{"form": {...}}`). El adaptador se encarga de renderizar ese input a la estructura esperada por su plataforma (ver FR-US1-010) y de desempaquetar la respuesta (ver FR-US1-011).
- **FR-US1-004**: MUST: Se respeta el principio de nomenclatura agnóstica a tecnología ([[SPEC-000-naming]]). Los identificadores en el código fuente de los nuevos clientes no usarán nombres de proveedores comerciales, empleando sufijos descriptivos sobre el mecanismo (ej. `SyncHttpAgentClient`, `WebSocketAgentClient`, `CustomRestAgentClient`).
- **FR-US1-005**: MUST: Se define un `AgentClientFactory` dentro de la capa `adapters/` con la firma `create(config: PlatformConfig) -> AgentClient`. Este factory encapsula el condicional de creación del cliente y **también** resuelve/instancia el `CredentialProvider` correspondiente, evitando duplicar este cableado en los composition roots.
- **FR-US1-006**: MUST: La validación y requerimiento de variables en `PlatformConfig.from_env()` MUST volverse condicional al `AGENT_CLIENT_TYPE` seleccionado. El set de variables exigidas (ej. las `ES_*` originales vs `ALT_CLIENT_*`) debe depender exclusivamente de la plataforma activa, evitando errores de inicialización por variables ajenas al cliente elegido.
- **FR-US1-007**: MAY: Los clientes alternativos pueden introducir SDKs de terceros en `requirements.txt` para interactuar con plataformas externas. Si lo hacen, la importación y uso de estas dependencias MUST confinarse exclusivamente a los módulos concretos dentro de `src/adapters/` para no contaminar el dominio ni la capa de aplicación.
- **FR-US1-008**: MUST: Las anotaciones concretas de tipo en los composition roots (específicamente en `dashboard/app.py`, ej. `tuple[..., RemoteAgentClient, ...]` y los `cast("RemoteAgentClient", ...)`) MUST relajarse al puerto abstracto `AgentClient` para evitar fallos en `mypy --strict` cuando el factory devuelva otros adaptadores.
- **FR-US1-009**: MUST: Las credenciales y endpoints específicos de los clientes alternativos se definen como variables de entorno genéricas y agnósticas al proveedor (ej. `ALT_CLIENT_URL`, `ALT_CLIENT_API_KEY`), leídas exclusivamente por `PlatformConfig` (único lector de `os.environ`). El set concreto exigido para cada cliente queda gobernado por la requeridad condicional de FR-US1-006.
- **FR-US1-010**: MUST: Cuando la plataforma alternativa consume el formulario de intent como JSON estructurado nativo (no como texto embebido), el adaptador MUST enviar el contenido del `form` **plano en la raíz del body**, sin el envoltorio `form` ni el `id` del caso. El mapeo de campos es identidad: los 12 campos y sus objetos anidados (`tipo_intent.{negocio,operativo,capacidad_equipos,tecnico_arquitectural}`, `datos_requeridos.{ninguno,datos_publicos,datos_operativos,datos_personales,datos_confidenciales,otros.{estado,message}}`) coinciden 1:1 con `schemas/FI_Orquestador_Input.schema.json`; el adaptador NO transforma nombres ni tipos. Nota: la plataforma puede exigir como obligatorios campos que el schema declara con `default` (ej. `restricciones`, `supuesto_riesgo`); esto no impacta porque `TestCase` ya garantiza su presencia no vacía.
- **FR-US1-011**: MUST: El adaptador MUST colapsar la respuesta multi-etapa de la plataforma a un único valor de `PALETA_CLASIFICACION` antes de construir el `AgentResponse.content`, aplicando: (a) si el bloque de clasificación final (`output_fastgate` — las claves del body real llevan prefijo `output_`, verificado funcionalmente 2026-07-03) viene presente, usar su color **por pass-through genérico** —depositar `output_fastgate.clasificacion` tal cual (la plataforma lo emite en mayúsculas, ej. `"VERDE"`), sin enumerar ni hardcodear la lista de colores—; (b) si dicho bloque viene con valor `null` —porque un gate previo (`integridad`, `impacto` o `factibilidad`) resolvió `false` y el pipeline hizo corto-circuito— emitir `Rechazado`. El discriminador MUST ser el valor `null` del bloque de clasificación final (cuya clave está presente en ambas ramas del pipeline, verificado empíricamente), no el bloque de mail de salida (también presente en ambas ramas). Un body `200` **sin la clave** del bloque de clasificación, o con un bloque sin color legible, no pertenece a ninguna rama del pipeline: es forma inesperada y se trata como fallo técnico (FR-US1-013), nunca como `Rechazado`. El adaptador deposita el valor colapsado en `AgentResponse.content` y la canonización a la paleta (title-case, case-insensitive sobre `PALETA_CLASIFICACION` completa) queda a cargo de `ClassificationEvaluator.extract`; así cualquier color que emita la plataforma se soporta sin cambios en el adaptador.
- **FR-US1-012**: MUST: La comunicación con la plataforma se encapsula íntegramente en el adaptador, que MUST honrar el contrato conversacional del puerto `AgentClient` **con independencia de si el transporte subyacente es síncrono o asíncrono**, de forma transparente para `run_one`, el dashboard y el runner (ningún consumidor se modifica según el modo de transporte). Para un adaptador síncrono (ej. la plataforma `/intents`, que responde en una sola llamada y sin `thread_id`): (a) `send(form)` ejecuta la invocación completa, cachea el resultado colapsado (FR-US1-011) y devuelve un `AgentResponse` con un `conversation_id` **sintético no nulo** —para satisfacer la guarda de `run_one` que aborta ante la ausencia de `thread_id`—; (b) `wait_for_completion` MUST devolver `True` inmediatamente; (c) `get_final_response` MUST devolver el valor cacheado asociado a ese `conversation_id`, que es la superficie desde la cual el evaluador lee el veredicto. Un adaptador asíncrono conserva el comportamiento de polling original. Esta encapsulación mantiene intacto el flujo conversacional del proceso.
- **FR-US1-013**: MUST: Los **fallos técnicos** del adaptador (HTTP no-200 —incl. `422`/`5xx`—, timeout de red, o respuesta con forma inesperada) MUST mapearse a un `AgentResponse` con `conversation_id=None`, de modo que `run_one` produzca un resultado **Indeterminado** anotado sin abortar la corrida (consistente con `RemoteAgentClient` y con la tolerancia a fallos de `run_suite`). Un fallo técnico MUST NOT interpretarse como veredicto de negocio: el `422` (payload inválido) indica un defecto de serialización del adaptador/caso, no un `Rechazado`; `Rechazado` proviene exclusivamente de un `200` con corto-circuito de gates (FR-US1-011). Se preserva el Principio III: ante fallo, no se infiere clasificación.

### Key Entities

- **PlatformConfig** (existente, `adapters/platform_config.py`): Se extiende para leer `AGENT_CLIENT_TYPE` y configuraciones genéricas de base de URL y llaves, aplicables según el adaptador instanciado.
- **AgentClientFactory** (nuevo, `adapters/agent_client_factory.py`): Único responsable de resolver el `CredentialProvider` e instanciar el cliente adecuado (`RemoteAgentClient` u otros) exponiendo el método genérico `create(config) -> AgentClient`.
- **SyncHttpAgentClient** (nuevo, `adapters/sync_agent_client.py`): Adaptador concreto que implementa el puerto `AgentClient` para la plataforma alternativa síncrona REST (auth por header `x-api-key`), aplicando FR-US1-010..FR-US1-013.
- **StaticCredentialProvider** (nuevo, `adapters/token_provider.py`): Implementación mínima del puerto `CredentialProvider` que devuelve una llave fija de configuración (la plataforma alternativa no tiene ciclo de token/refresh).

### Success Criteria

- [x] **SC-US1-001**: La ejecución de la suite sin alterar el `.env` invoca al proveedor original y funciona exactamente igual que antes.
- [x] **SC-US1-002**: Al cambiar `AGENT_CLIENT_TYPE` hacia un nuevo adaptador registrado, los envíos de casos se enrutan correctamente a través de dicho cliente con sus endpoints correspondientes.
- [x] **SC-US1-003**: Si `AGENT_CLIENT_TYPE` es inválido, el sistema arroja un error entendible antes de lanzar el dashboard o ejecutar el batch runner.
- [x] **SC-US1-004**: Prueba funcional manual del usuario, condición de cierre de esta User Story: (a) un caso real enviado con `AGENT_CLIENT_TYPE=sync_http` contra la plataforma alternativa devuelve un veredicto correcto por el circuito completo (dashboard o runner); (b) el camino por defecto (sin `AGENT_CLIENT_TYPE`) sigue operando contra el proveedor original. OK confirmado por el usuario el 2026-07-03.

### Assumptions

- **Desacople de [[SPEC-011-agent-under-test]]:** esta User Story es independiente de SPEC-011. Adopta la firma vigente `send(form: dict)` de [[SPEC-002-agent-client]] (verificado 1:1 contra el contrato de la plataforma, FR-US1-010), de modo que puede implementarse sin esperar el value object `AgentInput`. Si SPEC-011 introduce `send(input: AgentInput)` más adelante, la reconciliación de firma es responsabilidad de esa spec, no de esta.
- La variable `AGENT_CLIENT_TYPE` (plataforma/transporte) y la de perfil de agente de [[SPEC-011-agent-under-test]] (qué agente/lógica se evalúa) son ejes ortogonales e independientes.
- La lectura de entorno sigue centralizada en `PlatformConfig`, pero su exigencia se vuelve condicional al tipo de cliente seleccionado (FR-US1-006).

### Coverage mapping

| Requisito | Cubierto por |
|-----------|-------------|
| FR-US1-001 | `tests/unit/test_platform_config.py` (tipo por defecto `remote_async`, lectura de `AGENT_CLIENT_TYPE`) |
| FR-US1-002 | `tests/unit/test_sync_agent_client.py` (los 5 métodos del puerto; `get_thread_messages`→`[]`, `get_trace`→traza vacía) |
| FR-US1-003 | `tests/unit/test_sync_agent_client.py` (serialización del payload y desempaquetado de la respuesta en el adaptador) |
| FR-US1-004 | Linter `tools/check_naming.py` sobre `src/adapters/` (pipeline) |
| FR-US1-005 | `tests/unit/test_agent_client_factory.py` (instancia correcta según config; resolución del `CredentialProvider`) |
| FR-US1-006 | `tests/unit/test_platform_config.py` (exigencia de variables condicional al tipo de cliente activo) |
| FR-US1-007 | Linter `lint-imports` (pipeline); no se agregaron SDKs (el adaptador usa `requests`, ya presente) |
| FR-US1-008 | Anotaciones de `dashboard/app.py` relajadas al puerto `AgentClient`, verificado vía `mypy --strict` (pipeline) |
| FR-US1-009 | `tests/unit/test_platform_config.py` (parsing de `ALT_CLIENT_URL` / `ALT_CLIENT_API_KEY`) |
| FR-US1-010 | `tests/unit/test_sync_agent_client.py` (body plano sin envoltorio `form` ni `id`; identidad de campos contra `schemas/FI_Orquestador_Input.schema.json`) |
| FR-US1-011 | `tests/unit/test_sync_agent_client.py` (rama color por pass-through, rama corto-circuito → `Rechazado`, body sin bloque → fallo técnico) |
| FR-US1-012 | `tests/unit/test_sync_agent_client.py` (`conversation_id` sintético + cache; `wait_for_completion`→`True`; `get_final_response` cacheado) + `tests/integration/test_sync_client_run_one.py` (`run_one` sin modificar la capa de aplicación) |
| FR-US1-013 | `tests/unit/test_sync_agent_client.py` (no-200 `422`/`5xx`, timeout y forma inesperada → `conversation_id=None`, nunca `Rechazado`) |
| SC-US1-001 | `tests/unit/test_platform_config.py` (default) + `tests/unit/test_remote_agent_client.py` (cliente original intacto) |
| SC-US1-002 | `tests/unit/test_agent_client_factory.py` + `tests/integration/test_sync_client_run_one.py` |
| SC-US1-003 | `tests/unit/test_platform_config.py` (tipo inválido → `MissingConfigError`) + `tests/unit/test_agent_client_factory.py` (tipo no registrado → error) |
| SC-US1-004 | Prueba funcional manual del usuario contra la plataforma alternativa real y el proveedor original (no automatizable; se registra el OK en Historial) |

### Fuera de alcance

- Soporte simultáneo a múltiples clientes dentro de una misma corrida (cada corrida usa el cliente definido globalmente).
- Modificación del `MessageBuilder` actual (sólo se modifica cómo el cliente concreto serializa y envía el `form`).

---

## User Story 2 — Trazabilidad del endpoint bajo test (Priority: P3)

Como operador de la suite, quiero ver a qué URL/endpoint concreto se enviaron las pruebas de una corrida —tanto al enviarla como después, en las estadísticas y en la matriz de confusión—, para poder confirmar sin ambigüedad contra qué plataforma corrí cada evaluación, sin tener que inferirlo indirectamente del valor de `agent_id`.

**Why this priority:** Hoy `agent_id` es una etiqueta (el UUID del proveedor original, o el literal `"sync_http"` para la plataforma alternativa) que no identifica la URL real invocada; ante múltiples endpoints alternativos futuros (`ALT_CLIENT_URL` variable por entorno) esa etiqueta deja de alcanzar para auditar una corrida. Es P3 porque la suite ya es operable sin esto (User Story 1); es una mejora de trazabilidad/auditoría sobre una capacidad ya funcional.

**Independent Test:** Con `AGENT_CLIENT_TYPE` y sus variables de entorno configuradas (para cualquiera de los dos clientes registrados), envío un caso único desde el dashboard → veo la URL efectiva usada junto al resultado. Genero la estadística de corridas → la URL aparece en `estadistica-corridas.csv` y en la vista de la última corrida (incluida la matriz de confusión). Verificable sin modificar el contrato de red de ningún adaptador existente.

### Acceptance Scenarios

1. **Given** un `PlatformConfig` resuelto (cualquier `client_type` registrado), **When** el sistema necesita mostrar o persistir la URL bajo test, **Then** obtiene un valor único y agnóstico (`effective_endpoint_url`) sin conocer los detalles internos de cada adaptador.
2. **Given** el envío de un caso único desde el dashboard, **When** la evaluación termina, **Then** la URL efectiva se muestra junto al resultado y queda persistida en el detalle de la corrida (`runs/detail/*.json`).
3. **Given** una o más corridas persistidas, **When** genero `estadistica-corridas.csv` ([[SPEC-006-batch-suite]] User Story 2), **Then** el archivo incluye la URL efectiva de cada corrida.
4. **Given** la vista de la última corrida (estadísticas + matriz de confusión, [[SPEC-008-suite-metrics]]), **When** la abro en el dashboard, **Then** veo la URL efectiva de esa corrida junto al resto de la metadata (`run_id`, `timestamp`, `agent_id`).
5. **Given** una corrida persistida **antes** de esta User Story (sin el campo nuevo), **When** la cargo, **Then** el sistema no falla: el campo se lee como vacío/desconocido (retrocompatibilidad).

### Functional Requirements

- **FR-US2-001**: MUST: `PlatformConfig` expone una property agnóstica `effective_endpoint_url` que resuelve la URL bajo test según el `client_type` activo: para `remote_async`, la compone a partir de `chat_url` + `agent_id` (misma construcción que hoy hace `RemoteAgentClient` internamente); para `sync_http`, es `alt_client_url` tal cual. Ningún adaptador cambia su contrato ni su forma de armar el request; esta property sólo **expone hacia afuera** un valor que hoy queda encapsulado dentro de cada cliente concreto.
- **FR-US2-002**: MUST: El valor se persiste a nivel corrida como campo `endpoint_url` en la entidad `SuiteResult`, cuyo SSOT de esquema es [[SPEC-005-run-persistence]] (esta User Story no redeclara la estructura de `SuiteResult`; sólo exige que SPEC-005 la extienda con este campo). Corridas persistidas antes de esta spec no tienen la clave; la lectura (`from_dict`) MUST tolerarlo con un valor por defecto (`""`), sin romper el round-trip existente.
- **FR-US2-003**: MUST: `runs/stats/estadistica-corridas.csv` incorpora la columna `endpoint_url`, cuyo SSOT de columnas es [[SPEC-006-batch-suite]] User Story 2 (esta User Story no redeclara el esquema del CSV; sólo exige que SPEC-006 lo extienda con esta columna). La fila `TOTAL` la deja vacía (no aplica a un agregado multi-corrida).
- **FR-US2-004**: MUST: El dashboard muestra `effective_endpoint_url` en tres puntos: (a) junto al resultado al enviar un caso único; (b) en la vista de la última corrida / estadísticas (junto a `run_id`/`timestamp`/`agent_id`); (c) como parte del contexto visible junto a la matriz de confusión ([[SPEC-008-suite-metrics]]), sin que el cómputo puro de la matriz (`SuiteMetrics`) conozca la URL — el dato se imprime en el caller del render, no dentro del componente de métricas, preservando la separación domain/UI de SPEC-008.
- **FR-US2-005**: MUST: Se respeta [[SPEC-000-naming]]: el identificador es agnóstico al proveedor (`effective_endpoint_url` / `endpoint_url`), nunca el nombre comercial de una plataforma. Las variables de entorno de origen (`ES_URL_CHAT`, `ALT_CLIENT_URL`) siguen siendo las ya existentes; no se agregan variables nuevas.

### Key Entities

- **PlatformConfig** (existente, `adapters/platform_config.py`): se extiende con la property `effective_endpoint_url`, calculada a partir de los campos ya existentes (`client_type`, `chat_url`, `agent_id`, `alt_client_url`); no agrega variables de entorno nuevas.
- **SuiteResult** (existente, dominio; SSOT de su esquema en [[SPEC-005-run-persistence]]): se extiende ahí con el campo `endpoint_url: str = ""`, propagado en `create()`, `to_dict()` y `from_dict()` (con default retrocompatible). Esta User Story consume ese campo, no lo define.

### Success Criteria

- [x] **SC-US2-001**: Al enviar un caso único con cualquiera de los dos `client_type` registrados, la URL mostrada en el dashboard coincide exactamente con la URL a la que se hizo la petición HTTP real (verificable con un mock/proxy o inspección de red). *(Cubierto por `test_platform_config.py::test_effective_endpoint_url_*`: la property resuelve la misma URL que arma cada adaptador; el dashboard consume esa property. Confirmación visual final en SC-US2-004.)*
- [x] **SC-US2-002**: Una corrida persistida antes de esta spec se sigue cargando sin error, mostrando el campo de URL vacío en vez de fallar. *(`test_result.py::test_endpoint_url_default_and_backward_compatible`.)*
- [x] **SC-US2-003**: `estadistica-corridas.csv` regenerado incluye la columna `endpoint_url` poblada para corridas nuevas y vacía para corridas antiguas sin el campo. *(`test_file_run_repository.py::test_regenerate_run_stats_includes_endpoint_url` + `..._endpoint_url_empty_for_legacy_run`.)*
- [x] **SC-US2-004**: Prueba funcional manual del usuario, condición de cierre de esta User Story: enviar una prueba contra cada uno de los dos clientes registrados y confirmar visualmente en el dashboard (envío, estadísticas y matriz) que la URL mostrada es la correcta en cada caso. OK confirmado por el usuario el 2026-07-03.

### Assumptions

- El valor de `agent_id` no se reemplaza ni se deprecia: `endpoint_url` es información adicional, no un sustituto (ambos se muestran).
- No se contempla en esta User Story exponer la URL para clientes futuros más allá de los dos ya registrados (`remote_async`, `sync_http`); un tercer adaptador deberá extender `effective_endpoint_url` de forma análoga.
- La granularidad es por **corrida**, no por caso: un único cliente/endpoint se usa durante toda la corrida (consistente con "Fuera de alcance" de User Story 1), por lo que `estadistica-casos.csv` (SPEC-005) no necesita este campo.

### Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-US2-001 | `tests/unit/test_platform_config.py` (resolución de `effective_endpoint_url` por `client_type`) |
| FR-US2-002 | `tests/unit/test_result.py` (round-trip `SuiteResult` con y sin `endpoint_url`), cubierto formalmente en [[SPEC-005-run-persistence]] |
| FR-US2-003 | `tests/unit/test_file_run_repository.py` (columna `endpoint_url` en `estadistica-corridas.csv`, fila TOTAL vacía), cubierto formalmente en [[SPEC-006-batch-suite]] |
| FR-US2-004 | integración en `src/dashboard/app.py` (envío single-case, vista de última corrida, matriz) + verificación funcional |
| FR-US2-005 | `tools/check_naming.py` |
| SC-US2-001 | prueba funcional manual del usuario (SC-US2-004) + test de resolución (FR-US2-001) |
| SC-US2-002 | test de retrocompatibilidad de `from_dict` (cubierto por FR-US2-002) |
| SC-US2-003 | test del escritor de `estadistica-corridas.csv` (cubierto por FR-US2-003) |
| SC-US2-004 | prueba funcional manual del usuario (no automatizable; se registra el OK en Historial) |

### Fuera de alcance

- Persistir la URL a nivel **caso** (`estadistica-casos.csv`, SPEC-005): el endpoint es una propiedad de la corrida completa, no varía caso a caso (ver Assumptions).
- Historial/comparación de URLs entre corridas distintas más allá de listarlas en el CSV ya existente.
- Enmascarado o redacción de credenciales embebidas en la URL: los valores de origen (`ES_URL_CHAT`, `ALT_CLIENT_URL`) ya son URLs sin credenciales embebidas (la auth viaja por header/token, no por query string); si un adaptador futuro las embebiera, su saneamiento queda fuera de esta spec.
- Soporte de un tercer `client_type` o de múltiples endpoints simultáneos: sigue gobernado por "Fuera de alcance" de User Story 1.

---

## User Story 3 — Traza sintetizada del pipeline síncrono (Priority: P3)

Como evaluador de calidad, quiero ver las etapas del pipeline que la plataforma síncrona ya devuelve en su respuesta (`integridad → impacto → factibilidad → fastgate → redactor de mail`), para entender **por qué** clasificó o rechazó como lo hizo —igual que con la traza del proveedor original—, sin llamadas de red extra.

**Why this priority:** Hoy el body `200` del endpoint síncrono trae las etapas del pipeline, pero el adaptador las **descarta**: sólo colapsa `output_fastgate` al color y tira el resto (FR-US1-011). Con `sync_http` activo, el visor "Traza de ejecución" ([[SPEC-007-agent-trace]]) queda vacío, perdiendo la información diagnóstica que la plataforma **ya entregó**. Es P3: es diagnóstica, no bloquea el circuito de evaluación (el veredicto no cambia).

**Independent Test:** Enviar un caso con `AGENT_CLIENT_TYPE=sync_http` desde el dashboard y expandir "Traza de ejecución" → ver los pasos del pipeline con su estado. Para un caso de corto-circuito (rechazado), la etapa que cortó aparece y las posteriores se muestran como omitidas. Verificable sin llamadas de red adicionales (la respuesta ya se obtuvo en `send`).

### Clarifications

#### Session 2026-07-03

- Q: La síntesis de traza, ¿puede asumir la forma interna de los bloques de gate (`output_integridad/impacto/factibilidad`) y del bloque de mail? → A: **No.** Del contrato real sólo está verificado empíricamente (2026-07-03, FR-US1-011): el prefijo `output_`, que `output_fastgate.clasificacion` trae el color, y que el discriminador de corto-circuito es el bloque final **presente con valor `null`**. La forma interna de los demás bloques (ej. si un gate trae `{"resultado": bool}`, si en corto-circuito viene `null`, ausente o presente-pero-vacío) **no se sondeó**. Por eso el adaptador MUST ser **agnóstico a la forma interna**: decide el estado del paso por presencia/ausencia/contenido no vacío (FR-US3-004), no leyendo un campo interno; y el resumen serializa el contenido tal cual venga, sin asumir claves (FR-US3-005). La verificación del shape real de cada bloque queda diferida al primer envío funcional (SC-US3-004), que puede refinar la spec si aparece un marcador de "ejecutado" que valga la pena distinguir — mismo patrón con que se reconcilió el prefijo `output_` en US1.

### Acceptance Scenarios

1. **Given** un `200` con `output_fastgate` presente (pipeline completo), **When** se invoca `get_trace`, **Then** devuelve un `AgentTrace` con un `TraceStep` por cada etapa presente, todos en estado `completed`, en el orden fijo del pipeline.
2. **Given** un `200` con corto-circuito (`output_fastgate` en `null` porque un gate previo dio `false`), **When** se invoca `get_trace`, **Then** las etapas que no llegaron a ejecutarse por el corte se marcan `skipped`; la traza refleja hasta dónde corrió el pipeline.
3. **Given** un fallo técnico (`conversation_id=None`, FR-US1-013) o un `thread_id` sin respuesta cacheada, **When** se invoca `get_trace`, **Then** devuelve `AgentTrace(steps=())` sin propagar excepción (consistente con [[SPEC-007-agent-trace]] FR-009).

### Functional Requirements

- **FR-US3-001**: MUST: `SyncHttpAgentClient.send` MUST cachear la información necesaria para reconstruir la traza (el body crudo del pipeline o los pasos ya derivados) asociada al `conversation_id` sintético, junto al veredicto que ya cachea (FR-US1-012). No se hacen llamadas de red adicionales: la traza se sintetiza desde la respuesta **ya obtenida** en `send`. El contrato del puerto `AgentClient` y los consumidores (`run_one`, dashboard, runner) no cambian.
- **FR-US3-002**: MUST: `SyncHttpAgentClient.get_trace(thread_id)` MUST sintetizar un `AgentTrace` a partir de lo cacheado, mapeando cada bloque `output_*` del pipeline a un `TraceStep`. Todo el conocimiento del shape del proveedor queda confinado al adaptador (ADR-001), reusando el modelo de dominio `AgentTrace`/`TraceStep` de [[SPEC-007-agent-trace]] sin modificarlo. **Esta capacidad revisa, para el cliente síncrono, la conducta de FR-US1-002 respecto de `get_trace`** (de "estructura vacía" a "traza sintetizada del pipeline"); `get_thread_messages` sigue devolviendo `[]` (la plataforma no tiene historial de thread nativo).
- **FR-US3-003**: MUST: El orden de los pasos es el orden fijo del pipeline, independiente del orden de claves del body: `integridad`, `impacto`, `factibilidad`, `fastgate`, `redactor_mail` (los bloques reales llevan prefijo `output_`, verificado 2026-07-03; ver FR-US1-011). El `agent_name` de cada `TraceStep` es una etiqueta legible y agnóstica derivada del nombre de la etapa; el `step_id` es agnóstico y estable.
- **FR-US3-004**: MUST: El mapeo a `TRACE_STEP_STATUSES` ([[SPEC-007-agent-trace]] FR-004) es **agnóstico a la forma interna del bloque** (ver Clarifications 2026-07-03): el estado se decide **sólo por presencia y contenido**, sin leer campos internos como `resultado`. Regla: bloque **presente y con contenido no vacío** (dict/lista/valor no vacío) → `completed`; bloque **ausente, `null` o vacío** → `skipped`. Nunca `failed`: un `false` de negocio de un gate no es un fallo técnico de ejecución del paso (se preserva el Principio III y la distinción de FR-US1-013). Consecuencia deliberada de esta regla, no un defecto: (a) la etapa que resolvió `false` y disparó el corto-circuito aparece `completed` porque su bloque **llegó con contenido** (ejecutó, sin importar el valor booleano interno); (b) las etapas que no corrieron por el corte quedan `skipped`; (c) el bloque de mail de salida (`output_redactor_mail`), presente en ambas ramas (FR-US1-011), aparece `completed` incluso tras etapas `skipped` — refleja que en la rama de rechazo se emite el mail de rechazo. El discriminador de presencia/`null` es el mismo que ya rige el colapso a color (FR-US1-011), por lo que no introduce supuestos nuevos sobre el contrato.
- **FR-US3-005**: MUST: `input_summary`/`output_summary` de cada paso llevan un resumen **acotado y agnóstico** del contenido del bloque correspondiente (serialización del bloque tal cual venga, truncada a máx. 800 caracteres, consistente con [[SPEC-007-agent-trace]] FR-010); el adaptador NO asume claves internas del bloque (ver Clarifications 2026-07-03). Los campos sin dato nativo en la respuesta síncrona (`duration_ms`, `child_flow_id`, `started_at`, `completed_at`) quedan en `None` (la plataforma no expone spans de tiempo ni flows anidados).
- **FR-US3-006**: MUST: El `AgentTrace` sintetizado usa `thread_id` = el `conversation_id` sintético del run, `flow_id = None` (no hay flow nativo) y `overall_status = "completed"` para un `200` (el transporte síncrono completó en una sola llamada; `overall_status` es free-form del proveedor por [[SPEC-007-agent-trace]] FR-003). El botón "Actualizar traza" del visor (SPEC-007 FR-012) es un no-op inofensivo: al ser síncrona, no hay estado no terminal que refrescar.
- **FR-US3-007**: MUST: Ante fallo técnico (`conversation_id=None`, FR-US1-013) o `thread_id` sin entrada cacheada, `get_trace` MUST devolver `AgentTrace(steps=())` sin propagar excepción (consistente con [[SPEC-007-agent-trace]] FR-009). No se infiere una traza cuando no hubo respuesta válida.
- **FR-US3-008**: MUST: Se respeta [[SPEC-000-naming]] (identificadores agnósticos: `output_*` son claves del contrato del proveedor confinadas al adaptador, no identificadores de código expuestos). No se agregan variables de entorno ni dependencias. El visor existente (`src/dashboard/trace_panel.py`, SPEC-007) renderiza la traza sintetizada **sin cambios**, al consumir el mismo modelo `AgentTrace`.

### Key Entities

- **SyncHttpAgentClient** (existente, `adapters/sync_agent_client.py`): se extiende el cache que hoy guarda sólo el veredicto colapsado (FR-US1-012) para retener también lo necesario para la traza; `get_trace` deja de devolver vacío y sintetiza el `AgentTrace` desde el pipeline.
- **AgentTrace / TraceStep** (existentes, `domain/agent_trace.py`, SSOT en [[SPEC-007-agent-trace]]): se **reusan sin modificar**. Esta User Story consume el modelo; no lo redefine.

### Success Criteria

- [x] **SC-US3-001**: Un `200` con pipeline completo produce un `AgentTrace` con un paso `completed` por etapa presente, en el orden fijo del pipeline (`tests/unit/test_sync_agent_client.py`).
- [x] **SC-US3-002**: Un `200` con corto-circuito produce una traza donde las etapas no ejecutadas quedan `skipped` y la que cortó queda `completed` (`tests/unit/test_sync_agent_client.py`).
- [x] **SC-US3-003**: Un fallo técnico o un `thread_id` sin cache produce `AgentTrace(steps=())` sin excepción (`tests/unit/test_sync_agent_client.py`).
- [x] **SC-US3-004**: Prueba funcional manual del usuario, condición de cierre de esta User Story: enviar un caso con `sync_http` desde el dashboard y confirmar que "Traza de ejecución" muestra las etapas del pipeline (incluido un caso de rechazo con etapas omitidas). OK confirmado por el usuario el 2026-07-03.

### Assumptions

- La traza sintetizada es **diagnóstica** y no altera el veredicto (SPEC-003): el colapso a color de FR-US1-011 sigue siendo la única fuente del Pass/Fail/Indeterminado.
- No hay llamadas de red extra: la respuesta del pipeline ya se obtuvo en `send`; `get_trace` opera sobre lo cacheado (a diferencia de `RemoteAgentClient.get_trace`, que sí consulta `/flows`).
- La captura de trazas en batch (`capture_traces`) y su persistencia por caso ya las gobierna [[SPEC-010-batch-trace]] mediante el round-trip genérico de `AgentTrace`; esta User Story no las redefine: al poblar `get_trace`, el camino batch de `sync_http` obtiene y persiste la traza sintetizada sin cambios en `run_batch`.

### Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-US3-001 | `tests/unit/test_sync_agent_client.py` (cache del body en `send`, sin llamadas de red extra) |
| FR-US3-002 | `tests/unit/test_sync_agent_client.py` (mapeo de bloques `output_*` a `TraceStep`; `get_thread_messages` sigue `[]`) |
| FR-US3-003 | `tests/unit/test_sync_agent_client.py` (orden fijo del pipeline, independiente del orden de claves) |
| FR-US3-004 | `tests/unit/test_sync_agent_client.py` (presente→`completed`, corto-circuito→`skipped`, nunca `failed`) |
| FR-US3-005 | `tests/unit/test_sync_agent_client.py` (resúmenes acotados; campos sin dato nativo → `None`) |
| FR-US3-006 | `tests/unit/test_sync_agent_client.py` (`thread_id` sintético, `flow_id=None`, `overall_status="completed"`) |
| FR-US3-007 | `tests/unit/test_sync_agent_client.py` (fallo técnico / sin cache → `AgentTrace(steps=())`) |
| FR-US3-008 | `tools/check_naming.py` (pipeline) + render sin cambios de `src/dashboard/trace_panel.py` (SPEC-007) |
| SC-US3-001..003 | `tests/unit/test_sync_agent_client.py` (los tres escenarios de aceptación) |
| SC-US3-004 | Prueba funcional manual del usuario en el dashboard (no automatizable; se registra el OK en Historial) |

### Fuera de alcance

- **Duración por etapa** (`duration_ms`): la respuesta síncrona no expone spans de tiempo; queda `None`. Añadirla exigiría que la plataforma emita tiempos por etapa.
- **`child_flow_id` / navegación a sub-flows**: no aplica; la plataforma síncrona no expone flows anidados (a diferencia del proveedor original, SPEC-007 FR-002).
- **Refresco real de la traza** (SPEC-007 FR-012): innecesario en transporte síncrono (no hay estado no terminal); el botón queda como no-op.
- **Persistencia batch de la traza sintetizada**: ya la cubre el round-trip genérico de `AgentTrace` de [[SPEC-010-batch-trace]]; no se redefine aquí.

---

## Historial

- **2026-06-24** — Spec creada. Motivación: Separar explícitamente el perfil del agente a evaluar de la plataforma de infraestructura tecnológica subyacente donde este se aloja, dando soporte a plataformas alternativas de inferencia sin alterar el circuito de evaluación.
- **2026-07-02** — Verificación empírica contra una plataforma alternativa concreta (adaptador síncrono REST, auth `x-api-key`). Se confirmó por sondeo del contrato real: (1) el formulario de entrada coincide 1:1 con el schema actual, sin transformación de campos (FR-US1-010); (2) la respuesta es un pipeline con corto-circuito (`integridad → impacto → factibilidad → fastgate`), y su colapso a la paleta del dominio se rige por la presencia/ausencia del bloque de clasificación final, mapeando la rama de corto-circuito a `Rechazado` (FR-US1-011). Se agregaron FR-US1-010 y FR-US1-011 con su cobertura.
- **2026-07-02** — Desacople de [[SPEC-011-agent-under-test]]. Habilitado por la verificación anterior (el `form` coincide 1:1 con la plataforma), FR-US1-002/FR-US1-003 vuelven a la firma vigente `send(form: dict)` en vez de `send(input: AgentInput)`. Se quitó SPEC-011 de `Depende de` y se eliminó el "riesgo de orden" de Assumptions. SPEC-013 queda implementable de forma autónoma.
- **2026-07-03** — Implementación de User Story 1 (Iter 13, spec → active). Decisiones de reconciliación spec↔código: (1) FR-US1-001 fija los valores registrados `remote_async` (default) y `sync_http`; el tipo inválido falla en `from_env()` con `MissingConfigError` y el factory tiene su propio `UnknownClientTypeError` defensivo. (2) FR-US1-011 se precisó: el discriminador de corto-circuito es el bloque final **presente con valor `null`** (verificado empíricamente que la clave existe en ambas ramas); un body sin la clave o sin color legible es forma inesperada → fallo técnico (FR-US1-013), nunca `Rechazado`. (3) `AGENT_ID` pasa a ser opcional para `sync_http` (etiqueta de metadata de corridas, fallback al tipo de cliente). (4) FR-US1-005: `AgentClientFactory` expone además `resolve_credentials(config)` para que el dashboard conserve la validación anticipada de credenciales sin duplicar el cableado. (5) FR-US1-007 no se ejerció: el adaptador usa `requests` (ya presente), sin SDKs nuevos. Entidades: `SyncHttpAgentClient` (`adapters/sync_agent_client.py`), `AgentClientFactory`, `StaticCredentialProvider`. La spec permanece en `draft`: SC-US1-001..003 quedaron confirmados por la suite automatizada y se agregó **SC-US1-004** (prueba funcional manual del usuario) como condición explícita de cierre → `active`.
- **2026-07-03** — Reconciliación por prueba funcional (spec viva): el primer envío real al endpoint devolvió `200` con las claves del pipeline prefijadas — `output_integridad`, `output_impacto`, `output_factibilidad`, `output_fastgate`, `output_redactor_mail` — a diferencia del sondeo del 2026-07-02 que las registró sin prefijo. El color viene en `output_fastgate.clasificacion` en mayúsculas (`"VERDE"`); el pass-through + canonización del evaluador lo cubren sin cambios. Se corrigió `_FINAL_BLOCK_KEY` en el adaptador y FR-US1-011; la rama de fallo técnico (clave ausente → Indeterminado) funcionó según lo especificado (FR-US1-013) en ese primer intento.
- **2026-07-03** — Cierre de User Story 1: SC-US1-004 tildado con OK explícito del usuario (prueba funcional manual confirmada: `sync_http` contra la plataforma alternativa real y camino por defecto contra el proveedor original). Spec pasa de `draft` a `active`.
- **2026-07-03** — Migrada al **estándar multi-HU** (`docs/SPEC-FORMAT.md`) para admitir una segunda User Story sin perder la primera: FR-001..013 → FR-US1-001..013, SC-001..004 → SC-US1-001..004, renumeración sin cambio de comportamiento. Añadida **User Story 2 — Trazabilidad del endpoint bajo test** (P3): motivada por la dificultad práctica de auditar contra qué URL corrió una prueba, ya que `agent_id` es sólo una etiqueta (UUID del proveedor original o literal `"sync_http"`) y no identifica la URL real. Se decide exponer `PlatformConfig.effective_endpoint_url` (agnóstico al proveedor) y mostrarlo en el dashboard (envío single-case, estadísticas de corridas, matriz de confusión). La persistencia del campo se delega como SSOT a [[SPEC-005-run-persistence]] (`SuiteResult.endpoint_url`) y [[SPEC-006-batch-suite]] (columna `endpoint_url` en `estadistica-corridas.csv`) para no duplicar la definición de esas entidades; SPEC-013 sólo consume y expone. Spec vuelve a `draft` hasta el cierre de SC-US2-004 (prueba funcional manual).
- **2026-07-03** — Añadida **User Story 3 — Traza sintetizada del pipeline síncrono** (P3, en definición). Motivación: la respuesta `200` de la plataforma síncrona ya trae las etapas del pipeline (`output_integridad → output_impacto → output_factibilidad → output_fastgate → output_redactor_mail`), pero el adaptador las descarta al colapsar sólo el color (FR-US1-011), dejando el visor de traza vacío para `sync_http`. Se decide **sintetizar** un `AgentTrace` desde esa respuesta ya obtenida (sin llamadas de red extra), reusando el modelo y el visor de [[SPEC-007-agent-trace]] sin modificarlos. La US3 **revisa** la conducta de `get_trace` de FR-US1-002 para el cliente síncrono (de vacío a traza sintetizada); `get_thread_messages` sigue vacío. Mapeo de estado: etapa con contenido → `completed`, etapa no ejecutada por corto-circuito → `skipped`, nunca `failed` (un `false` de negocio no es fallo técnico, Principio III). Se agregó [[SPEC-007-agent-trace]] y [[SPEC-010-batch-trace]] a `Relacionada con`. Pendiente de implementación; cierre condicionado a SC-US3-004 (prueba funcional manual).
- **2026-07-03** — `/analyze` sobre SPEC-013 (7 hallazgos, 0 CRITICAL). Resuelto **A1 (HIGH)**: la síntesis de traza dependía de la forma interna de los bloques `output_integridad/impacto/factibilidad/redactor_mail`, nunca sondeada (sólo `output_fastgate` y el discriminador `null` están verificados). Decisión (Clarifications US3 2026-07-03): el adaptador es **agnóstico a la forma interna** — el estado del paso se decide por presencia/contenido no vacío (nunca leyendo un `resultado` interno) y el resumen serializa el bloque tal cual; la verificación del shape real se difiere al primer envío funcional (SC-US3-004). Se reescribieron FR-US3-004 (regla de estado shape-agnóstica) y FR-US3-005 (resumen sin asumir claves). De paso queda resuelto **A2 (MEDIUM)**: FR-US3-004 explicita el trato de `output_redactor_mail` (presente en ambas ramas) como consecuencia deliberada (aparece `completed` tras etapas `skipped` en la rama de rechazo). A3–A7 quedan como deuda menor (redacción / matices a resolver al implementar).
- **2026-07-03** — Cierre de SPEC-013: prueba funcional manual del usuario OK para las tres User Stories (SC-US1-004 ya estaba; SC-US2-004 y SC-US3-004 confirmados). La spec pasa de `draft` a `active`.
- **2026-07-03** — Implementación de User Story 3 (traza sintetizada del pipeline síncrono). Cambios en `SyncHttpAgentClient`: (1) `send` extiende el cache (`self._bodies`) para retener el body crudo del pipeline junto al veredicto ya cacheado (FR-US3-001), sin llamadas de red extra. (2) `get_trace` deja de devolver vacío y sintetiza un `AgentTrace` desde lo cacheado: un `TraceStep` por etapa en orden fijo `integridad → impacto → factibilidad → fastgate → redactor_mail` (constante `_PIPELINE_STAGES`, claves `output_*` confinadas al adapter), `flow_id=None`, `overall_status="completed"` (FR-US3-002/003/006). (3) Estado por presencia/contenido **agnóstico a la forma interna** (`_has_content`): bloque con contenido → `completed`, ausente/`null`/vacío → `skipped`, nunca `failed` (FR-US3-004, Principio III); consecuencia deliberada verificada en test: el gate que corto-circuitó queda `completed` y `output_redactor_mail` (presente en ambas ramas) queda `completed` tras etapas `skipped`. (4) `_summarize` serializa el bloque tal cual, truncado a 800 chars (FR-US3-005); campos sin dato nativo (`duration_ms`, `child_flow_id`, `started_at`, `completed_at`) en `None`. (5) Fallo técnico o `thread_id` sin cache → `AgentTrace(steps=())` sin excepción (FR-US3-007). El visor `trace_panel.py` (SPEC-007) renderiza sin cambios (FR-US3-008). Tests: 8 casos nuevos en `test_sync_agent_client.py` (orden fijo independiente de claves, corto-circuito, nunca `failed`, resúmenes/truncado, sin cache, fallo técnico). Pipeline local VERDE 10/10 (286 tests). SC-US3-001..003 confirmados por la suite automatizada; **SC-US3-004** (prueba funcional manual) queda pendiente como condición de cierre → la spec sigue en `draft`.
- **2026-07-03** — Implementación de User Story 2. Cambios: (1) `PlatformConfig.effective_endpoint_url` (property, agnóstica): `remote_async` → `chat_url + agent_id + "/chat/completions"` (replica `RemoteAgentClient.send`), `sync_http` → `alt_client_url`; ningún adaptador cambió su contrato. (2) `SuiteResult` gana `endpoint_url: str = ""` propagado en `create()`/`to_dict()`/`from_dict()` con retrocompat (`data.get`), esquema SSOT en [[SPEC-005-run-persistence]]. (3) `estadistica-corridas.csv` gana la columna `endpoint_url` (vacía en fila `TOTAL`), esquema SSOT en [[SPEC-006-batch-suite]]. (4) Composition roots pasan `config.effective_endpoint_url`: `runner.py` (vía `build_suite`, que ganó el parámetro), y `dashboard/app.py` en single-case y batch (session_state `batch_endpoint_url` → `_finalize_batch`). (5) El dashboard muestra la URL como `caption` en tres puntos (envío single-case, vista de última corrida antes de la matriz, y vista batch antes de la matriz), sin que `SuiteMetrics` conozca la URL (separación domain/UI de SPEC-008 intacta). Pipeline local VERDE 10/10 (279 tests). SC-US2-001..003 confirmados por la suite automatizada; **SC-US2-004** (prueba funcional manual) queda pendiente como condición de cierre → la spec sigue en `draft`.
