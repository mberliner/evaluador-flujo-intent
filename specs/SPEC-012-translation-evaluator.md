# SPEC-012-translation-evaluator — Evaluador de traducción de intents

**Estado:** draft
**Iter:** 12
**Formato:** Híbrido
**Depende de:** [[SPEC-011-agent-under-test]]
**Relacionada con:** [[SPEC-002b-message-builder]], [[SPEC-003-classification-evaluator]], [[SPEC-001-single-case-input]]

**Resumen:** Define la evaluación del agente **traductor** (inverso del clasificador: consume texto natural y produce el `{form}` de `schemas/FI_Orquestador_Input.schema.json`). Tres cortes: **US1** evaluador determinista puro con veredicto tri-estado (P1); **US2** caso en circuito — carga por archivo, envío y persistencia común (P2); **US3** similaridad fuzzy informativa + entrada por pantalla (P3). En `draft`: especificada y clarificada, pendiente de implementación (requiere el perfil de [[SPEC-011-agent-under-test]]).

## Clarifications

### Session 2026-06-09

- Q: ¿Cómo se define "vacío" para un campo de texto, dados los defaults-sentinela del esquema? → A: Campo presente está vacío si tras `strip()` es la cadena vacía **o** coincide con su `default` del esquema; emitir el default no cuenta como poblar. (FR-US1-006)
- Q: Frontera válido↔indeterminado: ¿qué hace "válido" a un form extraído? → A: Solo si valida el **shape completo** del esquema; falta cualquier clave → indeterminado (no fail). Supuesto: el traductor siempre emite el shape completo. (FR-US1-003)
- Q: Fuente del ground truth, dado que el Principio IV prohíbe versionar datasets. → A: El caso (entrada + esperado) se carga en runtime por la interfaz (mecanismo de SPEC-004/006 extendido); el esperado viaja en el archivo y no se versiona. (FR-US2-002)
- Q: Estructura de la entrada en lenguaje natural. → A: Cinco campos de texto nombrados; el constructor de `build/` los compone en un `AgentInput` variante texto. Nombres fijados en sesión 2026-06-12. (FR-US1-001, FR-US2-001)

### Session 2026-06-12

- Q: ¿Cuáles son los 5 campos de entrada? → A: Los del cuestionario «Intents IA» (ver «Contrato del caso de traducción» y «Referencia: cuestionario de origen»). (FR-US1-001)
- Q: ¿Cómo se representa el esperado en el archivo? → A: Como `form_esperado` completo, del que se derivan taxonomías, predicado poblado/vacío y referencia fuzzy. Sin bloques redundantes. (FR-US1-001)
- Q: ¿Cómo compone el constructor los 5 campos? → A: Cada respuesta precedida por el título de su pregunta, en orden, separadas por línea en blanco. (FR-US2-001)
- Q: ¿Algoritmo de la similaridad fuzzy? → A: `rapidfuzz` `token_sort_ratio` normalizado a [0,1], previa normalización de textos. Determinista (Principio III intacto). (FR-US3-001)
- Q: «El nombre del intent» no es un campo del esquema. → A: El nombre sale de la 1.ª pregunta (`presentacion_iniciativa`) que el traductor vuelca en `nombre_iniciativa`; la fuzzy se acota a `nombre_iniciativa`. (FR-US3-001)
- Q: ¿Se admiten campos de entrada vacíos? → A: No: los 5 son obligatorios y no-vacíos; el loader rechaza en carga. La información parcial se modela dentro del texto. (FR-US1-001)
- Q: ¿Entrada por pantalla además de archivo? → A: Sí, paridad con el clasificador (SPEC-001): el dashboard ofrece los 5 campos + captura del esperado, con las mismas validaciones. (FR-US3-002)
- Q: ¿Cómo se reconcilia el Principio III (redactado para el clasificador) con un 2.º evaluador? → A: Se enmendó el Principio III con redacción agnóstica (PATCH 0.5.1→0.5.2); la enumeración de evaluadores vive en el SSOT (`docs/ARCHITECTURE.md`, ADR-003). Ver `historial/sdd.md` 2026-06-13.

---

## Contrato del caso de traducción

Referencia única del modelo de caso; los FR la citan en lugar de repetir el detalle.

- **Identidad:** `id` obligatorio (string no vacío, mismas convenciones de identidad que el `TestCase` de SPEC-004/006; alimenta el `case_id` del resultado y la persistencia).
- **Entrada:** cinco campos de texto en lenguaje natural, **nombrados**, obligatorios y no-vacíos tras `strip()`: `presentacion_iniciativa`, `problema_y_objetivo`, `impacto_y_exito`, `solucion_imaginada`, `plazos_y_limites` (ver «Referencia: cuestionario de origen»). La información parcial se modela dentro del texto, no con preguntas en blanco.
- **Esperado:** un **`form_esperado` completo** — un único objeto con el shape de `schemas/FI_Orquestador_Input.schema.json`. De él se derivan, sin bloques redundantes: (1) las **taxonomías esperadas** (`tipo_intent`/`datos_requeridos`, usadas por FR-US1-004); (2) el predicado **esperado-poblado/esperado-vacío** por campo de texto (FR-US1-005, aplicando el predicado vacío de FR-US1-006); (3) el `nombre_iniciativa` esperado como referencia de la similaridad fuzzy (FR-US3-001).
- **Validez en carga:** cualquier entrada vacía o un `form_esperado` de shape incompleto hacen al caso **inválido en carga** (error de validación del archivo, no veredicto).
- **Modelo:** inmutable; `__test__ = False`.

---

## User Story 1 — Evaluador determinista de traducción (Priority: P1)

Como operador de la suite quiero un **evaluador del agente traductor** que, dado un caso (5 textos + `form_esperado`) y una respuesta del agente, emita un veredicto **determinista** (pass/fail/indeterminado) más un detalle por campo, verificando taxonomías cerradas, exclusividad de `tipo_intent` y completitud poblado/vacío, **para medir con un criterio reproducible y algorítmico si el traductor completa la ficha correcta**.

**Why this priority:** es el valor de producto del nuevo perfil habilitado por [[SPEC-011-agent-under-test]] y el **inverso** del clasificador. Es pura `domain/`: tiene valor demostrable por sí sola, sin red, UI ni el resto de las User Stories.

**Independent Test:** función pura sobre fixtures de `{form}` conocidos → veredicto tri-estado + detalle por campo, verificable sin red ni invocación al agente.

### Acceptance Scenarios

1. **Given** un `{form}` válido y un caso esperado, **When** el evaluador compara las **taxonomías cerradas** (`tipo_intent`: exactamente un `true`; `datos_requeridos` con sus booleanos y `otros.estado`), **Then** el veredicto es **pass** solo si todas coinciden exactamente con el esperado.
2. **Given** un `{form}` donde `tipo_intent` tiene cero o dos+ valores en `true`, **When** el evaluador valida la taxonomía mutuamente excluyente, **Then** el resultado es **fail**.
3. **Given** un caso cuyo texto de entrada implica un campo de texto poblado (p. ej. `metricas_de_exito`), **When** el `{form}` trae ese campo **vacío**, **Then** la **completitud** falla para ese campo (esperado-poblado que vino vacío).
4. **Given** un caso cuyo texto NO menciona cierto dato, **When** el `{form}` trae el campo correspondiente vacío (el traductor tiene prohibido inventar), **Then** la completitud de ese campo **pasa** (esperado-vacío y vino vacío).
5. **Given** una respuesta de la que **no** se puede extraer un `{form}` JSON válido, o con shape incompleto, **When** el evaluador la procesa, **Then** el veredicto es **indeterminado** (no fail), con nota — análogo a "sin clasificación" de [[SPEC-003-classification-evaluator]].

### Edge Cases

- MUST: La respuesta del traductor puede traer, además del `{form}`, una confirmación de la tool que registra la ficha; el evaluador extrae el objeto `{form}` e **ignora** el texto accesorio.
- MUST: Un `{form}` al que le falta **cualquier** clave declarada por el esquema produce veredicto **indeterminado** (FR-US1-003), no fail; el evaluador no rompe: detecta la clave faltante y reporta indeterminado con nota.

### Functional Requirements

- **FR-US1-001** (MUST): Define el **caso de traducción** (`domain/`) según el «Contrato del caso de traducción»: `id` + 5 entradas de texto + `form_esperado` completo, con sus derivaciones y validación en carga.
- **FR-US1-002** (MUST): El **`TranslationEvaluator`** es una pieza **pura en `domain/`** (sin I/O, red ni framework) que recibe el caso y la respuesta del agente y emite un veredicto tri-estado (pass/fail/indeterminado) más un detalle por campo. Implementa el puerto `Evaluator` de [[SPEC-011-agent-under-test]] y su resultado cumple el supertipo `EvaluatedResult` (SPEC-011 FR-015): expone `case_id`, veredicto y `to_dict()`, entrando al circuito común de persistencia/render sin ramificar por perfil. Reutiliza el vocabulario de veredicto de [[SPEC-003-classification-evaluator]].
- **FR-US1-003** (MUST): El evaluador **extrae el objeto `{form}`** de la respuesta cruda; el form es **evaluable** solo si es un objeto JSON parseable con **todas las claves** del esquema. Si no se extrae, no parsea como objeto o le falta cualquier clave → **indeterminado** (no fail), con nota. Con más de un objeto JSON candidato evalúa el **primer** objeto (en orden de aparición) que cumple el shape completo; si ninguno lo cumple, indeterminado.
  > Claves exigidas: `tipo_intent` con sus 4 booleanos; `datos_requeridos` con sus 5 booleanos, `otros.estado` y `otros.message`; todos los campos de texto. Acá se exige la **presencia** de la clave; que su **valor** esté vacío o poblado lo juzga FR-US1-006.
- **FR-US1-004** (MUST): Valida `tipo_intent` como **mutuamente excluyente** (exactamente un `true`; cero o más de uno = fail) y compara por **match exacto** contra el esperado las taxonomías cerradas: los cuatro booleanos de `tipo_intent`, los cinco de `datos_requeridos` y `datos_requeridos.otros.estado`.
- **FR-US1-005** (MUST): Verifica **completitud condicionada al esperado**: cada campo de texto esperado-poblado debe venir no-vacío; cada esperado-vacío debe venir vacío. Verificación exacta sobre el predicado "vacío / no-vacío" (FR-US1-006), no sobre el contenido.
- **FR-US1-006** (MUST): Un campo de texto **presente** está **vacío** si su valor, tras `strip()`, es la cadena vacía, **o** si coincide exactamente con el `default`-sentinela que el esquema declara para ese campo (`restricciones`→"sin restricciones", `supuesto_riesgo`→"sin supuesto riesgo", `datos_requeridos.otros.message`→"N/A"); en cualquier otro caso está **poblado**.
  > La clave ausente la captura FR-US1-003 como indeterminado. Emitir el default del esquema no cuenta como poblar. La lista de sentinelas se deriva del esquema (referencia fija), no se hardcodea aparte.
- **FR-US1-007** (Garantía constitucional): El veredicto **pass/fail** se decide **únicamente** con FR-US1-004 y FR-US1-005 (todo determinista y exacto). Ninguna comparación fuzzy de contenido interviene en el veredicto (Opción A — preserva el Principio III).
- **FR-US1-008** (MUST): invariante [[SPEC-000-naming]].

### Key Entities

- **Caso de traducción** (nuevo, `domain/`): ver «Contrato del caso de traducción».
- **TranslationEvaluator** (nuevo, `domain/`): `evaluate(case, agent_response) → resultado`, pura, sin estado ni I/O. Implementa el puerto `Evaluator`.
- **Resultado de traducción** (nuevo, `domain/`): `case_id` + veredicto tri-estado + detalle por campo. Cumple `EvaluatedResult` (SPEC-011 FR-015) y es serializable (`to_dict`).
- **Esquema `{form}`** (existente, `schemas/FI_Orquestador_Input.schema.json`): **salida** del traductor (y entrada del clasificador); referencia compartida del shape.

### Success Criteria

- [ ] **SC-US1-001**: Sobre un fixture de respuesta con `{form}` de taxonomías conocidas, el evaluador emite el veredicto correcto (pass cuando todas coinciden; fail cuando una no, o cuando `tipo_intent` no tiene exactamente un `true`).
- [ ] **SC-US1-002**: La completitud condicionada da pass cuando los esperados-poblados vienen no-vacíos y los esperados-vacíos vienen vacíos; da fail en el caso contrario, sobre fixtures conocidos.
- [ ] **SC-US1-003**: Una respuesta sin `{form}` extraíble, o con un form al que le falta cualquier clave del esquema, produce veredicto **indeterminado** (no fail), con nota.

### Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-US1-001 | modelo de caso en `domain/` + tests de validación (5 entradas no-vacías, `form_esperado` de shape completo) y de derivación (taxonomías, predicados poblado/vacío, referencia fuzzy) |
| FR-US1-002, FR-US1-004, SC-US1-001 | `TranslationEvaluator` en `domain/` + tests de taxonomías (exclusividad, match exacto) |
| FR-US1-003, SC-US1-003 | test de extracción de `{form}` (válido completo, ausente, shape incompleto, con texto accesorio, múltiples objetos) |
| FR-US1-005, SC-US1-002 | tests de completitud condicionada (poblado/vacío por campo) |
| FR-US1-006 | tests del predicado vacío: `""`/whitespace, default-sentinela (vacío) y string no-default (poblado) |
| FR-US1-007 | derivado de SC-US3-001 (variar el nombre no voltea el veredicto) |
| FR-US1-008 | `tools/check_naming.py` sobre `src/` |

## User Story 2 — Caso en circuito: carga, envío y reporte (Priority: P2)

Como operador de la suite quiero **cargar un caso de traducción por archivo, enviarlo al agente y ver el veredicto persistido** por el mismo circuito que el clasificador, **para probar al traductor sobre casos reales dentro de la app y conservar el resultado de cada corrida disponible para revisarlo después**.

**Why this priority:** convierte el evaluador (US1) en algo operable end-to-end. Depende de US1 y del perfil de [[SPEC-011-agent-under-test]]. US1 ya tiene valor por fixtures; esta US lo lleva al circuito real de la app.

**Independent Test:** construir el payload de texto a partir de los textos del caso sin invocar al agente (SC-US2-001), más una corrida real en el dashboard (SC-US2-002).

### Acceptance Scenarios

1. **Given** una respuesta del agente con `{form}` + confirmación de la tool de registro, **When** se procesa el caso, **Then** el constructor/evaluador toma el `{form}` e **ignora** el texto accesorio, siguiendo el circuito común.
2. **Given** un caso cargado por archivo con la entrada (5 textos) y el `form_esperado`, **When** se construye el caso, **Then** produce el **mismo modelo de caso** y entra al circuito común de envío/evaluación/persistencia.

### Functional Requirements

- **FR-US2-001** (MUST): Un **constructor de entrada** en `build/` produce un **`AgentInput` (variante texto)** a partir de los cinco campos del caso, con composición determinista: cada respuesta precedida por el **título de su pregunta** del cuestionario, en el orden del cuestionario, bloques separados por línea en blanco.
  > La serialización al payload del proveedor vive en el adapter ([[SPEC-011-agent-under-test]] FR-014); `build/` permanece puro (Principio II).
- **FR-US2-002** (MUST): El caso de traducción (entrada + esperado) se carga **en runtime por la interfaz**, reutilizando el mecanismo de archivo de SPEC-004/006 extendido al contrato de traducción; el esperado viaja **dentro del archivo** con la representación del «Contrato del caso de traducción» y **no se versiona** (Principio IV). Una entrada vacía o un `form_esperado` de shape incompleto → rechazo en carga con error legible.
  > Los fixtures de los tests del evaluador (`{form}` concretos) son código de test, no datasets operativos.
- **FR-US2-003** (MUST): El veredicto y el detalle por campo se exponen en el dashboard y se persisten en la corrida por el mismo circuito que el clasificador (reutiliza SPEC-005/006 vía el perfil de [[SPEC-011-agent-under-test]]). En modo batch, el resumen estadístico de la corrida del traductor son los **conteos del veredicto tri-estado** calculados sobre la superficie común `EvaluatedResult`.
  > La matriz de confusión y métricas por clase de [[SPEC-008-suite-metrics]] siguen siendo exclusivas del clasificador (ver Fuera de alcance).
- **FR-US2-004** (MUST): invariante [[SPEC-000-naming]].

### Key Entities

- **Constructor de entrada de texto natural** (nuevo, `build/`): produce un `AgentInput` (variante texto) componiendo los 5 textos con los títulos de pregunta (FR-US2-001).
- **Loader de caso de traducción** (extensión del mecanismo de SPEC-004/006): carga entrada + `form_esperado` en runtime, sin versionar datos.

### Success Criteria

- [ ] **SC-US2-001**: El constructor produce, a partir de los textos del caso, un payload de texto natural válido para enviar al traductor (verificable sin invocar al agente).
- [ ] **SC-US2-002** *(verificación funcional en la app real)*: Seleccionado el perfil traductor ([[SPEC-011-agent-under-test]]), un caso real se envía al agente, se extrae el `{form}` de la respuesta y se muestra el veredicto + detalle por campo en el dashboard.

### Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-US2-001, SC-US2-001 | constructor de entrada en `build/` + test de payload de texto natural |
| FR-US2-002 | extensión del loader de caso (SPEC-004/006) + test de carga en runtime de entrada+esperado, sin datos versionados (Principio IV) |
| FR-US2-003, SC-US2-002 | integración con persistencia/render vía perfil de [[SPEC-011-agent-under-test]] + verificación funcional |
| FR-US2-004 | `tools/check_naming.py` sobre `src/` |

## User Story 3 — Similaridad informativa y entrada por pantalla (Priority: P3)

Como operador de la suite quiero (a) una **similaridad fuzzy informativa** del `nombre_iniciativa` y (b) cargar un caso **por pantalla** en modo simple con paridad al flujo del clasificador, **para contar con una señal cualitativa extra al diagnosticar un fallo y para cargar un caso suelto de forma directa desde la pantalla**.

**Why this priority:** dos mejoras **complementarias**. La fuzzy es SHOULD y, por diseño (FR-US1-007), reporta una métrica sin alterar el veredicto; la entrada por pantalla da paridad con el flujo del clasificador (SPEC-001) sobre la carga por archivo (US2). Llegan después del núcleo y el circuito.

**Independent Test:** demostrar que variar solo el texto del nombre no cambia el veredicto (SC-US3-001), y que el envío por pantalla produce el mismo modelo de caso que la carga por archivo con las mismas validaciones (SC-US3-002).

### Acceptance Scenarios

1. **Given** un `{form}` válido, **When** el evaluador compara `nombre_iniciativa` contra el esperado por **similaridad fuzzy normalizada**, **Then** reporta la similaridad como **métrica informativa** que **no** altera el veredicto pass/fail (Opción A: Constitución intacta).
2. **Given** el perfil traductor activo y la entrada por pantalla con los 5 campos y el esperado completos y válidos, **When** el operador envía el caso, **Then** se construye el **mismo modelo de caso** que produciría la carga por archivo y sigue el mismo circuito de envío/evaluación (FR-US3-002).
3. **Given** la entrada por pantalla con algún campo de texto vacío o un `form_esperado` de shape incompleto, **When** el operador intenta enviar, **Then** el envío se **rechaza con error legible antes de invocar al agente** (mismas validaciones que la carga por archivo).

### Functional Requirements

- **FR-US3-001** (SHOULD): El evaluador calcula una **similaridad fuzzy normalizada** (determinista, sin LLM) entre el `nombre_iniciativa` producido y el del `form_esperado`, y la incluye en el detalle como **métrica informativa** (no altera el veredicto). Algoritmo: **`rapidfuzz`** `token_sort_ratio` normalizado a [0,1], tras normalizar ambos textos (casefold + strip + colapso de espacios). Si el `nombre_iniciativa` esperado está vacío (predicado de FR-US1-006), la similaridad **se omite** y el detalle la reporta como no aplicable.
  > Procedencia: el nombre surge de la 1.ª pregunta (`presentacion_iniciativa`), que el traductor vuelca en `nombre_iniciativa`. La dependencia `rapidfuzz` se justifica en `docs/DEVELOPMENT.md` al implementar (única pieza no-stdlib del evaluador; elegida por robustez a reordenamientos de palabras).
- **FR-US3-002** (MUST): Con el perfil traductor activo, el dashboard ofrece **entrada por pantalla** en modo simple (análoga a [[SPEC-001-single-case-input]]): el `id` del caso, los **5 campos de texto** del cuestionario (áreas de texto, en el orden y con los títulos de «Referencia: cuestionario de origen») y la captura del **esperado** (taxonomías cerradas + campos de texto del `form_esperado`). Aplican las validaciones del «Contrato del caso de traducción»; un envío inválido se rechaza con error legible antes de invocar al agente, y el válido produce el **mismo modelo de caso** y circuito que la carga por archivo (FR-US2-002).
- **FR-US3-003** (MUST): invariante [[SPEC-000-naming]].

### Key Entities

- **Cálculo de similaridad fuzzy** (nuevo, `domain/`, sobre el detalle del resultado): determinista, sin LLM; informativo, no graduante del veredicto.
- **Formulario de caso de traducción** (nuevo, `src/dashboard/`): 5 áreas de texto + captura del esperado, con las validaciones del «Contrato del caso de traducción».

### Success Criteria

- [ ] **SC-US3-001**: La similaridad fuzzy de `nombre_iniciativa` se reporta en el detalle y **no** cambia el veredicto entre dos corridas con el mismo resultado de taxonomías/completitud (variar solo el texto del nombre no voltea pass↔fail).
- [ ] **SC-US3-002**: El envío por pantalla inválido se rechaza con error legible antes de invocar al agente; el válido produce el **mismo modelo de caso** que la carga por archivo y sigue el mismo circuito.

### Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-US3-001, SC-US3-001 | test que demuestra que variar solo el texto del nombre no cambia el veredicto y que `nombre_iniciativa` esperado vacío → similaridad no aplicable |
| FR-US3-002, SC-US3-002 | formulario de caso de traducción en `src/dashboard/` (5 áreas de texto + captura del esperado) + test de validación de envío inválido |
| FR-US3-003 | `tools/check_naming.py` sobre `src/` |

## Assumptions (generales)

- El traductor devuelve el `{form}` como JSON en el contenido del mensaje `assistant` (su instrucción dice "devolvé únicamente el JSON válido"), eventualmente acompañado de la confirmación de la tool de registro; el evaluador tolera el texto accesorio (incluidos los títulos de pregunta que antepone el constructor, FR-US2-001).
- El traductor emite **todas las claves** del esquema en el `{form}` (con valor vacío o default cuando el dato no se menciona); por eso un form con claves faltantes es **fallo de producción del shape → indeterminado** (FR-US1-003), no fail. Si esta suposición no se sostuviera, se reabre la frontera válido↔indeterminado en una revisión de la spec.
- La paleta de taxonomías cerradas del `{form}` es estable y coincide con `schemas/FI_Orquestador_Input.schema.json`.
- "Sin LLM-as-judge" es un invariante constitucional (Principio III); la comparación fuzzy elegida es algorítmica, determinista e informativa (no graduante) bajo Opción A.

## Referencia: cuestionario de origen

Definición del formulario **«Intents IA»** (captura de iniciativas) aportada por el usuario el 2026-06-12. Las respuestas en lenguaje natural a estas 5 preguntas son la entrada del traductor; cada pregunta mapea a un campo del caso de traducción. Esta sección es el SSOT del texto del cuestionario dentro del proyecto.

> Consigna del formulario: *"Contanos en lenguaje natural qué querés resolver, en 5 preguntas abiertas. No necesitás definir la solución ni completar campos técnicos: nuestro agente desglosa, estructura y clasifica tu respuesta automáticamente. Cuanto más contexto des, mejor."*

| # | Campo | Título de la pregunta | Texto de la pregunta |
|---|---|---|---|
| 1 | `presentacion_iniciativa` | Presentación e impulso de la iniciativa | ¿Cómo la llamarías en una frase? ¿Desde qué dirección y gerencia la proponés y quién tu gerente y el sponsor del proyecto? ¿Ya la conversaste con algún equipo técnico o es la primera vez que la presentás? Y para ubicarla: ¿forma parte del Plan de Arquitectura TO BE del próximo Q? ¿De qué programa? |
| 2 | `problema_y_objetivo` | El problema y lo que querés lograr | ¿Qué dolor u oportunidad querés atacar y qué te gustaría conseguir? Ayudanos a entender a quién afecta hoy, cómo se resuelve actualmente (si es que se resuelve) y por qué es importante encararlo ahora. |
| 3 | `impacto_y_exito` | Dónde impacta y cómo se vería el éxito | Si esto funcionara, ¿en qué proceso o flujo de trabajo se notaría el cambio y quiénes lo aprovecharían? ¿Cómo sabrías que está dando resultado — qué tiempos, volúmenes, costos o indicadores mirarías? |
| 4 | `solucion_imaginada` | Cómo te imaginás la solución | Por ejemplo, ¿un asistente que responde y conversa, algo que clasifica o deriva casos, que resume documentos, que busca información, que entiende imágenes o voz, que coordina varias tareas? ¿Qué información o datos consumiría y con qué aplicativos o sistemas tendría que conectarse? |
| 5 | `plazos_y_limites` | Plazos, tamaño y límites | ¿Para cuándo te gustaría tenerlo y qué tan grande lo ves para un primer paso? ¿Hay restricciones, supuestos o riesgos a tener en cuenta — datos sensibles, temas regulatorios, presupuesto, dependencias con otras áreas, etc.? |

Notas:

- El cuestionario es la **definición del contrato de entrada** (referencia fija, análoga al schema para la salida); **no** es un dataset operativo, por lo que no viola el Principio IV. Las respuestas concretas de cada caso se cargan en runtime y no se versionan (FR-US2-002).
- Los nombres de campo son agnósticos a la tecnología del formulario (SPEC-000-naming): describen el contenido de la pregunta, no la herramienta de captura.

## Fuera de alcance

- Selección del perfil de agente y registro de perfiles → [[SPEC-011-agent-under-test]].
- Métricas de suite (matriz de confusión) para el traductor: la matriz de [[SPEC-008-suite-metrics]] está definida sobre la paleta de clasificación; su extensión al contrato de traducción es trabajo futuro.
- Graduar el veredicto con la similaridad fuzzy (Opción B): requeriría enmendar la Constitución (Principio III). Queda fuera salvo decisión de gobernanza posterior.
- Verificar la llamada interna del traductor a la tool de registro de la ficha (efecto colateral en la planilla externa): la suite evalúa la traducción, no el registro.

## Historial

- **2026-06-04** — Spec creada (draft) para probar el agente `traductor_intents` (id `3da38f33-3788-44c2-b326-fdbf3cd0605c`), contrato inverso del clasificador. Decisión de gobernanza: **Opción A** — veredicto solo con lo 100% determinista; la fuzzy es informativa (Principio III).
- **2026-06-09** — `/clarify` (4 rondas) + `/analyze`: predicado vacío con defaults-sentinela; frontera válido↔indeterminado por shape completo; ground truth en runtime sin versionar; entrada = 5 campos de texto compuestos en `AgentInput` variante texto. Nombres exactos pendientes.
- **2026-06-12** — `/clarify` (5 rondas): fijados los 5 campos del cuestionario «Intents IA» (sección de referencia = SSOT); esperado = `form_esperado` completo con derivaciones; composición con títulos de pregunta; fuzzy = `rapidfuzz` `token_sort_ratio`; 5 campos obligatorios no-vacíos. Sin marcadores pendientes.
- **2026-06-13** — `/analyze` + `/clarify` + **reorganización en 3 User Stories** (US1 P1, US2 P2, US3 P3; molde de [[SPEC-006-batch-suite]]); FR renombrados a `FR-USn-xxx`. Cerrados huecos: identidad `id`, múltiples objetos JSON, fuzzy con esperado vacío, resumen batch = conteos tri-estado. Decisiones: entrada por pantalla (FR-US3-002); enmienda agnóstica del Principio III (0.5.1→0.5.2, ADR-003 SSOT de evaluadores). 0 conflictos constitucionales; lista para implementar.
- **2026-06-14** — Simplificación editorial (sin cambio de comportamiento): Clarifications condensadas, Historial comprimido, retirada la nota de mapeo FR-NNN→FR-USn.
- **2026-07-05** — Reescritura editorial al formato compacto (convenciones de `docs/SPEC-FORMAT.md`): extraída la sección «Contrato del caso de traducción» como referencia única del modelo de caso, notas separadas de reglas en los FR, coverage agrupado. **Sin cambio normativo**: IDs de FR/SC y su semántica intactos.
