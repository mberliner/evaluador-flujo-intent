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

- Q: ¿El dashboard ofrece selector de perfil en caliente o solo refleja el `.env`? → A: Solo refleja (indicador read-only); el `.env` es el único mecanismo de selección. Perfil global fijado al arrancar ⇒ sin concurrencia ni resolución de conflictos. (FR-008)
- Q: ¿Nombres de la variable de selección y del `agent_id` del traductor? → A: `AGENT_PROFILE` (`clasificador`|`traductor`, default `clasificador`) y esquema `AGENT_ID_<PERFIL>` (`AGENT_ID_CLASIFICADOR`, `AGENT_ID_TRADUCTOR`); `AGENT_ID` queda como alias retrocompatible del clasificador. (FR-004, FR-005)
- Q: ¿Contrato común entre el constructor de entrada y `AgentClient.send` ({form} estructurado vs. texto natural)? → A: Value object de dominio `AgentInput` (variante estructurada|texto); el adapter lo renderiza al payload del proveedor. Serialización confinada al adapter (ADR-001, `build/` puro); descartado mover `json.dumps` a `build/`. (FR-014)
- Q: ¿Tipo de retorno del puerto `Evaluator` (resultados de forma distinta)? → A: Supertipo común `EvaluatedResult` en `domain/` (`case_id` + veredicto tri-estado + `to_dict()`); concreto, no `Any`, para que mypy capture incompatibilidades. (FR-011, FR-015)

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

- **AgentProfile** (nuevo, `src/application/`): tupla `(profile_id, agent_id, input_builder, response_evaluator)`. Vive en `application/` (no `domain/`) porque referencia `build/`. (FR-001)
- **Registro de perfiles** (nuevo, `src/application/`): colección de `AgentProfile` indexada por `profile_id`; expone `resolve(profile_id) -> AgentProfile` y la lista de `profile_id` válidos. Puro: recibe el `profile_id` ya leído por `PlatformConfig`, no lee `os.environ` ni importa `adapters/`. (FR-002)
- **Evaluator** (puerto nuevo, `domain/ports.py`, `typing.Protocol`): `evaluate(case, agent_response) -> EvaluatedResult`; lo cumplen el evaluador de clasificación (existente) y el de traducción ([[SPEC-012-translation-evaluator]]). (FR-011)
- **AgentInput** (nuevo, `domain/`): value object inmutable con variantes estructurada|texto; salida del constructor de entrada y entrada de `AgentClient.send`, que lo renderiza al payload del proveedor. (FR-014)
- **EvaluatedResult** (nuevo, `domain/`): supertipo común del resultado evaluado (`case_id` + veredicto tri-estado + `to_dict()`); retorno del puerto `Evaluator`. Lo cumplen `TestResult` y el resultado de traducción. (FR-011, FR-015)
- **PlatformConfig** (existente, `adapters/platform_config.py`): se extiende para leer `AGENT_PROFILE` y resolver `AGENT_ID_<PERFIL>`. Único lector de `os.environ`.
- **SuiteResult** (existente, SPEC-005): se extiende con `profile_id` para trazar de forma explícita el perfil de la corrida. (FR-013)

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

- **2026-06-04** — Spec creada (draft). Motivación: existe el agente `traductor_intents` (id `3da38f33-3788-44c2-b326-fdbf3cd0605c`), contrato **inverso** del clasificador (entra texto natural, sale `{form}`); reutilizar el circuito exige seleccionar el agente bajo prueba con su constructor de entrada y su evaluador. Selección por `.env`, default clasificador.
- **2026-06-09** — `/clarify` (2 rondas) + `/analyze`. Resueltos los `[NEEDS CLARIFICATION]`: (1) dashboard read-only del `.env` (FR-008); (2) variables `AGENT_PROFILE` + `AGENT_ID_<PERFIL>` con `AGENT_ID` como alias (FR-004/005); (3) seam constructor↔`send` vía value object `AgentInput`, reconcilia [[SPEC-002-agent-client]]/[[SPEC-002b-message-builder]] (FR-014); (4) retorno del puerto `Evaluator` = supertipo `EvaluatedResult` (FR-011/015). `/analyze` agregó los requisitos estructurales implícitos: puerto `Evaluator` (FR-011), parametrización de constructor+evaluador en `run_suite.py` (FR-012), `profile_id` explícito en `SuiteResult` (FR-013). Registro en `application/` y puro (FR-002); puertos con `typing.Protocol`. 0 conflictos constitucionales, coverage 100%, sin marcadores pendientes.
- **2026-06-14** — Simplificación editorial (sin cambio de comportamiento ni decisión nueva): Clarifications condensadas (Q + decisión + puntero al FR), Key Entities reducidas a punteros de sus FR, Historial comprimido. Eliminada la redundancia entre Clarifications/FR/Key Entities.
