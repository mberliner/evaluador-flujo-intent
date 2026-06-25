# SPEC-013-client-adapter-selection — Selección de adaptador de cliente para plataformas alternativas

**Estado:** draft
**Iter:** 13
**Formato:** Híbrido
**Depende de:** [[SPEC-000-naming]], [[SPEC-002-agent-client]], [[SPEC-011-agent-under-test]]

## User Story (Priority: P2)

Como operador de la suite, quiero poder configurar contra qué plataforma tecnológica se ejecuta mi perfil de pruebas, para poder evaluar al mismo agente (ej. el clasificador original) cuando este sea migrado a un proveedor diferente, sin modificar el código interno de la suite ni alterar sus métricas.

**Why this priority:** El negocio requiere flexibilidad para evaluar la precisión del modelo en distintas plataformas en la nube. Sin esta capacidad, la suite está rígidamente acoplada a la forma de comunicación (transporte, autenticación y empaquetado de payload) del proveedor original.

**Independent Test:** Levantar el sistema configurando un adaptador de cliente alternativo hacia un mock local y enviar un caso. Verificar que la solicitud HTTP y el payload resultante corresponden al contrato esperado por la plataforma alternativa, y que la respuesta es procesada correctamente por el dominio.

## Clarifications

### Session 2026-06-24

- Q: ¿Cómo deberían definirse y gestionarse las credenciales para los clientes alternativos en el entorno? → A: Añadir variables de entorno genéricas (ej. `ALT_CLIENT_URL`, `ALT_CLIENT_API_KEY`) a `PlatformConfig`, manteniéndolo como único lector del entorno (FR-009).
- Q: ¿Se permite incorporar SDKs de terceros como dependencias del proyecto para implementar los clientes alternativos? → A: Sí, se permite añadir SDKs en `requirements.txt`, confinando su importación estricta a la capa de adaptadores (FR-007).
- Q: ¿Dónde debería residir la lógica condicional que decide instanciar uno u otro adaptador de cliente alternativo? → A: En un nuevo `AgentClientFactory` dentro de la capa `adapters/` para centralizar la lógica de creación y evitar duplicación en los composition roots (FR-005).

## Acceptance Scenarios

1. **Given** que no se especifica una variable de selección de cliente de agente, **When** el sistema se inicializa, **Then** utiliza por defecto el adaptador asincrónico original (`RemoteAgentClient`), asegurando retrocompatibilidad total.
2. **Given** que se especifica un tipo de cliente de agente alternativo en el entorno y sus respectivas credenciales, **When** se envía un caso de prueba, **Then** la suite instancia el nuevo adaptador (que cumple el puerto `AgentClient`), delega la invocación usando su propio protocolo de comunicación y entrega el resultado al evaluador del perfil actual.
3. **Given** un tipo de cliente configurado que no existe en el sistema, **When** la aplicación arranca, **Then** falla inmediatamente con un error de configuración detallado antes de realizar cualquier petición de red.

## Functional Requirements

- **FR-001**: MUST: El sistema lee la variable de entorno `AGENT_CLIENT_TYPE` desde `adapters/platform_config.py` para determinar el tipo de adaptador a instanciar. Si la variable no está presente, su valor por defecto asume el cliente original.
- **FR-002**: MUST: Todo nuevo cliente de agente implementa los 5 métodos del puerto `AgentClient` (`send`, `wait_for_completion`, `get_thread_messages`, `get_final_response`, `get_trace`). Si la plataforma alternativa no soporta historiales o trazas nativas, los métodos `get_thread_messages` y `get_trace` MUST devolver estructuras vacías (ej. `[]` y `AgentTrace` vacío) para satisfacer el protocolo sin romper consumidores.
- **FR-003**: MUST: La construcción del payload específico del proveedor ocurre íntegramente en el adaptador concreto, que recibe el value object `AgentInput` (según se define en [[SPEC-011-agent-under-test]]). El adaptador se encarga de renderizar este input a la estructura esperada por su plataforma y de desempaquetar la respuesta.
- **FR-004**: MUST: Se respeta el principio de nomenclatura agnóstica a tecnología ([[SPEC-000-naming]]). Los identificadores en el código fuente de los nuevos clientes no usarán nombres de proveedores comerciales, empleando sufijos descriptivos sobre el mecanismo (ej. `SyncHttpAgentClient`, `WebSocketAgentClient`, `CustomRestAgentClient`).
- **FR-005**: MUST: Se define un `AgentClientFactory` dentro de la capa `adapters/` con la firma `create(config: PlatformConfig) -> AgentClient`. Este factory encapsula el condicional de creación del cliente y **también** resuelve/instancia el `CredentialProvider` correspondiente, evitando duplicar este cableado en los composition roots.
- **FR-006**: MUST: La validación y requerimiento de variables en `PlatformConfig.from_env()` MUST volverse condicional al `AGENT_CLIENT_TYPE` seleccionado. El set de variables exigidas (ej. las `ES_*` originales vs `ALT_CLIENT_*`) debe depender exclusivamente de la plataforma activa, evitando errores de inicialización por variables ajenas al cliente elegido.
- **FR-007**: MAY: Los clientes alternativos pueden introducir SDKs de terceros en `requirements.txt` para interactuar con plataformas externas. Si lo hacen, la importación y uso de estas dependencias MUST confinarse exclusivamente a los módulos concretos dentro de `src/adapters/` para no contaminar el dominio ni la capa de aplicación.
- **FR-009**: MUST: Las credenciales y endpoints específicos de los clientes alternativos se definen como variables de entorno genéricas y agnósticas al proveedor (ej. `ALT_CLIENT_URL`, `ALT_CLIENT_API_KEY`), leídas exclusivamente por `PlatformConfig` (único lector de `os.environ`). El set concreto exigido para cada cliente queda gobernado por la requeridad condicional de FR-006.
- **FR-008**: MUST: Las anotaciones concretas de tipo en los composition roots (específicamente en `dashboard/app.py`, ej. `tuple[..., RemoteAgentClient, ...]` y los `cast("RemoteAgentClient", ...)`) MUST relajarse al puerto abstracto `AgentClient` para evitar fallos en `mypy --strict` cuando el factory devuelva otros adaptadores.

## Key Entities

- **PlatformConfig** (existente, `adapters/platform_config.py`): Se extiende para leer `AGENT_CLIENT_TYPE` y configuraciones genéricas de base de URL y llaves, aplicables según el adaptador instanciado.
- **AgentClientFactory** (nuevo, `adapters/agent_client_factory.py`): Único responsable de resolver el `CredentialProvider` e instanciar el cliente adecuado (`RemoteAgentClient` u otros) exponiendo el método genérico `create(config) -> AgentClient`.
- **AlternativeAgentClient** (nuevo, `adapters/`): Ejemplo del nuevo adaptador concreto que implementa el puerto `AgentClient` para manejar la comunicación con la plataforma alternativa.

## Success Criteria

- [ ] **SC-001**: La ejecución de la suite sin alterar el `.env` invoca al proveedor original y funciona exactamente igual que antes.
- [ ] **SC-002**: Al cambiar `AGENT_CLIENT_TYPE` hacia un nuevo adaptador registrado, los envíos de casos se enrutan correctamente a través de dicho cliente con sus endpoints correspondientes.
- [ ] **SC-003**: Si `AGENT_CLIENT_TYPE` es inválido, el sistema arroja un error entendible antes de lanzar el dashboard o ejecutar el batch runner.

## Assumptions

- La variable `AGENT_CLIENT_TYPE` (plataforma/transporte) y la variable `AGENT_PROFILE` definida en [[SPEC-011-agent-under-test]] (qué agente/lógica se evalúa) son ejes ortogonales e independientes. Esta spec asume que SPEC-011 entra primero o en conjunto, adoptando la firma de `send(input: AgentInput)` en FR-003 en lugar de `send(form: dict)`.
- La lectura de entorno sigue centralizada en `PlatformConfig`, pero su exigencia se vuelve condicional al tipo de cliente seleccionado (FR-006).
- **Riesgo de orden (drafts encadenados):** FR-003 depende del value object `AgentInput` de [[SPEC-011-agent-under-test]], que aún está en `draft` y sin implementar. Esta spec asume que SPEC-011 se implementa antes o en conjunto; si SPEC-013 avanzara primero, FR-003 debería volver transitoriamente a la firma `send(form: dict)` de [[SPEC-002-agent-client]] y reconciliarse luego.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|-------------|
| FR-001 | Extensión en `adapters/platform_config.py` y tests de valores por defecto |
| FR-002 | Clase del nuevo adaptador concreto y pruebas unitarias usando `responses` o mocks |
| FR-003 | Pruebas unitarias que validan la serialización/deserialización del payload en el adaptador |
| FR-004 | Linter `check_naming.py` sobre `src/adapters/` |
| FR-005 | Unit test de `AgentClientFactory` validando que devuelve la instancia correcta según el config |
| FR-006 | Unit test verificando que la exigencia de variables (missing config error) depende del tipo de cliente activo |
| FR-007 | Verificación de importaciones cruzadas (linter `lint-imports`) que garantiza el aislamiento en `adapters/` |
| FR-009 | Extensión de `PlatformConfig` con lectura de variables genéricas `ALT_CLIENT_*` y tests de parsing |
| FR-008 | Ajuste de anotaciones en `app.py` verificado vía `mypy --strict` corriendo en el pipeline |
| SC-001 | Smoke test utilizando el cliente remoto original |
| SC-002 | Test de integración instanciando diferentes clientes alternativos según configuración mock |
| SC-003 | Prueba unitaria de fallo temprano al arrancar con un tipo de cliente no registrado |

## Fuera de alcance

- Soporte simultáneo a múltiples clientes dentro de una misma corrida (cada corrida usa el cliente definido globalmente).
- Modificación del `MessageBuilder` actual (sólo se modifica cómo el cliente concreto serializa y envía el `AgentInput`).

## Historial

- **2026-06-24** — Spec creada. Motivación: Separar explícitamente el perfil del agente a evaluar de la plataforma de infraestructura tecnológica subyacente donde este se aloja, dando soporte a plataformas alternativas de inferencia sin alterar el circuito de evaluación.
