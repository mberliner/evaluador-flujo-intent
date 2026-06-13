# SPEC-012-translation-evaluator — Evaluador de traducción de intents

**Estado:** draft
**Iter:** 12
**Formato:** Híbrido
**Depende de:** [[SPEC-011-agent-under-test]]
**Relacionada con:** [[SPEC-002b-message-builder]], [[SPEC-003-classification-evaluator]], [[SPEC-001-single-case-input]]

## Clarifications

> **Nota de mapeo (reorganización 2026-06-13 — ver Historial):** la spec pasó de una sola User Story P1 con FR-001..FR-015 a **tres User Stories** con FR renombrados `FR-USn-xxx`. Los `FR-NNN` citados en las Clarifications de abajo se conservan **tal cual se decidieron** y corresponden a: FR-001+FR-014→**FR-US1-001** · FR-003→**FR-US1-002** · FR-004→**FR-US1-003** · FR-005/FR-006→**FR-US1-004** · FR-007→**FR-US1-005** · FR-012→**FR-US1-006** · FR-008→**FR-US1-007** · FR-002→**FR-US2-001** · FR-013→**FR-US2-002** · FR-010→**FR-US2-003** · FR-009→**FR-US3-001** · FR-015→**FR-US3-002** · FR-011 (naming)→último FR de cada US.

### Session 2026-06-09

- Q: FR-007 decide pass/fail con un predicado "vacío / no-vacío" por campo de texto, pero el predicado no estaba definido. El esquema tiene tres campos con valor default-sentinela (`restricciones`="sin restricciones", `supuesto_riesgo`="sin supuesto riesgo", `otros.message`="N/A") que el traductor puede emitir cuando el dato no se menciona. ¿Cómo se define "vacío"? → A: Un campo **presente** está **vacío** si tras `strip()` es la cadena vacía, **o** si coincide exactamente con el valor `default` que el esquema declara para ese campo (sentinela). Emitir el default del esquema no cuenta como poblar (coherente con "prohibido inventar"). Determinista: los defaults viven en el esquema (referencia fija). Consecuencia: nuevo **FR-012**; FR-007 apunta a él. (La clave ausente la captura FR-004 como indeterminado — ver Q siguiente.)
- Q: Frontera **válido↔indeterminado** (FR-004 vs. Edge Case): ¿qué hace "válido" a un form extraído? → A: El form es válido (evaluable) solo si valida contra el **shape completo del esquema**: es un objeto JSON parseable con **todas** las claves declaradas (taxonomías completas y todos los campos de texto). Si falta cualquier clave → **indeterminado** (no fail). Supuesto que lo sostiene: el traductor siempre emite el shape completo (con valores vacíos/default), por lo que un form con claves faltantes es un fallo de producción, no una clasificación incorrecta. Consecuencia: FR-004 ampliado (gate de shape completo); Edge Case 2 reescrito (claves faltantes → indeterminado, ya no fail); FR-012 acotado a campos presentes; SC-003 ampliado; nueva Assumption.
- Q: Fuente del **form esperado de ground truth** (FR-001), dado que el Principio IV prohíbe versionar datasets. → A: El caso (entrada + esperado) se **carga en runtime por la interfaz**, reutilizando el mecanismo de archivo de SPEC-004 (unitario)/SPEC-006 (batch) extendido al contrato de traducción; el esperado viaja dentro del archivo del caso y no se versiona. Consecuencia: nuevo **FR-013**; fila de Coverage agregada.
- Q: Estructura de la **entrada en lenguaje natural** del caso (FR-001/FR-002). → A: Son **cinco campos de texto nombrados**; el constructor de `build/` los compone en un `AgentInput` variante texto. Los **nombres exactos quedan pendientes** y se fijan al implementar (`[NEEDS CLARIFICATION]` en FR-001). De paso se reconcilió FR-002 con [[SPEC-011-agent-under-test]] FR-014: el constructor devuelve `AgentInput` (variante texto), la serialización vive en el adapter (`build/` puro, Principio II).

### Session 2026-06-12

- Q: ¿Cuáles son los 5 campos de texto de entrada del caso de traducción (pendiente de FR-001)? → A: El usuario aportó la definición del **cuestionario «Intents IA»** (formulario de captura de iniciativas): 5 preguntas abiertas cuyas respuestas en lenguaje natural son la entrada del traductor. Se fijan los nombres agnósticos de los campos (uno por pregunta): `presentacion_iniciativa`, `problema_y_objetivo`, `impacto_y_exito`, `solucion_imaginada`, `plazos_y_limites`. El texto de referencia del cuestionario queda en la sección «Referencia: cuestionario de origen». Consecuencia: resuelto el último `[NEEDS CLARIFICATION]` de FR-001.
- Q: ¿Cómo se representa el **esperado** (ground truth) dentro del archivo del caso de traducción? → A: Como un **form esperado completo** (`form_esperado`), un único objeto con el mismo shape del esquema. Las taxonomías se comparan exactas contra él; el predicado esperado-poblado/esperado-vacío de cada campo de texto se **deriva** aplicando el mismo predicado vacío de FR-012 al form esperado (vacío/default en el esperado = esperado-vacío); el `nombre_iniciativa` del esperado es a la vez la referencia para la similaridad fuzzy. Un solo bloque, sin redundancia entre marca y valor. Consecuencia: nuevo **FR-014**; FR-001 y FR-013 referencian la representación.
- Q: ¿Cómo compone el constructor de `build/` los 5 campos en el texto natural que recibe el traductor (FR-002)? → A: **Con los títulos de pregunta del cuestionario**: cada respuesta precedida por el título de su pregunta (sección «Referencia: cuestionario de origen»), en el orden del cuestionario, separadas por línea en blanco. Reproduce lo que el traductor ve en el flujo real y le da contexto de cada bloque. Consecuencia: FR-002 ampliado con la regla de composición; SC-005 verificable sobre ella.
- Q: ¿Qué algoritmo determinista usa la similaridad fuzzy de `nombre_iniciativa` (FR-009)? → A: **`rapidfuzz`** (`token_sort_ratio` normalizado a [0,1]), previa normalización de texto (casefold + strip + colapso de espacios). Robusto a reordenamientos de palabras; sigue siendo algorítmico y determinista (Principio III intacto). Consecuencia: FR-009 fija el algoritmo; la dependencia nueva se justifica en `docs/DEVELOPMENT.md` al implementar.
- Q: FR-009/SC-004 mencionaban comparar por fuzzy «nombre_iniciativa (y el nombre del intent)», pero el esquema no tiene un campo «nombre del intent». → A: No es un campo aparte: el **nombre de la iniciativa sale de la 1.ª pregunta del cuestionario** (`presentacion_iniciativa`, «¿Cómo la llamarías en una frase?»), que el traductor vuelca en `nombre_iniciativa`. La similaridad fuzzy se calcula **solo sobre `nombre_iniciativa`**; la mención «el nombre del intent» se elimina de FR-009 y el Acceptance Scenario 5. Se documenta la procedencia (1.ª pregunta → `nombre_iniciativa`) en FR-009.
- Q: ¿El caso de traducción admite campos de entrada vacíos (pregunta sin responder)? → A: **No: los 5 campos de entrada son obligatorios y no-vacíos.** El loader rechaza en carga (error de validación del archivo, no veredicto) un caso con cualquier campo de entrada vacío tras `strip()`. Los casos de información parcial se modelan con respuestas que omiten datos dentro del texto, no con preguntas en blanco. Consecuencia: FR-001 fija la validación; Edge Case agregado.
- Q: ¿El perfil traductor admite ingresar un caso por pantalla en modo simple (análogo a SPEC-001) o solo carga por archivo? → A: **Pantalla y archivo**: además de la carga por archivo (FR-013), el dashboard con el perfil traductor activo ofrece entrada por pantalla con los 5 campos de texto del cuestionario y la captura del esperado (taxonomías + campos de texto del form esperado), con las mismas validaciones de FR-001/FR-014. Paridad con el flujo del clasificador (SPEC-001). Consecuencia: nuevo **FR-015**; fila de Coverage agregada.
- Q: El Principio III de la Constitución estaba redactado en términos del clasificador («clasificación esperada» + enforcement = solo el test del clasificador); ¿cómo se reconcilia con un segundo evaluador sin tener que reenmendar la constitución por cada evaluador futuro? → A: Se **enmendó el Principio III con redacción agnóstica** (PATCH 0.5.1→0.5.2): el invariante habla del «esperado del caso» y de «ningún evaluador del sistema», y la enumeración concreta de evaluadores vive en el SSOT (`docs/ARCHITECTURE.md`, ADR-003, ahora tabla enumerativa). SPEC-012 **no introduce conflicto constitucional** (veredicto determinista; fuzzy informativa). Agregar un evaluador es agregar una fila al SSOT, no tocar la constitución. Ver `historial/sdd.md` 2026-06-13.

## User Story 1 — Evaluador determinista de traducción (Priority: P1)

Como operador de la suite quiero un **evaluador del agente traductor** que, dado un caso (5 textos + `form_esperado`) y una respuesta del agente, emita un veredicto **determinista** (pass/fail/indeterminado) más un detalle por campo, verificando taxonomías cerradas, exclusividad de `tipo_intent` y completitud poblado/vacío, **para medir con un criterio reproducible y algorítmico si el traductor completa la ficha correcta**.

**Why this priority:** es el valor de producto del nuevo perfil habilitado por [[SPEC-011-agent-under-test]] y el **inverso** del clasificador (consume texto natural y **produce** el `{form}` de `schemas/FI_Orquestador_Input.schema.json`). Es pura `domain/`: tiene valor demostrable por sí sola, sin red, UI ni el resto de las User Stories.

**Independent Test:** función pura sobre fixtures de `{form}` conocidos → veredicto tri-estado + detalle por campo, verificable sin red ni invocación al agente.

### Acceptance Scenarios

1. **Given** un `{form}` válido y un caso esperado, **When** el evaluador compara las **taxonomías cerradas** (`tipo_intent`: exactamente un `true`; `datos_requeridos` con sus booleanos y `otros.estado`), **Then** el veredicto es **pass** solo si todas coinciden exactamente con el esperado.
2. **Given** un `{form}` donde `tipo_intent` tiene cero o dos+ valores en `true`, **When** el evaluador valida la taxonomía mutuamente excluyente, **Then** el resultado es **fail**.
3. **Given** un caso cuyo texto de entrada implica un campo de texto poblado (p. ej. `metricas_de_exito`), **When** el `{form}` trae ese campo **vacío**, **Then** la **completitud** falla para ese campo (esperado-poblado que vino vacío).
4. **Given** un caso cuyo texto NO menciona cierto dato, **When** el `{form}` trae el campo correspondiente vacío (el traductor tiene prohibido inventar), **Then** la completitud de ese campo **pasa** (esperado-vacío y vino vacío).
5. **Given** una respuesta de la que **no** se puede extraer un `{form}` JSON válido, o con shape incompleto (falta alguna clave), **When** el evaluador la procesa, **Then** el veredicto es **indeterminado** (no fail), con nota — análogo a "sin clasificación" de [[SPEC-003-classification-evaluator]].

### Edge Cases

- MUST: La respuesta del traductor puede traer, además del `{form}`, una confirmación de la tool que registra la ficha; el evaluador extrae el objeto `{form}` y **ignora** el texto accesorio.
- MUST: Un `{form}` al que le falta **cualquier** clave declarada por el esquema (de taxonomía o de texto) **no** se evalúa como fail: produce veredicto **indeterminado** (FR-US1-003). El evaluador no rompe: detecta la clave faltante y reporta indeterminado con nota.

### Functional Requirements

- **FR-US1-001** (MUST): Define el **caso de traducción** (`domain/`): un **`id` obligatorio** (string no vacío, mismas convenciones de identidad que el `TestCase` de SPEC-004/006, alimenta el `case_id` del resultado y la persistencia) + la **entrada** (los **cinco** campos de texto en lenguaje natural, **nombrados**, obligatorios y no-vacíos tras `strip()`: `presentacion_iniciativa`, `problema_y_objetivo`, `impacto_y_exito`, `solucion_imaginada`, `plazos_y_limites`, ver «Referencia: cuestionario de origen») + el **esperado**, representado como un **`form_esperado` completo**: un único objeto con el mismo shape del esquema (`schemas/FI_Orquestador_Input.schema.json`). Del `form_esperado` se derivan, sin bloques redundantes: (1) las **taxonomías esperadas** (`tipo_intent`/`datos_requeridos`, usadas por FR-US1-004); (2) el predicado **esperado-poblado/esperado-vacío** de cada campo de texto (FR-US1-005), aplicándole el predicado vacío de FR-US1-006; (3) el `nombre_iniciativa` esperado como **referencia de la similaridad fuzzy** (FR-US3-001). Un caso con cualquier entrada vacía o un `form_esperado` de shape incompleto es **inválido en carga** (error de validación del archivo, no veredicto). La información parcial se modela dentro del texto, no con preguntas en blanco. Modelo inmutable; `__test__ = False`.
- **FR-US1-002** (MUST): El **`TranslationEvaluator`** es una pieza **pura en `domain/`** (sin I/O, red ni framework) que recibe el caso y la respuesta del agente y emite un veredicto tri-estado (pass/fail/indeterminado) más un detalle por campo. Implementa el puerto `Evaluator` de [[SPEC-011-agent-under-test]] y su resultado **cumple el supertipo `EvaluatedResult`** (SPEC-011 FR-015): expone `case_id`, el veredicto tri-estado y `to_dict()`, de modo que entra al circuito común de persistencia/render sin ramificar por perfil. Reutiliza el vocabulario de veredicto de [[SPEC-003-classification-evaluator]].
- **FR-US1-003** (MUST): El evaluador **extrae el objeto `{form}`** de la respuesta cruda. El form es **válido (evaluable)** solo si es un objeto JSON parseable que contiene **todas las claves** del esquema (`tipo_intent` con sus 4 booleanos; `datos_requeridos` con sus 5 booleanos, `otros.estado` y `otros.message`; todos los campos de texto). Si no se extrae, no parsea como objeto o le **falta cualquier clave** → **indeterminado** (no fail), con nota. Con **más de un objeto JSON candidato** (form + confirmación de la tool de registro) evalúa el **primer** objeto parseable que cumple el shape completo, en orden de aparición; si ninguno lo cumple, indeterminado. Acá se exige la **presencia** de la clave; que su **valor** esté vacío o poblado lo juzga FR-US1-006.
- **FR-US1-004** (MUST): Valida `tipo_intent` como **mutuamente excluyente** (exactamente un `true`; cero o más de uno = fail) y compara por **match exacto** contra el esperado las taxonomías cerradas: los cuatro booleanos de `tipo_intent`, los cinco de `datos_requeridos` y `datos_requeridos.otros.estado`.
- **FR-US1-005** (MUST): Verifica **completitud condicionada al esperado**: cada campo de texto esperado-poblado debe venir no-vacío; cada esperado-vacío debe venir vacío. Verificación exacta sobre el predicado "vacío / no-vacío" (FR-US1-006), no sobre el contenido.
- **FR-US1-006** (MUST): El predicado **vacío** de un campo de texto se aplica a campos **presentes** (la clave ausente la captura FR-US1-003 como indeterminado): el campo está **vacío** si su valor, tras `strip()`, es la cadena vacía; **o** si coincide exactamente con el `default`-sentinela que el esquema declara para ese campo (`restricciones`→"sin restricciones", `supuesto_riesgo`→"sin supuesto riesgo", `datos_requeridos.otros.message`→"N/A"). En cualquier otro caso está **poblado**. Emitir el default del esquema **no** cuenta como poblar. La lista de sentinelas se deriva del esquema (referencia fija), no se hardcodea aparte.
- **FR-US1-007** (Garantía constitucional): El veredicto **pass/fail** se decide **únicamente** con FR-US1-004 y FR-US1-005 (todo determinista y exacto). Ninguna comparación fuzzy de contenido de texto interviene en el veredicto (Opción A — preserva el Principio III de la Constitución).
- **FR-US1-008** (MUST): Ningún identificador nombra proveedor, framework de UI, formato de serialización ni protocolo de auth (SPEC-000-naming).

### Key Entities

- **Caso de traducción** (nuevo, `domain/`): `id` + 5 textos del cuestionario + `form_esperado` completo (del que se derivan taxonomías esperadas, predicados poblado/vacío y referencia fuzzy — no se almacenan como bloques separados). Modelo inmutable, validado; `__test__ = False`.
- **TranslationEvaluator** (nuevo, `domain/`): `evaluate(case, agent_response) → resultado`, pura, sin estado ni I/O. Implementa el puerto `Evaluator`.
- **Resultado de traducción** (nuevo, `domain/`): `case_id` + veredicto tri-estado + detalle por campo. **Cumple `EvaluatedResult`** (SPEC-011 FR-015) y es serializable (`to_dict`).
- **Esquema `{form}`** (existente, `schemas/FI_Orquestador_Input.schema.json`): **salida** del traductor (y entrada del clasificador); referencia compartida del shape.

### Success Criteria

- [ ] **SC-US1-001**: Sobre un fixture de respuesta con `{form}` de taxonomías conocidas, el evaluador emite el veredicto correcto (pass cuando todas coinciden; fail cuando una no, o cuando `tipo_intent` no tiene exactamente un `true`).
- [ ] **SC-US1-002**: La completitud condicionada da pass cuando los esperados-poblados vienen no-vacíos y los esperados-vacíos vienen vacíos; da fail en el caso contrario, sobre fixtures conocidos.
- [ ] **SC-US1-003**: Una respuesta sin `{form}` extraíble, o con un form al que le falta cualquier clave del esquema, produce veredicto **indeterminado** (no fail), con nota.

### Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-US1-001 | modelo de caso en `domain/` + tests de validación (5 entradas no-vacías, `form_esperado` de shape completo) y de derivación (taxonomías, predicados poblado/vacío vía FR-US1-006, referencia fuzzy) |
| FR-US1-002, FR-US1-004 | `TranslationEvaluator` en `domain/` + tests de taxonomías (exclusividad, match exacto) |
| FR-US1-003 | test de extracción de `{form}` (válido completo, ausente, **shape incompleto**, con texto accesorio, múltiples objetos) → SC-US1-003 |
| FR-US1-005 | tests de completitud condicionada (poblado/vacío por campo) → SC-US1-002 |
| FR-US1-006 | tests del predicado vacío: `""`/whitespace, default-sentinela (vacío) y string no-default (poblado) |
| FR-US1-007 | derivado de SC-US3-001 (variar el nombre no voltea el veredicto) |
| FR-US1-008 | `tools/check_naming.py` sobre `src/` |

## User Story 2 — Caso en circuito: carga, envío y reporte (Priority: P2)

Como operador de la suite quiero **cargar un caso de traducción por archivo, enviarlo al agente y ver el veredicto persistido** por el mismo circuito que el clasificador, **para probar al traductor sobre casos reales dentro de la app y conservar el resultado de cada corrida disponible para revisarlo después**.

**Why this priority:** convierte el evaluador (US1) en algo operable end-to-end. Depende de US1 (necesita el evaluador y el modelo de caso) y del perfil de [[SPEC-011-agent-under-test]]. US1 ya tiene valor por fixtures; esta US lo lleva al circuito real de la app.

**Independent Test:** construir el payload de texto a partir de los textos del caso sin invocar al agente (SC-US2-001), más una corrida real en el dashboard (SC-US2-002).

### Acceptance Scenarios

1. **Given** una respuesta del agente con `{form}` + confirmación de la tool de registro, **When** se procesa el caso, **Then** el constructor/evaluador toma el `{form}` e **ignora** el texto accesorio, siguiendo el circuito común.
2. **Given** un caso cargado por archivo con la entrada (5 textos) y el `form_esperado`, **When** se construye el caso, **Then** produce el **mismo modelo de caso** y entra al circuito común de envío/evaluación/persistencia.

### Functional Requirements

- **FR-US2-001** (MUST): Un **constructor de entrada** en `build/` produce un **`AgentInput` (variante texto)** a partir de los cinco campos de texto del caso. La **composición** es determinista: cada respuesta precedida por el **título de su pregunta** del cuestionario (ver «Referencia: cuestionario de origen»), en el orden del cuestionario, con los bloques separados por línea en blanco. La serialización al payload del proveedor vive en el adapter ([[SPEC-011-agent-under-test]] FR-014); `build/` permanece puro (Principio II).
- **FR-US2-002** (MUST): El **caso de traducción** (entrada + esperado) se carga **en runtime por la interfaz**, reutilizando el mismo mecanismo de archivo que SPEC-004 (caso unitario) y SPEC-006 (batch), extendido al contrato de traducción. El **esperado** viaja **dentro del archivo** con la representación de FR-US1-001 y **no se versiona** (Principio IV). Una entrada vacía o un `form_esperado` de shape incompleto → rechazo en carga con error legible. Los fixtures de los tests del evaluador (`{form}` concretos) son código de test, no datasets operativos.
- **FR-US2-003** (MUST): El veredicto y el detalle por campo se exponen en el dashboard y se persisten en la corrida por el mismo circuito que el clasificador (reutiliza SPEC-005/006 vía el perfil de [[SPEC-011-agent-under-test]]). En modo batch, el resumen estadístico de la corrida del traductor son los **conteos del veredicto tri-estado** (pass/fail/indeterminado) calculados sobre la superficie común `EvaluatedResult`; la matriz de confusión y métricas por clase de [[SPEC-008-suite-metrics]] siguen siendo exclusivas del clasificador (ver Fuera de alcance).
- **FR-US2-004** (MUST): Ningún identificador nombra proveedor, framework de UI, formato de serialización ni protocolo de auth (SPEC-000-naming).

### Key Entities

- **Constructor de entrada de texto natural** (nuevo, `build/`): produce un `AgentInput` (variante texto) a partir de los 5 textos, componiéndolos con los títulos de pregunta (FR-US2-001). `build/` permanece puro; la serialización vive en el adapter ([[SPEC-011-agent-under-test]] FR-014).
- **Loader de caso de traducción** (extensión del mecanismo de SPEC-004/006): carga entrada + `form_esperado` en runtime, sin versionar datos.

### Success Criteria

- [ ] **SC-US2-001**: El constructor produce, a partir de los textos del caso, un payload de texto natural válido para enviar al traductor (verificable sin invocar al agente).
- [ ] **SC-US2-002** *(verificación funcional en la app real)*: Seleccionado el perfil traductor ([[SPEC-011-agent-under-test]]), un caso real se envía al agente, se extrae el `{form}` de la respuesta y se muestra el veredicto + detalle por campo en el dashboard.

### Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-US2-001 | constructor de entrada en `build/` + test de payload de texto natural → SC-US2-001 |
| FR-US2-002 | extensión del loader de caso (SPEC-004/006) + test de carga en runtime de entrada+esperado, sin datos versionados (Principio IV) |
| FR-US2-003 | integración con persistencia/render vía perfil de [[SPEC-011-agent-under-test]] → SC-US2-002 |
| FR-US2-004 | `tools/check_naming.py` sobre `src/` |

## User Story 3 — Similaridad informativa y entrada por pantalla (Priority: P3)

Como operador de la suite quiero (a) una **similaridad fuzzy informativa** del `nombre_iniciativa` y (b) cargar un caso **por pantalla** en modo simple con paridad al flujo del clasificador, **para contar con una señal cualitativa extra al diagnosticar un fallo y para cargar un caso suelto de forma directa desde la pantalla**.

**Why this priority:** dos mejoras **complementarias**. La fuzzy es SHOULD y, por diseño (FR-US1-007), reporta una métrica sin alterar el veredicto; la entrada por pantalla da paridad con el flujo del clasificador (SPEC-001) sobre la carga por archivo (US2). Llegan después del núcleo y el circuito.

**Independent Test:** demostrar que variar solo el texto del nombre no cambia el veredicto (SC-US3-001), y que el envío por pantalla produce el mismo modelo de caso que la carga por archivo con las mismas validaciones (SC-US3-002).

### Acceptance Scenarios

1. **Given** un `{form}` válido, **When** el evaluador compara `nombre_iniciativa` contra el esperado por **similaridad fuzzy normalizada**, **Then** reporta la similaridad como **métrica informativa** que **no** altera el veredicto pass/fail (Opción A: Constitución intacta).
2. **Given** el perfil traductor activo y la entrada por pantalla con los 5 campos del cuestionario y el esperado completos y válidos, **When** el operador envía el caso, **Then** se construye el **mismo modelo de caso** que produciría la carga por archivo y sigue el mismo circuito de envío/evaluación (FR-US3-002).
3. **Given** la entrada por pantalla con algún campo de texto vacío o un `form_esperado` de shape incompleto, **When** el operador intenta enviar, **Then** el envío se **rechaza con error legible antes de invocar al agente** (mismas validaciones de FR-US1-001 que la carga por archivo).

### Functional Requirements

- **FR-US3-001** (SHOULD): El evaluador calcula una **similaridad fuzzy normalizada** (determinista, sin LLM) entre el `nombre_iniciativa` producido y el del `form_esperado`, y la incluye en el detalle como **métrica informativa** (no altera el veredicto). Procedencia: el nombre surge de la 1.ª pregunta del cuestionario (`presentacion_iniciativa`, «¿Cómo la llamarías en una frase?»), que el traductor vuelca en `nombre_iniciativa`. Si el `nombre_iniciativa` esperado está vacío (predicado de FR-US1-006), la similaridad **se omite** y el detalle la reporta como no aplicable. Algoritmo: **`rapidfuzz`**, `token_sort_ratio` normalizado a [0,1], tras normalizar ambos textos (casefold + strip + colapso de espacios). La dependencia `rapidfuzz` se justifica en `docs/DEVELOPMENT.md` al implementar (única pieza no-stdlib del evaluador; elegida por robustez a reordenamientos de palabras).
- **FR-US3-002** (MUST): Con el perfil traductor activo, el dashboard ofrece **entrada por pantalla** en modo simple (análoga a [[SPEC-001-single-case-input]]): el `id` del caso, los **5 campos de texto** del cuestionario (áreas de texto, en el orden y con los títulos de la sección «Referencia: cuestionario de origen») y la captura del **esperado** (taxonomías cerradas + campos de texto del `form_esperado`). Aplican las **mismas validaciones** que la carga por archivo (FR-US1-001: 5 campos no-vacíos, `form_esperado` de shape completo); un envío inválido se rechaza con error legible antes de invocar al agente. La entrada por pantalla y la carga por archivo (FR-US2-002) producen el **mismo modelo de caso** y siguen el mismo circuito.
- **FR-US3-003** (MUST): Ningún identificador nombra proveedor, framework de UI, formato de serialización ni protocolo de auth (SPEC-000-naming).

### Key Entities

- **Cálculo de similaridad fuzzy** (nuevo, `domain/`, sobre el detalle del resultado): determinista, sin LLM; informativo, no graduante del veredicto.
- **Formulario de caso de traducción** (nuevo, `src/dashboard/`): 5 áreas de texto + captura del esperado, con las validaciones de FR-US1-001.

### Success Criteria

- [ ] **SC-US3-001**: La similaridad fuzzy de `nombre_iniciativa` se reporta en el detalle y **no** cambia el veredicto entre dos corridas con el mismo resultado de taxonomías/completitud (variar solo el texto del nombre no voltea pass↔fail).
- [ ] **SC-US3-002**: El envío por pantalla inválido se rechaza con error legible antes de invocar al agente; el válido produce el **mismo modelo de caso** que la carga por archivo y sigue el mismo circuito.

### Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-US3-001 | test que demuestra que variar solo el texto del nombre no cambia el veredicto y que `nombre_iniciativa` esperado vacío → similaridad no aplicable → SC-US3-001 |
| FR-US3-002 | formulario de caso de traducción en `src/dashboard/` (5 áreas de texto + captura del esperado) + test de validación de envío inválido → SC-US3-002 |
| FR-US3-003 | `tools/check_naming.py` sobre `src/` |

## Assumptions (generales)

- El traductor devuelve el `{form}` como JSON en el contenido del mensaje `assistant` (su instrucción dice "devolvé únicamente el JSON válido"), eventualmente acompañado de la confirmación de la tool de registro; el evaluador tolera el texto accesorio (incluidos los títulos de pregunta que el constructor antepone, FR-US2-001).
- El traductor emite **todas las claves** del esquema en el `{form}` (con valor vacío o default cuando el dato no se menciona). Por eso un form con claves faltantes se interpreta como **fallo de producción del shape → indeterminado** (FR-US1-003), no como clasificación incorrecta (fail). Si esta suposición no se sostuviera, se reabre la frontera válido↔indeterminado en una revisión de la spec.
- La paleta de taxonomías cerradas del `{form}` (estructura de `tipo_intent` y `datos_requeridos`) es estable y coincide con `schemas/FI_Orquestador_Input.schema.json`.
- "Sin LLM-as-judge" es un invariante constitucional (Principio III); la comparación fuzzy elegida es algorítmica, determinista e informativa (no graduante) bajo Opción A.

## Referencia: cuestionario de origen

Definición del formulario **«Intents IA»** (captura de iniciativas) aportada por el usuario el 2026-06-12. Las respuestas en lenguaje natural a estas 5 preguntas son la entrada del traductor; cada pregunta mapea a un campo del caso de traducción (FR-US1-001). Esta sección es el SSOT del texto del cuestionario dentro del proyecto.

> Consigna del formulario: *"Contanos en lenguaje natural qué querés resolver, en 5 preguntas abiertas. No necesitás definir la solución ni completar campos técnicos: nuestro agente desglosa, estructura y clasifica tu respuesta automáticamente. Cuanto más contexto des, mejor."*

| # | Campo | Título de la pregunta | Texto de la pregunta |
|---|---|---|---|
| 1 | `presentacion_iniciativa` | Presentación e impulso de la iniciativa | ¿Cómo la llamarías en una frase? ¿Desde qué dirección y gerencia la proponés y quién tu gerente y el sponsor del proyecto? ¿Ya la conversaste con algún equipo técnico o es la primera vez que la presentás? Y para ubicarla: ¿forma parte del Plan de Arquitectura TO BE del próximo Q? ¿De qué programa? |
| 2 | `problema_y_objetivo` | El problema y lo que querés lograr | ¿Qué dolor u oportunidad querés atacar y qué te gustaría conseguir? Ayudanos a entender a quién afecta hoy, cómo se resuelve actualmente (si es que se resuelve) y por qué es importante encararlo ahora. |
| 3 | `impacto_y_exito` | Dónde impacta y cómo se vería el éxito | Si esto funcionara, ¿en qué proceso o flujo de trabajo se notaría el cambio y quiénes lo aprovecharían? ¿Cómo sabrías que está dando resultado — qué tiempos, volúmenes, costos o indicadores mirarías? |
| 4 | `solucion_imaginada` | Cómo te imaginás la solución | Por ejemplo, ¿un asistente que responde y conversa, algo que clasifica o deriva casos, que resume documentos, que busca información, que entiende imágenes o voz, que coordina varias tareas? ¿Qué información o datos consumiría y con qué aplicativos o sistemas tendría que conectarse? |
| 5 | `plazos_y_limites` | Plazos, tamaño y límites | ¿Para cuándo te gustaría tenerlo y qué tan grande lo ves para un primer paso? ¿Hay restricciones, supuestos o riesgos a tener en cuenta — datos sensibles, temas regulatorios, presupuesto, dependencias con otras áreas, etc.? |

Notas:

- El cuestionario es la **definición del contrato de entrada** (referencia fija, análoga a `schemas/FI_Orquestador_Input.schema.json` para la salida); **no** es un dataset operativo, por lo que no viola el Principio IV. Las respuestas concretas de cada caso siguen cargándose en runtime y no se versionan (FR-US2-002).
- Los nombres de campo son agnósticos a la tecnología del formulario (SPEC-000-naming): describen el contenido de la pregunta, no la herramienta de captura.

## Fuera de alcance

- Selección del perfil de agente y registro de perfiles → [[SPEC-011-agent-under-test]].
- Métricas de suite (matriz de confusión) para el traductor: la matriz de [[SPEC-008-suite-metrics]] está definida sobre la paleta de clasificación; su extensión al contrato de traducción es trabajo futuro, no de esta spec.
- Graduar el veredicto con la similaridad fuzzy del texto redactado (Opción B): requeriría enmendar la Constitución (Principio III). Queda fuera salvo decisión de gobernanza posterior.
- Verificar la llamada interna del traductor a la tool de registro de la ficha (efecto colateral en la planilla externa): la suite evalúa la traducción, no el registro.

## Historial

- **2026-06-13** — **Reorganización en 3 User Stories** (sin cambio de comportamiento ni decisión nueva del usuario; a pedido del usuario por tamaño de la spec). La única User Story P1 con FR-001..FR-015 se dividió en tres slices verticales independientemente entregables y testeables, siguiendo el molde de [[SPEC-006-batch-suite]]: **US1 — Evaluador determinista (P1)** (núcleo puro `domain/`: modelo de caso, extracción/shape, taxonomías, completitud, predicado vacío, garantía constitucional); **US2 — Caso en circuito (P2)** (constructor `build/`, carga por archivo, persistencia/render por el circuito del clasificador); **US3 — Similaridad informativa y entrada por pantalla (P3)** (fuzzy informativa + entrada por pantalla). FR renombrados a `FR-USn-xxx` (ver nota de mapeo al inicio de Clarifications); 15 FR → 13 (FR-001+FR-014 fusionados en FR-US1-001; FR-008 reexpresado como garantía FR-US1-007; FR-011 replicado como naming por US). Acceptance/SC/Coverage repartidos por US. Clarifications, «Referencia: cuestionario de origen», Assumptions generales y Fuera de alcance se conservan a nivel spec. Cada User Story se redactó en formato «Como… quiero… para…», en afirmativo, nombrando el valor esperado.
- **2026-06-13** — `/analyze` (verificación) + corrección de derivas A1–A4. El análisis semántico no encontró conflictos constitucionales ni `[NEEDS CLARIFICATION]`, pero detectó derivas de redacción interna que se corrigieron sin cambio de comportamiento ni decisión del usuario: **A1** Key Entity «Caso de traducción» realineada con FR-014 (esperado = `form_esperado` completo, no tres bloques); **A2** Key Entity del constructor de entrada pasa de «arma el payload» a «produce `AgentInput` variante texto» (la serialización vive en el adapter, Principio II); **A3** FR-003 y Key Entity «Resultado de traducción» explicitan que **cumplen `EvaluatedResult`** (SPEC-011 FR-015: `case_id` + veredicto tri-estado + `to_dict()`); **A4** agregados los Acceptance Scenarios 7 y 8 para la entrada por pantalla (FR-015). Pendientes menores no aplicados (LOW): A5 (Assumption sobre tolerancia del traductor al texto con títulos), A6 (User Story «campos obligatorios» sin correlato), A7 (cómputo de accuracy tri-estado, frontera de SPEC-011).
- **2026-06-13** — `/analyze` + `/clarify` (sesión 2026-06-13). El `/analyze` confirmó 0 conflictos constitucionales en la letra del invariante pero detectó que el Principio III había quedado angosto para un segundo evaluador, más cuatro huecos de subespecificación que se cerraron por redacción (patrón anti-`run_id`, sin requerir decisión): (a) **identidad del caso** — `id` obligatorio análogo a `TestCase`, alimenta `case_id`/persistencia (FR-001); (b) **múltiples objetos JSON** en la respuesta (form + confirmación de tool) — se evalúa el primer objeto que cumple el shape completo (FR-004); (c) **fuzzy con `nombre_iniciativa` esperado vacío** — se omite, se reporta no aplicable (FR-009); (d) **resumen batch del traductor** — conteos del veredicto tri-estado sobre `EvaluatedResult`; la matriz de confusión sigue siendo del clasificador (FR-010). Dos preguntas que sí requerían decisión del usuario: **A3** entrada por pantalla además de archivo → nuevo **FR-015**; **A4** reconciliación del Principio III → **enmienda constitucional agnóstica** (PATCH 0.5.1→0.5.2; ADR-003 promovido a SSOT enumerativo de evaluadores; ver `historial/sdd.md`). Tocadas: Clarifications, FR-001, FR-004, FR-009, FR-010, FR-015 (nuevo), Edge Cases, Coverage. **Sin marcadores `[NEEDS CLARIFICATION]`; spec lista para implementar.**
- **2026-06-12** — `/clarify` (sesión 2026-06-12, 5 preguntas). (1) Representación del **esperado**: form esperado completo (`form_esperado`), del que se derivan taxonomías, predicados poblado/vacío (vía FR-012) y referencia fuzzy → nuevo **FR-014**, fila de Coverage. (2) **Composición** del texto al traductor: títulos de pregunta del cuestionario + respuesta, en orden, separados por línea en blanco → FR-002 ampliado. (3) Algoritmo **fuzzy**: `rapidfuzz` `token_sort_ratio` normalizado, con normalización casefold/strip/espacios; dependencia a justificar en `docs/DEVELOPMENT.md` al implementar → FR-009. (4) «El nombre del intent» no es un campo: el nombre surge de la 1.ª pregunta (`presentacion_iniciativa`) y la fuzzy se acota a `nombre_iniciativa` → FR-009, SC-004, Acceptance 5. (5) Los **5 campos de entrada son obligatorios** y no-vacíos; rechazo en carga → FR-001, Edge Case nuevo. Sin marcadores pendientes; spec lista para `/analyze` de verificación e implementación.
- **2026-06-12** — Resuelto el `[NEEDS CLARIFICATION]` de FR-001 (enumeración de los 5 campos de texto de entrada). El usuario aportó la definición del cuestionario **«Intents IA»** (5 preguntas abiertas de captura de iniciativas). Se fijan los campos `presentacion_iniciativa`, `problema_y_objetivo`, `impacto_y_exito`, `solucion_imaginada`, `plazos_y_limites` y se incorpora el texto del cuestionario como sección de referencia (SSOT del contrato de entrada). Tocadas: Clarifications (sesión 2026-06-12), FR-001, nueva sección «Referencia: cuestionario de origen». **No quedan marcadores `[NEEDS CLARIFICATION]` en la spec**; pendiente menor previo a implementar: algoritmo fuzzy concreto (FR-009, decisión de implementación).
- **2026-06-09** — `/clarify` (sesión 2026-06-09). Resuelto el gap de mayor impacto detectado por `/analyze`: el predicado **vacío/no-vacío** del que cuelga el veredicto de completitud (FR-007) no estaba definido y los tres campos con default-sentinela del esquema (`restricciones`, `supuesto_riesgo`, `otros.message`) lo volvían no-determinista. Decisión del usuario (Opción A): vacío = `strip()` vacío **o** valor igual al default del esquema **o** clave ausente; emitir el default no cuenta como poblar. Requisito implícito → explícito: nuevo **FR-012**; FR-007 apunta a él; fila de Coverage agregada.
- **2026-06-09** — `/clarify` (sesión 2026-06-09, 2.ª pregunta). Resuelta la **frontera válido↔indeterminado** (FR-004 vs. Edge Case 2). Decisión del usuario: el form es válido solo si valida contra el **shape completo del esquema** (objeto parseable con todas las claves, taxonomías y textos); falta cualquier clave → **indeterminado** (no fail). Reconciliación: FR-004 ampliado con el gate de shape completo; Edge Case 2 reescrito (claves faltantes → indeterminado, antes "no coincidentes/fail"); FR-012 acotado a **campos presentes** (la clave ausente la captura FR-004); SC-003 ampliado a "shape incompleto"; nueva Assumption (el traductor emite siempre el shape completo) que sostiene la decisión; fila de Coverage FR-004 ampliada. Pendientes para próxima ronda de `/clarify`: enumeración de los campos de texto de entrada del caso (FR-001/FR-002), fuente del ground truth (Principio IV) y algoritmo fuzzy (FR-009).
- **2026-06-09** — `/clarify` (sesión 2026-06-09, 3.ª pregunta). Resuelta la **fuente del ground truth** (FR-001, Principio IV). Decisión del usuario: el caso (entrada + esperado) se **carga en runtime por la interfaz**, reutilizando el mecanismo de archivo de SPEC-004/006 extendido al contrato de traducción; el esperado viaja dentro del archivo y no se versiona. Requisito implícito → explícito: nuevo **FR-013**; fila de Coverage agregada. Pendientes: enumeración de los campos de texto de entrada del caso (FR-001/FR-002) y algoritmo fuzzy (FR-009).
- **2026-06-09** — `/clarify` (sesión 2026-06-09, 4.ª pregunta). Estructura de la **entrada del caso** (FR-001/FR-002): **cinco campos de texto nombrados**, compuestos por el constructor de `build/` en un `AgentInput` variante texto. Los **nombres exactos quedan pendientes** (`[NEEDS CLARIFICATION]` en FR-001) — el usuario aún no los tiene. Reconciliación con [[SPEC-011-agent-under-test]] FR-014: FR-002 pasa de "arma el payload" a "produce un `AgentInput` variante texto", confinando la serialización al adapter (preserva `build/` puro, Principio II). Pendientes para próxima ronda: enumeración de los 5 campos (al implementar) y algoritmo fuzzy (FR-009).
- **2026-06-04** — Spec creada (draft). Motivación: habilitar la prueba del agente `traductor_intents` (id `3da38f33-3788-44c2-b326-fdbf3cd0605c`), cuyo contrato es el inverso del clasificador. Se inspeccionó su `description`/`instructions` en la plataforma: traduce texto natural al `{form}` de `schemas/FI_Orquestador_Input.schema.json`, con `tipo_intent` mutuamente excluyente, `datos_requeridos` inferido y prohibición de inventar campos. Decisión de gobernanza del usuario: **Opción A** — el veredicto se decide solo con lo 100% determinista (taxonomías exactas + completitud poblado/vacío); la similaridad fuzzy de `nombre_iniciativa`/nombre del intent se calcula pero es **informativa**, para no violar el Principio III de la Constitución (que prohíbe variantes equivalentes y LLM-as-judge). `[NEEDS CLARIFICATION]` a resolver al implementar: (1) cuáles son exactamente los campos de texto de entrada del caso de traducción (el usuario indicó "5 campos de texto"); (2) la fuente del form esperado de ground truth (carga por archivo, derivación de un caso existente, u otra); (3) el algoritmo de similaridad fuzzy concreto y su umbral de reporte.
