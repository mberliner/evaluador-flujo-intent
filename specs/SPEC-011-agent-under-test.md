# SPEC-011-agent-under-test — Selección del agente bajo prueba (perfiles)

**Estado:** draft
**Iter:** 11
**Formato:** Híbrido
**Relacionada con:** [[SPEC-002-agent-client]], [[SPEC-002b-message-builder]], [[SPEC-003-classification-evaluator]], [[SPEC-012-translation-evaluator]]

## User Story (Priority: P1)

Como operador de la suite quiero **elegir contra qué agente se ejecutan las pruebas** (hoy el clasificador de riesgo; mañana el traductor de intents u otro), sin editar código, para reutilizar el mismo circuito de envío, persistencia y métricas con agentes que tienen contratos de entrada/salida distintos.

**Why this priority:** sin selección de agente, la suite está cableada a un único contrato (form estructurado → clasificación). Es el prerrequisito que habilita probar el agente traductor ([[SPEC-012-translation-evaluator]]): mientras el agente bajo prueba sea fijo, no hay dónde enchufar un builder de entrada ni un evaluador distintos.

**Independent Test:** con dos perfiles registrados, fijar la selección en la configuración a cada uno y verificar que el sistema resuelve el `agent_id`, el constructor de entrada y el evaluador correspondientes a ese perfil — verificable sin invocar al agente, inspeccionando el perfil resuelto.

## Clarifications

### Session 2026-06-09

- Q: ¿El dashboard solo refleja el perfil del `.env` (read-only) o ofrece un selector interactivo para cambiarlo en caliente? → A: Solo refleja; el `.env` es el único mecanismo de selección. El dashboard muestra el perfil activo como indicador de lectura y adapta el formulario, sin selector interactivo. Consecuencia: el perfil activo es global y se fija al arrancar; no hay estado de sesión ni edición simultánea, por lo que no aplica resolución de conflictos por concurrencia.
- Q: ¿Nombres exactos de la variable de selección de perfil y del `agent_id` del traductor? → A: Esquema uniforme `AGENT_ID_<PERFIL>`. Selección: `AGENT_PROFILE` (valores `clasificador` | `traductor`; default `clasificador`). `agent_id` por perfil: `AGENT_ID_CLASIFICADOR` y `AGENT_ID_TRADUCTOR`. `AGENT_ID` se conserva como **alias retrocompatible** del clasificador: si `AGENT_ID_CLASIFICADOR` no está presente, el clasificador resuelve su `agent_id` desde `AGENT_ID`.
- Q: ¿Qué contrato común usan el constructor de entrada y `AgentClient.send`, dado que el clasificador produce un `{form}` estructurado y el traductor texto natural? → A: Un **value object de dominio `AgentInput`** (variante estructurada | variante texto). El constructor de entrada (`build/`) devuelve un `AgentInput`; el adapter (`AgentClient.send`) lo recibe y **lo renderiza al payload del proveedor según la variante**. Toda la serialización y el conocimiento del formato quedan en el adapter (se respeta ADR-001 y la regla de `build/` puro, sin tocar `ARCHITECTURE.md`). Elegida por pureza de capas frente a mover `json.dumps` a `build/` (opción descartada por contradecir ADR-001).
- Q: ¿Qué tipo de retorno concreto declara el puerto `Evaluator`, dado que el resultado del clasificador y el del traductor tienen forma distinta? → A: Un **supertipo común `EvaluatedResult`** en `domain/` (`case_id` + veredicto tri-estado pass/fail/indeterminado + `to_dict()`). El puerto retorna ese supertipo (no `Any`, para que mypy capture incompatibilidades); `TestResult` y el resultado de traducción lo cumplen y cada uno agrega su detalle. Persistencia y render se apoyan en la superficie común; la matriz de confusión (SPEC-008) sigue siendo específica de clasificación. Elegida por uniformidad del circuito frente a forzar `TestResult` o ramificar por perfil.

## Acceptance Scenarios

1. **Given** la configuración sin selección explícita de perfil, **When** el sistema resuelve el agente bajo prueba, **Then** usa el perfil **clasificador** (comportamiento actual: `message_builder` + evaluador de clasificación + `AGENT_ID` actual) — compatibilidad hacia atrás.
2. **Given** la configuración con el perfil **traductor** seleccionado, **When** el sistema resuelve el agente bajo prueba, **Then** expone el `agent_id` del traductor, su constructor de entrada de texto natural y su evaluador de traducción ([[SPEC-012-translation-evaluator]]).
3. **Given** una selección de perfil que no existe en el registro, **When** el sistema arranca, **Then** falla con un error de configuración legible que enumera los perfiles válidos, sin invocar al agente.
4. **Given** un perfil seleccionado cuyo `agent_id` no está configurado, **When** el sistema arranca, **Then** falla con el mismo tipo de error de configuración (variable faltante), reutilizando el mecanismo de [[SPEC-002-agent-client]].
5. **Given** cualquier perfil seleccionado, **When** se ejecuta un caso (modo simple o batch), **Then** el **comportamiento** del circuito de envío, espera de completitud, persistencia y render se preserva; lo específico del perfil son el constructor de entrada y el evaluador. (La habilitación de esto requiere un refactor único —firma de `AgentClient.send` vía `AgentInput` (FR-014) y campo `profile_id` en `SuiteResult` (FR-013)— tras el cual el circuito no vuelve a cambiar por perfil.)

### Edge Cases

- MUST: La corrida persistida registra **qué perfil** se usó, además del `agent_id`, mediante un campo `profile_id` explícito en `SuiteResult` (ver FR-013; no se deriva del `agent_id`).
- MUST: Cambiar de perfil entre corridas no mezcla resultados: cada corrida es de un solo perfil.
- N/A (concurrencia): el perfil activo es global y se fija por `.env` al arrancar (no hay selector en caliente, FR-008), por lo que **no existe edición simultánea del perfil ni resolución de conflictos** dentro de una instancia. Cambiar de perfil implica reconfigurar el `.env` y reiniciar el proceso.

## Functional Requirements

- **FR-001**: MUST: El sistema define el concepto **perfil de agente bajo prueba** como la tupla `(identificador de perfil, agent_id, constructor de entrada, evaluador de respuesta)`. El perfil es la unidad que se selecciona.
- **FR-002**: MUST: Existe un **registro de perfiles** que compone una pieza de `build/` (constructor de entrada) con una pieza de `domain/` (evaluador). El registro vive en **`src/application/`** (capa de composición que ya importa de `build/` y `domain/`; no en `domain/`, que no importa de `build/` ni `adapters/`). El registro es **puro**: recibe el `profile_id` activo como dato de entrada (un string) y **no** lee `os.environ` ni importa `adapters/` — la lectura del entorno y la selección viven en `adapters/platform_config.py` (FR-004), y el composition root (`runner.py` / `dashboard/`) cablea ambos. Esto preserva la regla `application ↛ adapters` (Principio II).
- **FR-003**: MUST: El registro incluye al menos dos perfiles: **clasificador** (actual: constructor `message_builder.build` + evaluador de clasificación de [[SPEC-003-classification-evaluator]]) y **traductor** (constructor de entrada de texto natural + evaluador de [[SPEC-012-translation-evaluator]]).
- **FR-004**: MUST: La **selección del perfil activo** se hace por la variable de entorno dedicada **`AGENT_PROFILE`** (valores válidos: `clasificador` | `traductor`), leída únicamente por `adapters/platform_config.py` (único punto que conoce nombres de variables de entorno). Si la variable no está, el default es **clasificador** (compatibilidad con setups existentes).
- **FR-005**: MUST: Cada perfil resuelve su propio `agent_id` desde configuración con el esquema uniforme **`AGENT_ID_<PERFIL>`**: `AGENT_ID_CLASIFICADOR` y `AGENT_ID_TRADUCTOR`. La variable **`AGENT_ID`** se conserva como **alias retrocompatible del clasificador**: si `AGENT_ID_CLASIFICADOR` no está presente, el clasificador resuelve su `agent_id` desde `AGENT_ID` (si ambas están, `AGENT_ID_CLASIFICADOR` tiene precedencia). El `.env.example` documenta las variables de cada perfil.
- **FR-006**: MUST: Una selección de perfil inexistente o un `agent_id` faltante para el perfil seleccionado producen un error de configuración legible (`MissingConfigError` o equivalente) **antes** de cualquier llamada al agente, enumerando los perfiles válidos.
- **FR-007**: MUST: El runner headless (`python -m src.runner`) acepta la selección de perfil por configuración y, opcionalmente, por el argumento de línea de comandos canónico **`--perfil`** (con alias `--agent`), cuyo valor usa el **mismo vocabulario** que `AGENT_PROFILE` (`clasificador` | `traductor`) y tiene **precedencia** sobre la variable de entorno.
- **FR-008**: MUST: El dashboard refleja el **perfil activo** de forma visible al operador (qué agente se está probando) como **indicador de lectura** y adapta el formulario/entrada de carga al constructor del perfil seleccionado. MUST NOT: el dashboard **no** ofrece un selector interactivo para cambiar de perfil en caliente; la selección es exclusiva del `.env` (FR-004) y se fija al arrancar.
- **FR-009**: MUST: Ningún identificador de código nombra proveedor, framework de UI, formato de serialización ni protocolo de auth (SPEC-000-naming). Los nombres de perfil describen *qué hace* el agente (clasificador, traductor), no la tecnología.
- **FR-010**: SHOULD: El registro está diseñado para **extenderse** a más perfiles agregando una entrada (identificador + agent_id + constructor + evaluador) sin modificar el runner ni el dashboard.
- **FR-011**: MUST: Se define el **puerto `Evaluator`** en `src/domain/ports.py` (protocolo estructural `typing.Protocol`, consistente con los puertos existentes `AgentClient`/`CredentialProvider`/`RunRepository` — no `ABC`). El puerto retorna un **supertipo común de resultado evaluado** (ver `EvaluatedResult`, FR-015), **no `Any`**, de modo que mypy capture incompatibilidades en compilación. Los use-cases de `application/` y los composition roots dependen de **este puerto y de ese supertipo**, no del evaluador ni del resultado concreto. El `ClassificationEvaluator` existente pasa a cumplir el puerto sin heredar de él.
- **FR-012**: MUST: Los use-cases `run_one` / `run_batch` / `build_suite` (`src/application/run_suite.py`) reciben el **constructor de entrada** y el **evaluador** del perfil activo **por parámetro**, y dejan de importar `message_builder` y `ClassificationEvaluator` de forma directa. El comportamiento del perfil clasificador es idéntico al actual cuando se le inyectan su constructor y su evaluador (compatibilidad hacia atrás, SC-001).
- **FR-013**: MUST: La corrida persistida registra el **`profile_id`** del perfil activo además del `agent_id`. Esto **extiende el modelo `SuiteResult`** de [[SPEC-005-run-persistence]] con un campo `profile_id`; el perfil queda trazable de forma explícita (no derivado del `agent_id`, que es ambiguo por el alias `AGENT_ID`↔`AGENT_ID_CLASIFICADOR`). La reconciliación de SPEC-005 se registra en su Historial.
- **FR-014**: MUST: El **constructor de entrada** de cada perfil es un callable `(case) -> AgentInput`, donde **`AgentInput`** es un value object de `domain/` con dos variantes: **estructurada** (lleva el `{form}` como dato, p. ej. el clasificador) y **texto** (lleva texto natural, p. ej. el traductor). El puerto `AgentClient.send` recibe un `AgentInput` y **lo renderiza al payload del proveedor según la variante** (la variante estructurada se serializa a JSON; la de texto se envía como contenido crudo). Toda la serialización y el conocimiento del formato del proveedor permanecen en el adapter (ADR-001; `build/` sigue puro). Esto **modifica la firma de `AgentClient.send`** (hoy `send(form: dict)`) → reconciliar [[SPEC-002-agent-client]]; y **cambia el tipo de retorno del constructor del clasificador** (`message_builder.build`, hoy `dict` → `AgentInput` variante estructurada) → reconciliar [[SPEC-002b-message-builder]]. Ambas reconciliaciones se registran en el Historial de las specs respectivas al implementar.
- **FR-015**: MUST: Se define en `domain/` un **supertipo común de resultado evaluado** (`EvaluatedResult`) que expone la superficie compartida: `case_id`, **veredicto tri-estado** (pass / fail / indeterminado) y `to_dict()` serializable. `TestResult` (clasificación) y el resultado de traducción ([[SPEC-012-translation-evaluator]]) lo cumplen; cada uno agrega su detalle propio. La persistencia ([[SPEC-005-run-persistence]]) y el render del dashboard se apoyan en esta superficie común; la métrica de matriz de confusión ([[SPEC-008-suite-metrics]]) sigue siendo específica de la clasificación (no se generaliza acá).

## Key Entities

- **AgentProfile** (nuevo, `src/application/`): tupla `(profile_id, agent_id, input_builder, response_evaluator)`. Atributos clave: identificador agnóstico, referencia al constructor de entrada (`build/`) y al evaluador (`domain/`). Vive en `application/` (no en `domain/`) porque referencia `build/`.
- **Registro de perfiles** (nuevo, `src/application/`): colección de `AgentProfile` indexada por `profile_id`; expone la resolución `resolve(profile_id) -> AgentProfile` y la lista de `profile_id` válidos. Es **puro**: recibe el `profile_id` ya leído del entorno por `PlatformConfig`; no lee `os.environ` ni importa `adapters/`.
- **Evaluator** (puerto nuevo en `domain/ports.py`, `typing.Protocol`): abstrae `evaluate(case, agent_response)`, implementado por el evaluador de clasificación (existente) y el de traducción ([[SPEC-012-translation-evaluator]]); permite que runner y dashboard dependan de la abstracción, no del concreto (FR-011). Retorna el supertipo común `EvaluatedResult` (FR-011/FR-015).
- **AgentInput** (nuevo, `domain/`): value object inmutable que representa la entrada a enviar al agente, con dos variantes — **estructurada** (transporta el `{form}`) y **texto** (transporta texto natural). Es la salida del constructor de entrada de cada perfil y la entrada de `AgentClient.send`, que lo renderiza al payload del proveedor. Puro, sin I/O; identificador agnóstico al formato (FR-014, SPEC-000-naming).
- **EvaluatedResult** (nuevo, `domain/`): supertipo común del resultado de evaluación — `case_id` + veredicto tri-estado (pass/fail/indeterminado) + `to_dict()`. Es el **retorno del puerto `Evaluator`** (FR-011/FR-015). Lo cumplen `TestResult` (existente) y el resultado de traducción ([[SPEC-012-translation-evaluator]]); persistencia y render dependen de esta superficie, no del concreto.
- **PlatformConfig** (existente, `adapters/platform_config.py`): se extiende para leer `AGENT_PROFILE` y resolver el `agent_id` del perfil activo (`AGENT_ID_<PERFIL>`). Sigue siendo el único lector de `os.environ`.
- **SuiteResult** (existente, SPEC-005): hoy guarda `agent_id`; se **extiende con `profile_id`** para registrar de forma explícita y trazable el perfil de la corrida (FR-013).

## Success Criteria

- [ ] **SC-001**: Con la selección por defecto (sin variable), el sistema resuelve el perfil clasificador y una corrida existente reproduce el comportamiento actual sin cambios observables.
- [ ] **SC-002**: Fijando la selección al perfil traductor, el sistema resuelve el `agent_id`, el constructor de entrada y el evaluador del traductor — verificable sin llamar al agente.
- [ ] **SC-003**: Una selección de perfil inexistente o un `agent_id` faltante producen un error de configuración legible antes de cualquier llamada al agente.
- [ ] **SC-004**: El runner headless permite seleccionar el perfil por configuración y por argumento CLI (con precedencia del argumento).
- [ ] **SC-005** *(verificación funcional en la app real)*: En el dashboard, el operador ve el perfil activo y puede ejecutar un caso contra el perfil seleccionado de punta a punta.

## Assumptions

- Los dos perfiles iniciales (clasificador y traductor) son estables; otros perfiles se agregarán por configuración a futuro (el usuario indicó que "posiblemente se extienda").
- El mecanismo de selección primario es la configuración de entorno (el usuario indicó selección "en `.env`"); el argumento CLI y el reflejo en el dashboard son convenientes, no sustituyen al `.env`.
- El circuito de envío/espera/persistencia ([[SPEC-002-agent-client]], SPEC-005/006) es agnóstico al contrato del agente y se reutiliza tal cual; lo único específico del agente son el constructor de entrada y el evaluador.
- Los puertos del sistema se modelan con `typing.Protocol` (conformidad estructural verificada por `mypy --strict`), no con `ABC`; el puerto `Evaluator` nuevo sigue esa convención. La garantía de conformidad depende de que el pipeline corra mypy en verde (sin mypy, una incompatibilidad de puerto recién aparecería en runtime).

## Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-001, FR-002, FR-003, FR-010 | módulo de composición de perfiles + tests de resolución de perfil (clasificador/traductor) |
| FR-004, FR-005, FR-006 | extensión de `adapters/platform_config.py` + tests de selección, default y errores de configuración |
| FR-007 | argumento `--agent`/`--perfil` en `src/runner.py` + test de precedencia CLI sobre entorno |
| FR-008 | render del perfil activo en `src/dashboard/app.py` + SC-005 (verificación funcional) |
| FR-009 | `tools/check_naming.py` sobre `src/` |
| FR-011 | puerto `Evaluator` en `src/domain/ports.py` + `ClassificationEvaluator` conformándolo + chequeo `mypy --strict` de los puntos de inyección |
| FR-012 | firmas de `run_one`/`run_batch`/`build_suite` parametrizadas (`src/application/run_suite.py`) + test que inyecta constructor+evaluador del perfil clasificador y reproduce el resultado actual |
| FR-013 | campo `profile_id` en `SuiteResult` (extensión SPEC-005) + test de persistencia/lectura que conserva el `profile_id` de la corrida |
| FR-014 | value object `AgentInput` en `src/domain/` + render por variante en `AgentClient.send` (`adapters/remote_agent_client.py`) + tests de construcción (clasificador→estructurada, traductor→texto) y de render del payload (reconcilia SPEC-002) |
| FR-015 | supertipo `EvaluatedResult` en `src/domain/` + `TestResult` conformándolo + chequeo `mypy --strict` de que el puerto `Evaluator` retorna el supertipo + test de `to_dict()`/veredicto sobre la superficie común |
| SC-001..SC-003 | tests de resolución de perfil y de configuración (sin invocar al agente) |
| SC-004 | test del runner con argumento de perfil |
| SC-005 | verificación funcional en el dashboard (último SC en cerrarse) |

## Fuera de alcance

- El contrato de entrada/salida y la evaluación del traductor → [[SPEC-012-translation-evaluator]] (esta spec solo provee el punto de selección y la abstracción de evaluador).
- Ejecutar varios perfiles en una misma corrida o comparar perfiles entre sí: cada corrida es de un solo perfil.
- Descubrimiento dinámico de agentes desde la plataforma para poblar el registro (el registro es estático/configurado); `tools/connection_check.py --list-agents` sigue siendo la vía de inspección manual.

## Historial

- **2026-06-04** — Spec creada (draft). Motivación: se verificó la existencia del agente `traductor_intents` (id `3da38f33-3788-44c2-b326-fdbf3cd0605c`) en la instancia; su contrato es el **inverso** del clasificador (entra texto natural, sale el `{form}` estructurado), por lo que reutilizar el circuito exige poder seleccionar el agente bajo prueba y, con él, su constructor de entrada y su evaluador. Selección por `.env` con default al perfil clasificador (decisión del usuario).
- **2026-06-09** — `/clarify` (sesión 2026-06-09): resueltos los dos `[NEEDS CLARIFICATION]`. (1) El dashboard **solo refleja** el perfil del `.env` (indicador read-only, sin selector interactivo): el perfil es global y se fija al arrancar, por lo que no hay concurrencia ni resolución de conflictos. (2) Esquema de variables: `AGENT_PROFILE` para la selección (default `clasificador`) y `AGENT_ID_<PERFIL>` (`AGENT_ID_CLASIFICADOR`, `AGENT_ID_TRADUCTOR`), con `AGENT_ID` como alias retrocompatible del clasificador. Tocadas: Clarifications (nueva), FR-004, FR-005, FR-008, Edge Cases.
- **2026-06-09** — `/analyze` + redacción de cierre de gaps. El análisis semántico detectó requisitos estructurales implícitos sin FR (patrón `run_id`). Agregados: **FR-011** (puerto `Evaluator` en `domain/ports.py`, los use-cases dependen de la abstracción), **FR-012** (parametrizar constructor de entrada + evaluador en `application/run_suite.py`, hoy hardcodeados), **FR-013** (persistir `profile_id` explícito en `SuiteResult`, extiende SPEC-005). Aclarados por redacción (sin requerir decisión del usuario): el registro vive en `src/application/` y es **puro** (recibe `profile_id`, no lee entorno ni importa `adapters/`), preservando `application ↛ adapters` (FR-002, Key Entities). Convención de puertos `typing.Protocol` (no `ABC`) hecha explícita. Pendiente para `/clarify`: contrato del seam constructor-de-entrada↔`AgentClient.send` (A3) y tipo de retorno del puerto `Evaluator` (marcado `[NEEDS CLARIFICATION]` en FR-011).
- **2026-06-09** — `/clarify` (segunda ronda, A3 + puerto). (1) Seam constructor-de-entrada↔`send`: value object `AgentInput` (variantes estructurada/texto); el adapter lo renderiza, serialización confinada al adapter (FR-014, Key Entity `AgentInput`). Modifica la firma de `AgentClient.send` → reconciliar [[SPEC-002-agent-client]]. (2) Retorno del puerto `Evaluator`: supertipo común `EvaluatedResult` (`case_id` + veredicto tri-estado + `to_dict()`), concreto para que mypy proteja (FR-011, FR-015, Key Entity `EvaluatedResult`). Resuelto el último `[NEEDS CLARIFICATION]`. Tocadas: Clarifications, FR-011, FR-014 (nuevo), FR-015 (nuevo), Key Entities, Coverage. **No quedan marcadores `[NEEDS CLARIFICATION]` en la spec.**
- **2026-06-09** — `/analyze` (verificación) + correcciones de coherencia. Confirmados los 6 hallazgos resueltos, 0 `[NEEDS CLARIFICATION]`, 0 conflictos constitucionales, coverage 100%. Alineadas frases desactualizadas tras las ediciones: Key Entity `Evaluator` (retorno = `EvaluatedResult`, ya no "pendiente"); Edge Case de persistencia (apunta a `profile_id`/FR-013); FR-014 suma la reconciliación de [[SPEC-002b-message-builder]] (cambio de retorno de `message_builder.build`); Acceptance Scenario 5 matizado (refactor único de `send`/`SuiteResult`, comportamiento del circuito preservado); FR-007 fija `--perfil` canónico con vocabulario de `AGENT_PROFILE`; "terna"→"tupla" (FR-001, Key Entity).
