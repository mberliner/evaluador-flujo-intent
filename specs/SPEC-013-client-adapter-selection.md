# SPEC-013-client-adapter-selection — Selección de adaptador de cliente para plataformas alternativas

**Estado:** active (implementada 2026-07-03; SC-001..004 confirmados)
**Iter:** 13 impl.2026-07-03
**Formato:** Híbrido
**Depende de:** [[SPEC-000-naming]], [[SPEC-002-agent-client]]

## User Story (Priority: P2)

Como operador de la suite, quiero poder configurar contra qué plataforma tecnológica se ejecuta mi perfil de pruebas, para poder evaluar al mismo agente (ej. el clasificador original) cuando este sea migrado a un proveedor diferente, sin modificar el código interno de la suite ni alterar sus métricas.

**Why this priority:** El negocio requiere flexibilidad para evaluar la precisión del modelo en distintas plataformas en la nube. Sin esta capacidad, la suite está rígidamente acoplada a la forma de comunicación (transporte, autenticación y empaquetado de payload) del proveedor original.

**Independent Test:** Levantar el sistema configurando un adaptador de cliente alternativo hacia un mock local y enviar un caso. Verificar que la solicitud HTTP y el payload resultante corresponden al contrato esperado por la plataforma alternativa, y que la respuesta es procesada correctamente por el dominio.

## Clarifications

### Session 2026-06-24

- Q: ¿Cómo deberían definirse y gestionarse las credenciales para los clientes alternativos en el entorno? → A: Añadir variables de entorno genéricas (ej. `ALT_CLIENT_URL`, `ALT_CLIENT_API_KEY`) a `PlatformConfig`, manteniéndolo como único lector del entorno (FR-009).
- Q: ¿Se permite incorporar SDKs de terceros como dependencias del proyecto para implementar los clientes alternativos? → A: Sí, se permite añadir SDKs en `requirements.txt`, confinando su importación estricta a la capa de adaptadores (FR-007).
- Q: ¿Dónde debería residir la lógica condicional que decide instanciar uno u otro adaptador de cliente alternativo? → A: En un nuevo `AgentClientFactory` dentro de la capa `adapters/` para centralizar la lógica de creación y evitar duplicación en los composition roots (FR-005).

### Session 2026-07-02

Verificación empírica contra una plataforma alternativa concreta de flujo de intents (adaptador síncrono REST con auth por header `x-api-key`), sondeando su contrato real.

- Q: ¿El formulario de entrada que exige la plataforma alternativa requiere transformación respecto del schema actual? → A: No. Los 12 campos top-level y sus objetos anidados (`tipo_intent`, `datos_requeridos.otros`) coinciden **1:1** con `schemas/FI_Orquestador_Input.schema.json` y con lo que produce `MessageBuilder`. El adaptador sólo desenvuelve la clave `form` y postea su contenido **plano** en la raíz del body (descartando `id`); no incrusta el payload como texto en un bloque `messages` (FR-010).
- Q: ¿Cómo se mapea la respuesta multi-etapa de la plataforma a la paleta única del dominio (`PALETA_CLASIFICACION`)? → A: La respuesta es un pipeline con corto-circuito: `integridad → impacto → factibilidad → fastgate`. Regla de colapso confirmada con datos: si `fastgate` viene presente → se usa su `clasificacion` (color); si `fastgate` viene `null` (algún gate previo dio `false`) → se emite `Rechazado`. El discriminador es `fastgate is null`, no el mail de salida (que existe en ambas ramas) (FR-011).
- Q: ¿SPEC-013 debe esperar a SPEC-011 (`AgentInput`) para implementarse? → A: No. Se desacopla: la spec adopta la firma vigente `send(form: dict)` porque el `form` de `MessageBuilder` ya coincide 1:1 con la entrada de la plataforma. Se elimina la dependencia y el "riesgo de orden"; la migración a `AgentInput` queda a cargo de SPEC-011 (FR-002, FR-003).
- Q: El orquestador `run_one` es asíncrono (exige `conversation_id` de `send` y lee el veredicto de `get_final_response`), pero `/intents` es síncrona y sin `thread_id`. ¿Cómo se resuelve? → A: Se **encapsula la comunicación en el adaptador** para no depender de sync/async y mantener el flujo conversacional transparente: el adaptador síncrono simula el ciclo (conversation_id sintético + cache en `send`, `wait_for_completion`→True, `get_final_response`→valor cacheado). No se modifican los consumidores ni el puerto (FR-012).
- Q: ¿Cómo se mapean los fallos de transporte (no-200, timeout, forma inesperada)? → A: Igual que el cliente original: fallo técnico → `conversation_id=None` → Indeterminado, sin abortar la corrida. Un `422` es defecto de serialización, no `Rechazado`; el rechazo de negocio es siempre un `200` con `fastgate=null` (FR-013).

## Acceptance Scenarios

1. **Given** que no se especifica una variable de selección de cliente de agente, **When** el sistema se inicializa, **Then** utiliza por defecto el adaptador asincrónico original (`RemoteAgentClient`), asegurando retrocompatibilidad total.
2. **Given** que se especifica un tipo de cliente de agente alternativo en el entorno y sus respectivas credenciales, **When** se envía un caso de prueba, **Then** la suite instancia el nuevo adaptador (que cumple el puerto `AgentClient`), delega la invocación usando su propio protocolo de comunicación y entrega el resultado al evaluador del perfil actual.
3. **Given** un tipo de cliente configurado que no existe en el sistema, **When** la aplicación arranca, **Then** falla inmediatamente con un error de configuración detallado antes de realizar cualquier petición de red.

## Functional Requirements

- **FR-001**: MUST: El sistema lee la variable de entorno `AGENT_CLIENT_TYPE` desde `adapters/platform_config.py` para determinar el tipo de adaptador a instanciar. Valores registrados: `remote_async` (cliente original, `RemoteAgentClient`) y `sync_http` (adaptador síncrono REST, `SyncHttpAgentClient`). Si la variable no está presente, su valor por defecto es `remote_async`. Un valor fuera del registro produce `MissingConfigError` en `from_env()` (SC-003).
- **FR-002**: MUST: Todo nuevo cliente de agente implementa los 5 métodos del puerto `AgentClient` (`send`, `wait_for_completion`, `get_thread_messages`, `get_final_response`, `get_trace`). Esta spec adopta la firma **actual** del puerto, `send(form: dict, conversation_id=None)` de [[SPEC-002-agent-client]], sin modificarla: el `form` que produce `MessageBuilder` ya es el contrato de entrada suficiente (ver FR-010). La eventual migración a `send(input: AgentInput)` queda fuera de alcance y a cargo de [[SPEC-011-agent-under-test]]. Si la plataforma alternativa no soporta historiales o trazas nativas, los métodos `get_thread_messages` y `get_trace` MUST devolver estructuras vacías (ej. `[]` y `AgentTrace` vacío) para satisfacer el protocolo sin romper consumidores.
- **FR-003**: MUST: La construcción del payload específico del proveedor ocurre íntegramente en el adaptador concreto, que recibe el `form: dict` (payload de `MessageBuilder`, `{"form": {...}}`). El adaptador se encarga de renderizar ese input a la estructura esperada por su plataforma (ver FR-010) y de desempaquetar la respuesta (ver FR-011).
- **FR-004**: MUST: Se respeta el principio de nomenclatura agnóstica a tecnología ([[SPEC-000-naming]]). Los identificadores en el código fuente de los nuevos clientes no usarán nombres de proveedores comerciales, empleando sufijos descriptivos sobre el mecanismo (ej. `SyncHttpAgentClient`, `WebSocketAgentClient`, `CustomRestAgentClient`).
- **FR-005**: MUST: Se define un `AgentClientFactory` dentro de la capa `adapters/` con la firma `create(config: PlatformConfig) -> AgentClient`. Este factory encapsula el condicional de creación del cliente y **también** resuelve/instancia el `CredentialProvider` correspondiente, evitando duplicar este cableado en los composition roots.
- **FR-006**: MUST: La validación y requerimiento de variables en `PlatformConfig.from_env()` MUST volverse condicional al `AGENT_CLIENT_TYPE` seleccionado. El set de variables exigidas (ej. las `ES_*` originales vs `ALT_CLIENT_*`) debe depender exclusivamente de la plataforma activa, evitando errores de inicialización por variables ajenas al cliente elegido.
- **FR-007**: MAY: Los clientes alternativos pueden introducir SDKs de terceros en `requirements.txt` para interactuar con plataformas externas. Si lo hacen, la importación y uso de estas dependencias MUST confinarse exclusivamente a los módulos concretos dentro de `src/adapters/` para no contaminar el dominio ni la capa de aplicación.
- **FR-008**: MUST: Las anotaciones concretas de tipo en los composition roots (específicamente en `dashboard/app.py`, ej. `tuple[..., RemoteAgentClient, ...]` y los `cast("RemoteAgentClient", ...)`) MUST relajarse al puerto abstracto `AgentClient` para evitar fallos en `mypy --strict` cuando el factory devuelva otros adaptadores.
- **FR-009**: MUST: Las credenciales y endpoints específicos de los clientes alternativos se definen como variables de entorno genéricas y agnósticas al proveedor (ej. `ALT_CLIENT_URL`, `ALT_CLIENT_API_KEY`), leídas exclusivamente por `PlatformConfig` (único lector de `os.environ`). El set concreto exigido para cada cliente queda gobernado por la requeridad condicional de FR-006.
- **FR-010**: MUST: Cuando la plataforma alternativa consume el formulario de intent como JSON estructurado nativo (no como texto embebido), el adaptador MUST enviar el contenido del `form` **plano en la raíz del body**, sin el envoltorio `form` ni el `id` del caso. El mapeo de campos es identidad: los 12 campos y sus objetos anidados (`tipo_intent.{negocio,operativo,capacidad_equipos,tecnico_arquitectural}`, `datos_requeridos.{ninguno,datos_publicos,datos_operativos,datos_personales,datos_confidenciales,otros.{estado,message}}`) coinciden 1:1 con `schemas/FI_Orquestador_Input.schema.json`; el adaptador NO transforma nombres ni tipos. Nota: la plataforma puede exigir como obligatorios campos que el schema declara con `default` (ej. `restricciones`, `supuesto_riesgo`); esto no impacta porque `TestCase` ya garantiza su presencia no vacía.
- **FR-011**: MUST: El adaptador MUST colapsar la respuesta multi-etapa de la plataforma a un único valor de `PALETA_CLASIFICACION` antes de construir el `AgentResponse.content`, aplicando: (a) si el bloque de clasificación final (`output_fastgate` — las claves del body real llevan prefijo `output_`, verificado funcionalmente 2026-07-03) viene presente, usar su color **por pass-through genérico** —depositar `output_fastgate.clasificacion` tal cual (la plataforma lo emite en mayúsculas, ej. `"VERDE"`), sin enumerar ni hardcodear la lista de colores—; (b) si dicho bloque viene con valor `null` —porque un gate previo (`integridad`, `impacto` o `factibilidad`) resolvió `false` y el pipeline hizo corto-circuito— emitir `Rechazado`. El discriminador MUST ser el valor `null` del bloque de clasificación final (cuya clave está presente en ambas ramas del pipeline, verificado empíricamente), no el bloque de mail de salida (también presente en ambas ramas). Un body `200` **sin la clave** del bloque de clasificación, o con un bloque sin color legible, no pertenece a ninguna rama del pipeline: es forma inesperada y se trata como fallo técnico (FR-013), nunca como `Rechazado`. El adaptador deposita el valor colapsado en `AgentResponse.content` y la canonización a la paleta (title-case, case-insensitive sobre `PALETA_CLASIFICACION` completa) queda a cargo de `ClassificationEvaluator.extract`; así cualquier color que emita la plataforma se soporta sin cambios en el adaptador.
- **FR-012**: MUST: La comunicación con la plataforma se encapsula íntegramente en el adaptador, que MUST honrar el contrato conversacional del puerto `AgentClient` **con independencia de si el transporte subyacente es síncrono o asíncrono**, de forma transparente para `run_one`, el dashboard y el runner (ningún consumidor se modifica según el modo de transporte). Para un adaptador síncrono (ej. la plataforma `/intents`, que responde en una sola llamada y sin `thread_id`): (a) `send(form)` ejecuta la invocación completa, cachea el resultado colapsado (FR-011) y devuelve un `AgentResponse` con un `conversation_id` **sintético no nulo** —para satisfacer la guarda de `run_one` que aborta ante la ausencia de `thread_id`—; (b) `wait_for_completion` MUST devolver `True` inmediatamente; (c) `get_final_response` MUST devolver el valor cacheado asociado a ese `conversation_id`, que es la superficie desde la cual el evaluador lee el veredicto. Un adaptador asíncrono conserva el comportamiento de polling original. Esta encapsulación mantiene intacto el flujo conversacional del proceso.
- **FR-013**: MUST: Los **fallos técnicos** del adaptador (HTTP no-200 —incl. `422`/`5xx`—, timeout de red, o respuesta con forma inesperada) MUST mapearse a un `AgentResponse` con `conversation_id=None`, de modo que `run_one` produzca un resultado **Indeterminado** anotado sin abortar la corrida (consistente con `RemoteAgentClient` y con la tolerancia a fallos de `run_suite`). Un fallo técnico MUST NOT interpretarse como veredicto de negocio: el `422` (payload inválido) indica un defecto de serialización del adaptador/caso, no un `Rechazado`; `Rechazado` proviene exclusivamente de un `200` con corto-circuito de gates (FR-011). Se preserva el Principio III: ante fallo, no se infiere clasificación.

## Key Entities

- **PlatformConfig** (existente, `adapters/platform_config.py`): Se extiende para leer `AGENT_CLIENT_TYPE` y configuraciones genéricas de base de URL y llaves, aplicables según el adaptador instanciado.
- **AgentClientFactory** (nuevo, `adapters/agent_client_factory.py`): Único responsable de resolver el `CredentialProvider` e instanciar el cliente adecuado (`RemoteAgentClient` u otros) exponiendo el método genérico `create(config) -> AgentClient`.
- **SyncHttpAgentClient** (nuevo, `adapters/sync_agent_client.py`): Adaptador concreto que implementa el puerto `AgentClient` para la plataforma alternativa síncrona REST (auth por header `x-api-key`), aplicando FR-010..FR-013.
- **StaticCredentialProvider** (nuevo, `adapters/token_provider.py`): Implementación mínima del puerto `CredentialProvider` que devuelve una llave fija de configuración (la plataforma alternativa no tiene ciclo de token/refresh).

## Success Criteria

- [x] **SC-001**: La ejecución de la suite sin alterar el `.env` invoca al proveedor original y funciona exactamente igual que antes.
- [x] **SC-002**: Al cambiar `AGENT_CLIENT_TYPE` hacia un nuevo adaptador registrado, los envíos de casos se enrutan correctamente a través de dicho cliente con sus endpoints correspondientes.
- [x] **SC-003**: Si `AGENT_CLIENT_TYPE` es inválido, el sistema arroja un error entendible antes de lanzar el dashboard o ejecutar el batch runner.
- [x] **SC-004**: Prueba funcional manual del usuario, condición de cierre de la spec: (a) un caso real enviado con `AGENT_CLIENT_TYPE=sync_http` contra la plataforma alternativa devuelve un veredicto correcto por el circuito completo (dashboard o runner); (b) el camino por defecto (sin `AGENT_CLIENT_TYPE`) sigue operando contra el proveedor original. OK confirmado por el usuario el 2026-07-03.

## Assumptions

- **Desacople de [[SPEC-011-agent-under-test]]:** esta spec es independiente de SPEC-011. Adopta la firma vigente `send(form: dict)` de [[SPEC-002-agent-client]] (verificado 1:1 contra el contrato de la plataforma, FR-010), de modo que puede implementarse sin esperar el value object `AgentInput`. Si SPEC-011 introduce `send(input: AgentInput)` más adelante, la reconciliación de firma es responsabilidad de esa spec, no de esta.
- La variable `AGENT_CLIENT_TYPE` (plataforma/transporte) y la de perfil de agente de [[SPEC-011-agent-under-test]] (qué agente/lógica se evalúa) son ejes ortogonales e independientes.
- La lectura de entorno sigue centralizada en `PlatformConfig`, pero su exigencia se vuelve condicional al tipo de cliente seleccionado (FR-006).

## Coverage mapping

| Requisito | Cubierto por |
|-----------|-------------|
| FR-001 | `tests/unit/test_platform_config.py` (tipo por defecto `remote_async`, lectura de `AGENT_CLIENT_TYPE`) |
| FR-002 | `tests/unit/test_sync_agent_client.py` (los 5 métodos del puerto; `get_thread_messages`→`[]`, `get_trace`→traza vacía) |
| FR-003 | `tests/unit/test_sync_agent_client.py` (serialización del payload y desempaquetado de la respuesta en el adaptador) |
| FR-004 | Linter `tools/check_naming.py` sobre `src/adapters/` (pipeline) |
| FR-005 | `tests/unit/test_agent_client_factory.py` (instancia correcta según config; resolución del `CredentialProvider`) |
| FR-006 | `tests/unit/test_platform_config.py` (exigencia de variables condicional al tipo de cliente activo) |
| FR-007 | Linter `lint-imports` (pipeline); no se agregaron SDKs (el adaptador usa `requests`, ya presente) |
| FR-008 | Anotaciones de `dashboard/app.py` relajadas al puerto `AgentClient`, verificado vía `mypy --strict` (pipeline) |
| FR-009 | `tests/unit/test_platform_config.py` (parsing de `ALT_CLIENT_URL` / `ALT_CLIENT_API_KEY`) |
| FR-010 | `tests/unit/test_sync_agent_client.py` (body plano sin envoltorio `form` ni `id`; identidad de campos contra `schemas/FI_Orquestador_Input.schema.json`) |
| FR-011 | `tests/unit/test_sync_agent_client.py` (rama color por pass-through, rama corto-circuito → `Rechazado`, body sin bloque → fallo técnico) |
| FR-012 | `tests/unit/test_sync_agent_client.py` (`conversation_id` sintético + cache; `wait_for_completion`→`True`; `get_final_response` cacheado) + `tests/integration/test_sync_client_run_one.py` (`run_one` sin modificar la capa de aplicación) |
| FR-013 | `tests/unit/test_sync_agent_client.py` (no-200 `422`/`5xx`, timeout y forma inesperada → `conversation_id=None`, nunca `Rechazado`) |
| SC-001 | `tests/unit/test_platform_config.py` (default) + `tests/unit/test_remote_agent_client.py` (cliente original intacto) |
| SC-002 | `tests/unit/test_agent_client_factory.py` + `tests/integration/test_sync_client_run_one.py` |
| SC-003 | `tests/unit/test_platform_config.py` (tipo inválido → `MissingConfigError`) + `tests/unit/test_agent_client_factory.py` (tipo no registrado → error) |
| SC-004 | Prueba funcional manual del usuario contra la plataforma alternativa real y el proveedor original (no automatizable; se registra el OK en Historial) |

## Fuera de alcance

- Soporte simultáneo a múltiples clientes dentro de una misma corrida (cada corrida usa el cliente definido globalmente).
- Modificación del `MessageBuilder` actual (sólo se modifica cómo el cliente concreto serializa y envía el `form`).

## Historial

- **2026-06-24** — Spec creada. Motivación: Separar explícitamente el perfil del agente a evaluar de la plataforma de infraestructura tecnológica subyacente donde este se aloja, dando soporte a plataformas alternativas de inferencia sin alterar el circuito de evaluación.
- **2026-07-02** — Verificación empírica contra una plataforma alternativa concreta (adaptador síncrono REST, auth `x-api-key`). Se confirmó por sondeo del contrato real: (1) el formulario de entrada coincide 1:1 con el schema actual, sin transformación de campos (FR-010); (2) la respuesta es un pipeline con corto-circuito (`integridad → impacto → factibilidad → fastgate`), y su colapso a la paleta del dominio se rige por la presencia/ausencia del bloque de clasificación final, mapeando la rama de corto-circuito a `Rechazado` (FR-011). Se agregaron FR-010 y FR-011 con su cobertura.
- **2026-07-02** — Desacople de [[SPEC-011-agent-under-test]]. Habilitado por la verificación anterior (el `form` coincide 1:1 con la plataforma), FR-002/FR-003 vuelven a la firma vigente `send(form: dict)` en vez de `send(input: AgentInput)`. Se quitó SPEC-011 de `Depende de` y se eliminó el "riesgo de orden" de Assumptions. SPEC-013 queda implementable de forma autónoma.
- **2026-07-03** — Implementación (Iter 13, spec → active). Decisiones de reconciliación spec↔código: (1) FR-001 fija los valores registrados `remote_async` (default) y `sync_http`; el tipo inválido falla en `from_env()` con `MissingConfigError` y el factory tiene su propio `UnknownClientTypeError` defensivo. (2) FR-011 se precisó: el discriminador de corto-circuito es el bloque final **presente con valor `null`** (verificado empíricamente que la clave existe en ambas ramas); un body sin la clave o sin color legible es forma inesperada → fallo técnico (FR-013), nunca `Rechazado`. (3) `AGENT_ID` pasa a ser opcional para `sync_http` (etiqueta de metadata de corridas, fallback al tipo de cliente). (4) FR-005: `AgentClientFactory` expone además `resolve_credentials(config)` para que el dashboard conserve la validación anticipada de credenciales sin duplicar el cableado. (5) FR-007 no se ejerció: el adaptador usa `requests` (ya presente), sin SDKs nuevos. Entidades: `SyncHttpAgentClient` (`adapters/sync_agent_client.py`), `AgentClientFactory`, `StaticCredentialProvider`. La spec permanece en `draft`: SC-001..003 quedaron confirmados por la suite automatizada y se agregó **SC-004** (prueba funcional manual del usuario) como condición explícita de cierre → `active`.
- **2026-07-03** — Reconciliación por prueba funcional (spec viva): el primer envío real al endpoint devolvió `200` con las claves del pipeline prefijadas — `output_integridad`, `output_impacto`, `output_factibilidad`, `output_fastgate`, `output_redactor_mail` — a diferencia del sondeo del 2026-07-02 que las registró sin prefijo. El color viene en `output_fastgate.clasificacion` en mayúsculas (`"VERDE"`); el pass-through + canonización del evaluador lo cubren sin cambios. Se corrigió `_FINAL_BLOCK_KEY` en el adaptador y FR-011; la rama de fallo técnico (clave ausente → Indeterminado) funcionó según lo especificado (FR-013) en ese primer intento.
- **2026-07-03** — Cierre: SC-004 tildado con OK explícito del usuario (prueba funcional manual confirmada: `sync_http` contra la plataforma alternativa real y camino por defecto contra el proveedor original). Spec pasa de `draft` a `active`.
