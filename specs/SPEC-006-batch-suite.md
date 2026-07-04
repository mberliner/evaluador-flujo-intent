# SPEC-006-batch-suite — Ejecución batch y estadística de corridas

**Estado:** active
**Iter:** 6
**Formato:** Híbrido
**Depende de:** [[SPEC-004-single-case-file]], [[SPEC-005-run-persistence]], [[SPEC-002-agent-client]], [[SPEC-003-classification-evaluator]]
**Relacionada con:** [[SPEC-008-suite-metrics]], [[SPEC-010-batch-trace]], [[SPEC-013-client-adapter-selection]]

---

## User Story 1 — Ejecución batch (Priority: P2)

Como usuario quiero cargar un **archivo con varios casos** y ejecutarlos en lote, viendo los **resultados conjuntos** (lista por caso + accuracy global) y persistiendo la corrida completa, para evaluar el agente sobre un dataset en una sola pasada.

**Why this priority:** es el salto de "un caso" a "una suite", propósito de producto (ver `docs/PRODUCT.md` §Modo batch). Llega después de fijar carga por archivo (SPEC-004) y esquema de persistencia (SPEC-005), reutilizando ambos en vez de reinventarlos.

**Independent Test:** subo un archivo con N casos → la suite ejecuta los N → veo lista de resultados + accuracy global → la corrida queda persistida como un único run con los N `TestResult`. Verificable sin la matriz de confusión (SPEC-008).

### Acceptance Scenarios

1. **Given** un archivo batch válido de N casos, **When** lo ejecuto, **Then** se evalúan los N casos y se persiste **un** run (SPEC-005) que contiene los N `TestResult`.
2. **Given** un batch ejecutado, **When** veo los resultados, **Then** obtengo accuracy global y el detalle por caso (esperado vs. detectado, veredicto) más la respuesta cruda del agente por caso.
3. **Given** un batch en ejecución, **When** cada caso completa, **Then** el dashboard muestra el progreso (índice/total, `case_id`, veredicto) sin esperar a que termine toda la suite.
4. **Given** un batch con filas inválidas (no pasan la validación de `TestCase`), **When** lo ejecuto, **Then** las filas inválidas se reportan y se cuentan aparte, y el resto de los casos se ejecuta igual (no se aborta la corrida).
5. **Given** un caso del batch que resulta Indeterminado, **When** se computa el accuracy, **Then** cuenta como no-pass en `accuracy_bruta` (denominador = total) y se excluye del denominador en `accuracy_efectiva` (ver User Story 2), reportándose ambas sin perder información (coherente con `docs/PRODUCT.md` "casos sin clasificación < 5%").

**Edge Cases:**

- MUST: El batch vacío o de un solo caso funciona (un caso = corrida de longitud 1, consistente con SPEC-005).
- MUST: El fallo de un envío puntual (error de red/agente) en medio del batch no aborta los demás; el caso fallido se marca y se sigue.
- MUST: Al subir un archivo distinto al anterior, el dashboard descarta el resultado batch previo en pantalla (no mezcla corridas de archivos diferentes).

### Functional Requirements

- **FR-US1-001**: MUST: El sistema acepta un archivo **tabular plano** (una fila por caso, encabezado en la primera fila) y construye una lista de `TestCase`, reutilizando la validación de `TestCase` (la misma regla que el formulario y SPEC-004) sin duplicarla. El parseo tabular vive en `build/`. El separador se **autodetecta** (`;` o `,`), tolerando el export de planilla en español y el CSV estándar.
- **FR-US1-002**: MUST: Las columnas usan los nombres planos de `TestCase`. Obligatorias para un caso válido: `nombre_iniciativa`, `intent_negocio`, `intent_operativo`, `intent_capacidad_equipos`, `intent_tecnico_arquitectural`, `declaracion_intent`, `area_proponente`, `flujo_de_valor`, `metricas_de_exito`, `impacto_personas`, `datos_ninguno`, `datos_publicos`, `datos_operativos`, `datos_personales`, `datos_confidenciales`, `datos_otros`, `supuesto_riesgo`, `restricciones`, `sponsor`, `mail_contacto`. Obligatoria como ground truth: `clasificacion_esperada`. Opcionales: `id` (se genera si está vacío), `datos_otros_mensaje` (requerida sólo si `datos_otros` es verdadero) y `marcadores` (tokens separados por `|`). Los booleanos aceptan `true/false` y `si/no` (insensible a may/min). Las reglas "≥1 intent" y "≥1 categoría de datos" las impone la validación de `TestCase`.
- **FR-US1-003**: MUST: El parser ignora columnas desconocidas presentes en el archivo (p.ej. respuestas Fast Gate por pregunta del dataset de referencia y columnas de cola vacías), porque el `TestCase`/`ClassificationEvaluator` actual (SPEC-003) sólo evalúa `clasificacion_esperada`. La evaluación por pregunta queda fuera de alcance.
- **FR-US1-004**: MUST: El sistema ejecuta los casos contra el agente (SPEC-002, async) y los evalúa (SPEC-003), produciendo un `TestResult` por caso.
- **FR-US1-005**: MUST: El sistema agrega los `TestResult` en un `SuiteResult` (SPEC-005) y lo persiste como **un** run, apendeando una fila por caso a `estadistica-casos.csv`. El archivo de detalle batch se nombra `run-<ts>.json` (sin sufijo de caso, porque la corrida representa N casos; ver ADR-004).
- **FR-US1-006**: MUST: El sistema expone una ejecución **headless** (sin UI) en `src/runner` (invocable como `python -m src.runner`, consistente con `docs/DEVELOPMENT.md`). El runner compone `build/` + `adapters/` + `domain/`; no es importado por `domain/` y no depende del framework de UI.
- **FR-US1-007**: MUST: El reporte conjunto incluye accuracy global y detalle por caso. El **cómputo** de agregados vive en `domain/`; el dashboard solo renderiza.
- **FR-US1-008**: MUST: Durante la ejecución batch, el progreso se reporta **por caso** a medida que cada uno completa (índice/total, `case_id`, veredicto). El índice de cada fila es su posición fija de finalización (1-based), no el tamaño del slice al momento del rerender. El runner expone un callback de progreso opcional; el dashboard lo renderiza en vivo y el entrypoint headless lo imprime por línea a medida que avanza.
- **FR-US1-009**: MUST: El detalle por caso en el dashboard permite ver la **respuesta cruda** del agente de cada caso (no sólo esperado/detectado/veredicto), consistente con lo ya persistido en el JSON de detalle.
- **FR-US1-010**: MUST: Un envío individual que falle no aborta la suite; el caso se marca como fallido y la corrida continúa.

### Key Entities

- **SuiteResult** (de SPEC-005): ahora ejercitado con N `TestResult`; agrega el bloque `summary`. (Sus cómputos `accuracy_bruta`/`accuracy_efectiva` se ejercen en User Story 2.)
- **Archivo batch**: documento tabular plano (planilla), una fila por caso, separador autodetectado (`;` o `,`). Columnas = nombres planos de `TestCase` (ver FR-US1-002); `clasificacion_esperada` obligatoria, `id`/`datos_otros_mensaje`/`marcadores` opcionales, columnas desconocidas ignoradas. Toma como referencia de schema `intake_clasificacion.csv` (raíz del workspace padre), simplificado: se omiten las columnas orientativas `resultado_p1..p5`. Difiere del unitario (SPEC-004, estructurado/anidado): aquí prima la edición masiva en planilla.
- **Orquestador de suite (runner)**: módulo `src/runner` que compone carga (`build/`) + cliente (`adapters/`) + evaluador (`domain/`) + persistencia (`adapters/`). Punto de entrada headless `python -m src.runner`. No es importado por `domain/`.

### Success Criteria

- [x] **SC-US1-001**: una corrida de N casos produce un único run persistido con N resultados.
- [x] **SC-US1-002**: el accuracy global reportado coincide con el conteo manual de Pass sobre total (definición de `docs/PRODUCT.md`).
- [x] **SC-US1-003**: la suite headless corre sin abrir UI y escribe el run en `runs/`.
- [x] **SC-US1-004**: un fallo puntual de envío no reduce la cantidad de casos restantes ejecutados.

### Assumptions

- El esquema de run de SPEC-005 escala a N casos sin cambios de fondo.

### Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-US1-001 | `src/build/` parser tabular (autodetección de separador) + tests (válido / con inválidas) |
| FR-US1-002 | tests de mapeo de columnas a `TestCase` (obligatorias, opcionales, booleanos `true/false` y `si/no`) |
| FR-US1-003 | test de archivo con columnas desconocidas (`resultado_p*`, cola vacía) que se ignoran |
| FR-US1-004, FR-US1-005 | orquestador `src/runner` + tests con cliente/evaluador stubbeados |
| FR-US1-006 | entrypoint headless `python -m src.runner` + test de smoke headless |
| FR-US1-007 | función de agregación en `domain/` + test de accuracy global |
| FR-US1-008 | callback de progreso en `run_batch` (test: una invocación por caso) + impresión por línea en `main` (headless) y placeholder en el dashboard |
| FR-US1-009 | expander por caso en `src/dashboard/app.py` (respuesta cruda) + verificación funcional |
| FR-US1-010 | test de batch con un envío que lanza error |
| SC-US1-001 | test que verifica N TestResult en SuiteResult persistido |
| SC-US1-002 | test de accuracy global en `domain/` |
| SC-US1-003 | test de smoke headless |
| SC-US1-004 | test de batch con envío fallido simulado |

### Fuera de alcance

- Traza del agente por caso en batch (y su persistencia) → [[SPEC-010-batch-trace]].
- **Evaluación del Fast Gate por pregunta** (`resultado_p1..p5` del dataset de referencia): el `TestCase`/`ClassificationEvaluator` actual sólo evalúa `clasificacion_esperada`; ampliar el ground truth a las 5 preguntas requiere extender el modelo y el evaluador → deuda, candidata a spec propia.

---

## User Story 2 — Estadística de corridas a pedido (Priority: P3)

Como usuario quiero **generar, desde la misma pantalla y a pedido**, una estadística agregada por corrida (`estadistica-corridas.csv`) con el accuracy de cada ejecución, para comparar el desempeño del agente entre corridas sin abrir cada JSON de detalle.

**Why this priority:** depende de que exista la noción de corrida con N casos (User Story 1). El accuracy agregado sólo tiene sentido sobre una corrida completa; en modo unitario (SPEC-005) sería redundante con el veredicto, por eso se difirió hasta acá. Es P3 porque la suite ya es usable sin este CSV: el accuracy global ya se muestra en pantalla (User Story 1) y el `summary` ya vive en el detalle.

**Independent Test:** con al menos una corrida persistida, presiono el control de "generar estadística de corridas" → aparece/actualiza `runs/stats/estadistica-corridas.csv` con una fila por corrida y sus columnas de accuracy → reabro el archivo y los valores coinciden con el `summary` del detalle. Verificable sin re-ejecutar el agente.

### Acceptance Scenarios

1. **Given** una o más corridas persistidas, **When** disparo la generación de estadística desde la pantalla, **Then** `runs/stats/estadistica-corridas.csv` contiene una fila por corrida con `run_id`, `timestamp`, `agent_id`, `endpoint_url`, `total`, `pass`, `fail`, `indeterminado`, `accuracy_bruta` y `accuracy_efectiva`.
2. **Given** una corrida donde **todos** los casos son Indeterminado, **When** se computa `accuracy_efectiva`, **Then** el valor es `null` (denominador cero) y `accuracy_bruta` es `0.0`, sin que el sistema falle por división por cero.
3. **Given** `estadistica-corridas.csv` ya generado, **When** lo genero de nuevo, **Then** se regenera completo releyendo todos los detalles de `runs/detail/` y reescribiendo el archivo entero (operación idempotente, sin filas duplicadas).
4. **Given** varias corridas persistidas, **When** genero la estadística, **Then** el CSV termina con una fila `TOTAL` que suma todos los casos de todas las corridas y reporta `accuracy_bruta`/`accuracy_efectiva` globales, y el dashboard muestra esos totales.

**Edge Cases:**

- MUST: `accuracy_efectiva` con denominador cero (todos Indeterminado) devuelve `null`, no error.

### Functional Requirements

- **FR-US2-001**: MUST: El sistema computa, por corrida, `accuracy_bruta = pass / total` y `accuracy_efectiva = pass / (total - indeterminado)` (definiciones SSOT en `docs/PRODUCT.md` §Métricas; si difieren, manda PRODUCT.md). Ambos cómputos viven en `domain/` (sobre `SuiteResult`), no en el dashboard.
- **FR-US2-002**: MUST: Si `total - indeterminado == 0`, `accuracy_efectiva` es `null`; el sistema no lanza error de división por cero.
- **FR-US2-003**: MUST: El dashboard expone un control que, **a pedido del usuario**, dispara la generación de `runs/stats/estadistica-corridas.csv` (separador `;`) con una fila por corrida y las columnas `run_id`, `timestamp`, `agent_id`, `endpoint_url`, `total`, `pass`, `fail`, `indeterminado`, `accuracy_bruta`, `accuracy_efectiva`. La columna `endpoint_url` es la URL efectiva del endpoint/agente bajo test de esa corrida (campo `SuiteResult.endpoint_url` de [[SPEC-005-run-persistence]], requisito originado en [[SPEC-013-client-adapter-selection]] User Story 2); queda vacía para corridas persistidas antes de existir ese campo.
- **FR-US2-004**: MUST: La generación **regenera el archivo completo** releyendo todas las corridas persistidas en `runs/detail/`; es idempotente y no produce filas duplicadas si se la invoca repetidamente.
- **FR-US2-005**: MUST: El CSV incluye, **al final**, una fila `TOTAL` con la estadística general sobre **todos los casos de todas las corridas**: suma de `total`/`pass`/`fail`/`indeterminado` y `accuracy_bruta`/`accuracy_efectiva` globales (`pass_total / total` y `pass_total / (total − indeterminado)`). El cómputo vive en `domain/` (`aggregate_runs`); la fila se omite si no hay corridas. La columna `endpoint_url` de la fila `TOTAL` queda vacía (no aplica a un agregado multi-corrida que puede mezclar endpoints distintos). El dashboard muestra además estos totales al generar.
- **FR-US2-006**: MUST: La generación de la estadística de corridas **no** invoca al agente; opera sobre las corridas ya persistidas / el `SuiteResult` en memoria.
- **FR-US2-007**: MUST: Ningún identificador de código nombra el formato (`csv`, `json`) ni el framework de UI (SPEC-000-naming).

### Key Entities

- **SuiteResult** (de SPEC-005): expone `accuracy_bruta` y `accuracy_efectiva` como cómputos puros del dominio.
- **Escritor de estadística de corridas**: en `adapters/` (parte de `FileRunRepository` o colaborador), escribe `estadistica-corridas.csv`. Identificador agnóstico al formato.

### Success Criteria

- [x] **SC-US2-001**: al disparar la estadística desde la pantalla, `estadistica-corridas.csv` contiene una fila por corrida cuyos `accuracy_bruta` / `accuracy_efectiva` coinciden con el `summary` del detalle.
- [x] **SC-US2-002**: una corrida con todos los casos Indeterminado produce `accuracy_efectiva = null` y `accuracy_bruta = 0.0`, sin error.
- [x] **SC-US2-003**: verificación funcional en la app real — ejecuto un batch, genero la estadística a pedido y abro el CSV resultante.
- [x] **SC-US2-004**: la fila `TOTAL` del CSV coincide con la suma manual de casos y con el accuracy global calculado sobre todos los `TestResult`.

### Assumptions

- Las métricas de `docs/PRODUCT.md` (accuracy global, por clase, % sin clasificación) son el SSOT; esta historia implementa el accuracy global (bruta/efectiva), dejando matriz/por-clase a SPEC-008.
- `estadistica-casos.csv` ya lo genera SPEC-005; esta historia sólo agrega `estadistica-corridas.csv`.

### Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-US2-001 | métodos `accuracy_bruta` / `accuracy_efectiva` en `SuiteResult` + tests de cómputo |
| FR-US2-002 | test de denominador cero (todos Indeterminado) |
| FR-US2-003 | control en `src/dashboard/app.py` + test del escritor de `estadistica-corridas.csv` (incl. columna `endpoint_url`, requisito de [[SPEC-013-client-adapter-selection]] User Story 2) |
| FR-US2-004 | test de idempotencia: regenerar dos veces produce el mismo archivo, sin duplicados |
| FR-US2-005 | `aggregate_runs` en `domain/` + test de la fila TOTAL (suma y accuracy global) + métricas en el dashboard |
| FR-US2-006 | garantía estructural: `FileRunRepository.regenerate_run_stats` opera sobre `runs/detail/` y no recibe el cliente del agente, por lo que no puede invocarlo (cubierto por los tests de `regenerate_run_stats` en `test_file_run_repository.py`) |
| FR-US2-007 | `tools/check_naming.py` |
| SC-US2-001 | test del escritor + verificación contra `summary` del detalle |
| SC-US2-002 | test de denominador cero (cubierto por FR-US2-002) |
| SC-US2-003 | verificación funcional en la app real |
| SC-US2-004 | test que compara la fila TOTAL contra la suma manual de los `TestResult` |

### Fuera de alcance

- Matriz de confusión, accuracy por clase, % sin clasificación como vista → [[SPEC-008-suite-metrics]].
- Comparación histórica entre runs / tendencias (este CSV habilita el insumo; la visualización comparada es posterior).

---

## User Story 3 — Parada manual de la corrida batch (Priority: P3)

Como usuario quiero **frenar una corrida batch en curso y quedarme con los resultados de los casos ya completados** (sin el caso en vuelo ni los pendientes), tanto en el runner headless como en el dashboard, para no perder el trabajo hecho cuando una corrida larga se tuerce o ya vi lo que necesitaba.

**Why this priority:** la suite ya es usable sin esto (User Story 1); es una mejora de operación para corridas largas. Llega después de que existe la noción de corrida con N casos y su persistencia. P3 porque no cambia el formato del run ni las métricas: reusa la finalización ya existente sobre un subconjunto de casos.

**Independent Test:** lanzo una corrida de N casos, la freno tras K completados (Ctrl+C en headless / botón "Frenar" en el dashboard) → se persiste **un** run con exactamente K `TestResult` y las métricas se computan sobre esos K. Verificable sin ejecutar los N casos.

### Acceptance Scenarios

1. **Given** una corrida headless en curso, **When** envío SIGINT (Ctrl+C), **Then** el caso en vuelo se descarta (no produce resultado), los pendientes no se lanzan, y la corrida se cierra y persiste con los casos completados.
2. **Given** una corrida en el dashboard en curso, **When** presiono "Frenar", **Then** no se lanzan más casos y la corrida se cierra y persiste con los casos completados hasta ese momento; el detalle indica que fue una parada manual.
3. **Given** una parada manual con K de N casos completados, **When** se persiste, **Then** el run contiene exactamente K `TestResult` y las métricas se computan sobre esos K (igual que una corrida de longitud K).
4. **Given** una parada manual sin ningún caso completado, **When** freno, **Then** el sistema no persiste un run vacío y lo informa.

**Edge Cases:**

- MUST: La corrida parcial es un `SuiteResult` válido de longitud K, indistinguible en formato de una corrida de K casos (round-trip de persistencia intacto).
- **Diferencia de granularidad documentada (esperada, no un defecto):** en headless el caso en vuelo se **aborta** (Ctrl+C es asincrónico y corta el `wait_for_completion`); en el dashboard el caso que se está ejecutando al momento del click **termina y se incluye**, y se frena antes del siguiente (Streamlit no interrumpe un caso en curso). En ambos, el/los caso(s) que no llegaron a completarse y los pendientes quedan fuera.

### Functional Requirements

- **FR-US3-001**: MUST: El runner headless captura SIGINT (Ctrl+C) durante la ejecución batch; el caso en vuelo se descarta sin resultado, los pendientes no se lanzan, y `run_batch` devuelve los `TestResult` acumulados.
- **FR-US3-002**: MUST: Tras una parada, el entrypoint headless construye y persiste el `SuiteResult` con los casos completados (la misma ruta que una corrida normal) e informa por consola cuántos de los N solicitados se completaron.
- **FR-US3-003**: MUST: El dashboard ejecuta el batch de forma **interrumpible** (un caso a la vez, cediendo el control a la interfaz entre casos) y expone un control "Frenar" que cierra la corrida con los casos completados.
- **FR-US3-004**: MUST: La finalización (armar `SuiteResult` + persistir) es **idéntica** venga de una corrida completa o de una parada manual; la corrida parcial es un `SuiteResult` de longitud K sin campos especiales que la distingan en el detalle persistido.
- **FR-US3-005**: MUST: Una parada sin casos completados **no** persiste un run vacío y se informa al usuario.
- **FR-US3-006**: MUST: Ningún identificador nombra el framework de UI ni el mecanismo de señal del SO (SPEC-000-naming).

### Key Entities

- **run_batch (runner)**: ahora corta limpio ante `KeyboardInterrupt`, devolviendo los resultados acumulados (parada cooperativa por descarte del caso en vuelo).
- **Finalización compartida**: `SuiteResult.create(resultados_completados)` + persistencia (`FileRunRepository`), reutilizada por headless y dashboard.

### Success Criteria

- [x] **SC-US3-001**: en headless, una interrupción tras K casos produce un `SuiteResult` con exactamente K resultados (test con `KeyboardInterrupt` simulado en el cliente).
- [x] **SC-US3-002**: el run parcial es indistinguible en formato de una corrida de K casos (se arma y persiste por la misma ruta; round-trip intacto).
- [x] **SC-US3-003**: verificación funcional en el dashboard — freno una corrida a mitad y el run guardado contiene solo los casos completados, con la nota de parada manual.

### Assumptions

- El `SuiteResult` de SPEC-005 representa sin cambios una corrida de longitud K < N.
- La granularidad de la parada difiere por plataforma (ver Edge Cases) y es aceptable: el invariante es "no se incluyen casos que no completaron".

### Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-US3-001 | `except KeyboardInterrupt: break` en `run_batch` + test que verifica K resultados y descarte del caso en vuelo |
| FR-US3-002 | rama de corrida parcial en `main` (mensaje + persistencia) + test de `build_suite` parcial |
| FR-US3-003 | ejecución por casos con `fragment` interrumpible + botón "Frenar" en `src/dashboard/app.py` |
| FR-US3-004 | finalización compartida (`SuiteResult.create` + `FileRunRepository.save`) + test de round-trip del run parcial |
| FR-US3-005 | guarda de "sin casos completados" en `main` (headless) y en `_finalize_batch` (dashboard) |
| FR-US3-006 | `tools/check_naming.py` |
| SC-US3-001 | test con `KeyboardInterrupt` simulado |
| SC-US3-002 | test de persistencia/round-trip del run parcial |
| SC-US3-003 | verificación funcional en la app real |

### Fuera de alcance

- Reanudar (resume) una corrida frenada desde donde quedó: acá solo se cierra con lo hecho.
- Interrumpir un caso individual en curso en el dashboard (Streamlit no lo permite sin threads; se acepta que el caso actual termina).

---

## Historial

- **2026-05-25** — Spec creada en formato híbrido. Absorbe el viejo SPEC-004-batch-input + la parte de ejecución del viejo SPEC-005-runner. Métricas avanzadas (matriz, por-clase) separadas a SPEC-008.
- **2026-05-26** — Añadida User Story 2 (estadística de corridas a pedido) y reestructurada la spec para que cada HU agrupe sus propios Acceptance / FR / SC. Se trasladó aquí `estadistica-corridas.csv` desde SPEC-005 porque el accuracy agregado sólo tiene sentido con N casos. Resuelto el tratamiento de Indeterminado en accuracy: se reportan **dos** columnas — `accuracy_bruta` (denominador = total) y `accuracy_efectiva` (denominador = total − indeterminado, `null` si es cero). La generación se dispara desde la misma pantalla, a pedido, sin invocar al agente.
- **2026-05-26** — Resueltos los 4 `[NEEDS CLARIFICATION]` con el usuario: (1) **filas inválidas** → se reportan y cuentan aparte, el resto se ejecuta (no aborta); (2) **runner headless** → módulo `src/runner` (`python -m src.runner`); (3) **formato batch** → CSV tabular plano con separador autodetectado (`;`/`,`), columnas = nombres planos de `TestCase` (los nombres se simplificaron respecto del dataset de referencia, que el usuario habilitó a cambiar), `clasificacion_esperada` obligatoria, `marcadores` opcional, columnas orientativas `resultado_p1..p5` omitidas/ignoradas; (4) **regeneración del CSV de corridas** → regenerar completo desde `runs/detail/` (idempotente). Se tomó `intake_clasificacion.csv` (raíz) como referencia de schema. La evaluación Fast Gate por pregunta queda como deuda fuera de alcance.
- **2026-05-26** — Implementada y cerrada (`draft` → `active`). Agregados durante la implementación, acordados con el usuario: visibilidad por caso (FR-005b progreso en vivo headless + dashboard; FR-005c respuesta cruda por caso), separador `;` en los CSV de estadística, naming del detalle batch `run-<ts>.json` (sin sufijo de caso), manejo controlado de archivo inexistente/ilegible en el runner, y estadística general con fila `TOTAL` (FR-009c, `aggregate_runs` en `domain/`). Títulos del dashboard reescritos para reflejar la funcionalidad. Pipeline local VERDE 8/8 (158 tests); SC-003 (headless) y SC-007 (dashboard) verificados en la app real por el usuario. *(Las referencias FR/SC de esta entrada usan la numeración previa a la migración del 2026-05-27; ver el mapeo abajo.)*
- **2026-06-01** — Añadida **User Story 3 — Parada manual de la corrida batch** (P3). Headless: `run_batch` corta ante `KeyboardInterrupt` (Ctrl+C) descartando el caso en vuelo; `main` cierra y persiste la corrida parcial e informa K/N. Dashboard: ejecución interrumpible por casos con `fragment` (un caso por tick, cediendo control entre casos) + botón "Frenar"; finalización compartida (`SuiteResult.create` + persistencia). `_execution_failure` → `execution_failure` (ahora reutilizada por el dashboard). Diferencia de granularidad documentada (headless aborta el caso en vuelo; dashboard lo termina y frena antes del siguiente). SC-US3-003 (dashboard) pendiente de verificación funcional en la app real.
- **2026-06-07** — Por [ADR-005](../docs/ARCHITECTURE.md) la orquestación (`run_one`, `run_batch`, `build_suite`, `execution_failure`) se mueve de `src/runner` a `src/application/run_suite.py`. `src/runner` sigue siendo el entrypoint headless `python -m src.runner` y composition root que invoca el use-case (FR-US1-006 sin cambio de comportamiento: sólo cambia dónde vive la orquestación). El stepping batch del dashboard (US3) permanece en `dashboard/` y reutiliza `application.run_one`. Las menciones a `src/runner`/`run_batch` en los FR se leen como "el use-case en `application/`, invocado por el composition root". **Implementado**: `run_one`/`run_batch`/`build_suite`/`execution_failure` viven en `src/application/run_suite.py`; `src/runner` los re-exporta por compatibilidad e invoca el use-case como composition root. Sin cambio de comportamiento.
- **2026-06-07** — Pase de consistencia spec↔código (`/analyze`): (1) `SC-US3-003` marcado `[x]` tras verificación funcional del "Frenar" en el dashboard; (2) corregida la entrada ADR-005 (la orquestación en `src/application/run_suite.py` ya está implementada, no pendiente); (3) el mapping de `FR-US2-006` se hizo veraz — describe la garantía estructural (`regenerate_run_stats` no recibe el cliente) en vez de un test inexistente. Deuda restante: US1 carece de un SC de verificación funcional propio para sus FRs de UI (`FR-US1-008/009`); FR-US2-006 podría reforzarse con un test-espía explícito.
- **2026-07-03** — Ampliación de esquema (spec viva) a pedido de [[SPEC-013-client-adapter-selection]] User Story 2: `estadistica-corridas.csv` agrega la columna `endpoint_url` (FR-US2-003), poblada desde `SuiteResult.endpoint_url` ([[SPEC-005-run-persistence]]); la fila `TOTAL` la deja vacía (FR-US2-005). SPEC-006 sigue siendo el único SSOT de las columnas del CSV; SPEC-013 sólo consume el campo. **Implementado** el 2026-07-03 (columna `endpoint_url` en `_RUN_STATS_COLUMNS`, poblada por corrida y vacía en `TOTAL`; verificado en `test_file_run_repository.py`).
- **2026-05-27** — Migrada al **estándar multi-HU** (cada HU encapsulada de inicio a fin con sus propias Key Entities/Assumptions/Coverage/Fuera de alcance; numeración de FR/SC prefijada por HU), formalizado en `docs/SPEC-FORMAT.md`. Renumeración sin cambio de comportamiento — US1: FR-001→FR-US1-001, FR-001b→FR-US1-002, FR-001c→FR-US1-003, FR-002→FR-US1-004, FR-003→FR-US1-005, FR-004→FR-US1-006, FR-005→FR-US1-007, FR-005b→FR-US1-008, FR-005c→FR-US1-009, FR-006→FR-US1-010, SC-001..004→SC-US1-001..004; US2: FR-007→FR-US2-001, FR-008→FR-US2-002, FR-009→FR-US2-003, FR-009b→FR-US2-004, FR-009c→FR-US2-005, FR-010→FR-US2-006, FR-011→FR-US2-007, SC-005..008→SC-US2-001..004. Las entradas previas del historial conservan la numeración vieja (registro de su fecha). El puntero de traza ("Traza del agente") se reapuntó de `notas SPEC-007` a [[SPEC-010-batch-trace]].
