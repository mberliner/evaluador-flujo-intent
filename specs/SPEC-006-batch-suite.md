# SPEC-006-batch-suite — Ejecución batch y estadística de corridas

**Estado:** active
**Iter:** 6
**Formato:** Híbrido
**Depende de:** [[SPEC-004-single-case-file]], [[SPEC-005-run-persistence]], [[SPEC-002-agent-client]], [[SPEC-003-classification-evaluator]]
**Relacionada con:** [[SPEC-008-suite-metrics]], [[SPEC-010-batch-trace]]

**Resumen:** La suite ejecuta un archivo tabular de N casos en lote y persiste la corrida completa como un único run ([[SPEC-005-run-persistence]]). Tres cortes: **US1** ejecución batch con progreso por caso, runner headless y accuracy global (P2); **US2** estadística agregada por corrida a pedido, `estadistica-corridas.csv` (P3); **US3** parada manual conservando los casos completados (P3). Las tres cerradas con verificación funcional.

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
5. **Given** un caso del batch que resulta Indeterminado, **When** se computa el accuracy, **Then** cuenta como no-pass en `accuracy_bruta` y se excluye del denominador en `accuracy_efectiva` (ver User Story 2), reportándose ambas sin perder información.

**Edge Cases:**

- MUST: El batch vacío o de un solo caso funciona (un caso = corrida de longitud 1, consistente con SPEC-005).
- MUST: El fallo de un envío puntual (error de red/agente) en medio del batch no aborta los demás; el caso fallido se marca y se sigue.
- MUST: Al subir un archivo distinto al anterior, el dashboard descarta el resultado batch previo en pantalla (no mezcla corridas de archivos diferentes).

### Functional Requirements

- **FR-US1-001**: MUST: El sistema acepta un archivo **tabular plano** (una fila por caso, encabezado en la primera fila), **autodetecta** el separador (`;` o `,` — tolera el export de planilla en español y el CSV estándar) y construye una lista de `TestCase`, reutilizando la validación de `TestCase` (la misma regla que el formulario y SPEC-004) sin duplicarla. El parseo tabular vive en `build/`.
- **FR-US1-002**: MUST: Las columnas usan los nombres planos de `TestCase`. Obligatorias para un caso válido: `nombre_iniciativa`, `intent_negocio`, `intent_operativo`, `intent_capacidad_equipos`, `intent_tecnico_arquitectural`, `declaracion_intent`, `area_proponente`, `flujo_de_valor`, `metricas_de_exito`, `impacto_personas`, `datos_ninguno`, `datos_publicos`, `datos_operativos`, `datos_personales`, `datos_confidenciales`, `datos_otros`, `supuesto_riesgo`, `restricciones`, `sponsor`, `mail_contacto`. Obligatoria como ground truth: `clasificacion_esperada`. Opcionales: `id` (se genera si está vacío), `datos_otros_mensaje` (requerida sólo si `datos_otros` es verdadero) y `marcadores` (tokens separados por `|`). Los booleanos aceptan `true/false` y `si/no` (insensible a may/min); las reglas "≥1 intent" y "≥1 categoría de datos" las impone la validación de `TestCase`.
- **FR-US1-003**: MUST: El parser ignora columnas desconocidas presentes en el archivo (p. ej. `resultado_p1..p5` del dataset de referencia y columnas de cola vacías).
  > El `TestCase`/`ClassificationEvaluator` vigente (SPEC-003) sólo evalúa `clasificacion_esperada`; la evaluación por pregunta queda fuera de alcance (ver «Fuera de alcance»).
- **FR-US1-004**: MUST: El sistema ejecuta los casos contra el agente (SPEC-002, async) y los evalúa (SPEC-003), produciendo un `TestResult` por caso.
- **FR-US1-005**: MUST: El sistema agrega los `TestResult` en un `SuiteResult` (SPEC-005) y lo persiste como **un** run, apendeando una fila por caso a `estadistica-casos.csv`. El detalle batch se nombra `run-<ts>.json`, sin sufijo de caso (ADR-004: la corrida representa N casos).
- **FR-US1-006**: MUST: El sistema expone una ejecución **headless** (sin UI) en `src/runner` (invocable como `python -m src.runner`, consistente con `docs/DEVELOPMENT.md`). El runner compone `build/` + `adapters/` + `domain/`; no es importado por `domain/` y no depende del framework de UI.
- **FR-US1-007**: MUST: El reporte conjunto incluye accuracy global y detalle por caso. El **cómputo** de agregados vive en `domain/`; el dashboard solo renderiza.
- **FR-US1-008**: MUST: Durante la ejecución batch, el progreso se reporta **por caso** a medida que cada uno completa (índice/total, `case_id`, veredicto); el índice de cada fila es su posición fija de finalización (1-based), no el tamaño del slice al momento del rerender. El runner expone un callback de progreso opcional; el dashboard lo renderiza en vivo y el entrypoint headless lo imprime por línea.
- **FR-US1-009**: MUST: El detalle por caso en el dashboard permite ver la **respuesta cruda** del agente de cada caso, consistente con lo persistido en el JSON de detalle.
- **FR-US1-010**: MUST: Un envío individual que falle no aborta la suite; el caso se marca como fallido y la corrida continúa.

### Key Entities

- **SuiteResult** (de SPEC-005): ahora ejercitado con N `TestResult`; agrega el bloque `summary`. (Sus cómputos `accuracy_bruta`/`accuracy_efectiva` se ejercen en User Story 2.)
- **Archivo batch**: documento tabular plano (planilla), una fila por caso; separador y columnas según FR-US1-001/FR-US1-002. Referencia de schema: `intake_clasificacion.csv` (raíz del workspace padre), simplificado (se omiten las columnas orientativas `resultado_p1..p5`). Difiere del unitario (SPEC-004, estructurado/anidado): aquí prima la edición masiva en planilla.
- **Orquestador de suite (runner)**: módulo `src/runner`, punto de entrada headless `python -m src.runner`, compone carga (`build/`) + cliente (`adapters/`) + evaluador (`domain/`) + persistencia (`adapters/`). No es importado por `domain/`.

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
| FR-US1-001, FR-US1-002, FR-US1-003 | parser tabular en `src/build/` + tests (separador autodetectado, mapeo de columnas obligatorias/opcionales, booleanos `true/false` y `si/no`, filas inválidas reportadas, columnas desconocidas ignoradas) |
| FR-US1-004, FR-US1-005, SC-US1-001 | orquestador batch + tests con cliente/evaluador stubbeados (N `TestResult` en un único run persistido) |
| FR-US1-006, SC-US1-003 | entrypoint headless `python -m src.runner` + test de smoke headless |
| FR-US1-007, SC-US1-002 | función de agregación en `domain/` + test de accuracy global |
| FR-US1-008 | callback de progreso en `run_batch` (test: una invocación por caso, índice fijo 1-based) + impresión por línea en headless y render en vivo en el dashboard |
| FR-US1-009 | expander por caso en `src/dashboard/app.py` (respuesta cruda) + verificación funcional |
| FR-US1-010, SC-US1-004 | test de batch con un envío que lanza error |

### Fuera de alcance

- Traza del agente por caso en batch (y su persistencia) → [[SPEC-010-batch-trace]].
- **Evaluación del Fast Gate por pregunta** (`resultado_p1..p5`): ampliar el ground truth a las 5 preguntas requiere extender el modelo y el evaluador → deuda, candidata a spec propia.

---

## User Story 2 — Estadística de corridas a pedido (Priority: P3)

Como usuario quiero **generar, desde la misma pantalla y a pedido**, una estadística agregada por corrida (`estadistica-corridas.csv`) con el accuracy de cada ejecución, para comparar el desempeño del agente entre corridas sin abrir cada JSON de detalle.

**Why this priority:** depende de que exista la noción de corrida con N casos (User Story 1). El accuracy agregado sólo tiene sentido sobre una corrida completa; en modo unitario (SPEC-005) sería redundante con el veredicto. Es P3 porque la suite ya es usable sin este CSV: el accuracy global ya se muestra en pantalla y el `summary` ya vive en el detalle.

**Independent Test:** con al menos una corrida persistida, presiono el control de "generar estadística de corridas" → aparece/actualiza `runs/stats/estadistica-corridas.csv` con una fila por corrida y sus columnas de accuracy → reabro el archivo y los valores coinciden con el `summary` del detalle. Verificable sin re-ejecutar el agente.

### Acceptance Scenarios

1. **Given** una o más corridas persistidas, **When** disparo la generación de estadística desde la pantalla, **Then** `runs/stats/estadistica-corridas.csv` contiene una fila por corrida con `run_id`, `timestamp`, `agent_id`, `total`, `pass`, `fail`, `indeterminado`, `accuracy_bruta` y `accuracy_efectiva`.
2. **Given** una corrida donde **todos** los casos son Indeterminado, **When** se computa `accuracy_efectiva`, **Then** el valor es `null` (denominador cero) y `accuracy_bruta` es `0.0`, sin que el sistema falle por división por cero.
3. **Given** `estadistica-corridas.csv` ya generado, **When** lo genero de nuevo, **Then** se regenera completo releyendo todos los detalles de `runs/detail/` y reescribiendo el archivo entero (operación idempotente, sin filas duplicadas).
4. **Given** varias corridas persistidas, **When** genero la estadística, **Then** el CSV termina con una fila `TOTAL` que suma todos los casos de todas las corridas y reporta `accuracy_bruta`/`accuracy_efectiva` globales, y el dashboard muestra esos totales.

**Edge Cases:**

- MUST: `accuracy_efectiva` con denominador cero (todos Indeterminado) devuelve `null`, no error.

### Functional Requirements

- **FR-US2-001**: MUST: El sistema computa, por corrida, `accuracy_bruta = pass / total` y `accuracy_efectiva = pass / (total - indeterminado)` (definiciones SSOT en `docs/PRODUCT.md` §Métricas; si difieren, manda PRODUCT.md). Ambos cómputos viven en `domain/` (sobre `SuiteResult`), no en el dashboard.
- **FR-US2-002**: MUST: Si `total - indeterminado == 0`, `accuracy_efectiva` es `null`; el sistema no lanza error de división por cero.
- **FR-US2-003**: MUST: El dashboard expone un control que, **a pedido del usuario**, genera `runs/stats/estadistica-corridas.csv` (separador `;`) con una fila por corrida y las columnas `run_id`, `timestamp`, `agent_id`, `total`, `pass`, `fail`, `indeterminado`, `accuracy_bruta`, `accuracy_efectiva`.
- **FR-US2-004**: MUST: La generación **regenera el archivo completo** releyendo todas las corridas persistidas en `runs/detail/`; es idempotente y no produce filas duplicadas si se la invoca repetidamente.
- **FR-US2-005**: MUST: El CSV incluye, **al final**, una fila `TOTAL` con la estadística sobre **todos los casos de todas las corridas** (suma de `total`/`pass`/`fail`/`indeterminado` y `accuracy_bruta`/`accuracy_efectiva` globales). El cómputo vive en `domain/` (`aggregate_runs`); la fila se omite si no hay corridas. El dashboard muestra además estos totales al generar.
- **FR-US2-006**: MUST: La generación de la estadística de corridas **no** invoca al agente; opera sobre las corridas ya persistidas / el `SuiteResult` en memoria.
- **FR-US2-007**: MUST: invariante [[SPEC-000-naming]] — ningún identificador nombra el formato (`csv`, `json`) ni el framework de UI.

### Key Entities

- **SuiteResult** (de SPEC-005): expone `accuracy_bruta` y `accuracy_efectiva` como cómputos puros del dominio.
- **Escritor de estadística de corridas**: en `adapters/` (parte de `FileRunRepository` o colaborador), escribe `estadistica-corridas.csv`. Identificador agnóstico al formato.

### Success Criteria

- [x] **SC-US2-001**: al disparar la estadística desde la pantalla, `estadistica-corridas.csv` contiene una fila por corrida cuyos `accuracy_bruta` / `accuracy_efectiva` coinciden con el `summary` del detalle.
- [x] **SC-US2-002**: una corrida con todos los casos Indeterminado produce `accuracy_efectiva = null` y `accuracy_bruta = 0.0`, sin error.
- [x] **SC-US2-003**: verificación funcional en la app real — ejecuto un batch, genero la estadística a pedido y abro el CSV resultante.
- [x] **SC-US2-004**: la fila `TOTAL` del CSV coincide con la suma manual de casos y con el accuracy global calculado sobre todos los `TestResult`.

### Assumptions

- Las métricas de `docs/PRODUCT.md` son el SSOT; esta historia implementa el accuracy global (bruta/efectiva), dejando matriz/por-clase a SPEC-008.
- `estadistica-casos.csv` ya lo genera SPEC-005; esta historia sólo agrega `estadistica-corridas.csv`.

### Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-US2-001 | métodos `accuracy_bruta` / `accuracy_efectiva` en `SuiteResult` + tests de cómputo |
| FR-US2-002, SC-US2-002 | test de denominador cero (todos Indeterminado) |
| FR-US2-003, SC-US2-001 | control en `src/dashboard/app.py` + test del escritor de `estadistica-corridas.csv`, verificado contra el `summary` del detalle |
| FR-US2-004 | test de idempotencia: regenerar dos veces produce el mismo archivo, sin duplicados |
| FR-US2-005, SC-US2-004 | `aggregate_runs` en `domain/` + test de la fila TOTAL contra la suma manual + métricas en el dashboard |
| FR-US2-006 | garantía estructural: `FileRunRepository.regenerate_run_stats` opera sobre `runs/detail/` y no recibe el cliente del agente (tests en `test_file_run_repository.py`) |
| FR-US2-007 | `tools/check_naming.py` |
| SC-US2-003 | verificación funcional en la app real |

### Fuera de alcance

- Matriz de confusión, accuracy por clase, % sin clasificación como vista → [[SPEC-008-suite-metrics]].
- Comparación histórica entre runs / tendencias (este CSV habilita el insumo; la visualización comparada es posterior).

---

## User Story 3 — Parada manual de la corrida batch (Priority: P3)

Como usuario quiero **frenar una corrida batch en curso y quedarme con los resultados de los casos ya completados** (sin el caso en vuelo ni los pendientes), tanto en el runner headless como en el dashboard, para no perder el trabajo hecho cuando una corrida larga se tuerce o ya vi lo que necesitaba.

**Why this priority:** la suite ya es usable sin esto (User Story 1); es una mejora de operación para corridas largas. P3 porque no cambia el formato del run ni las métricas: reusa la finalización ya existente sobre un subconjunto de casos.

**Independent Test:** lanzo una corrida de N casos, la freno tras K completados (Ctrl+C en headless / botón "Frenar" en el dashboard) → se persiste **un** run con exactamente K `TestResult` y las métricas se computan sobre esos K. Verificable sin ejecutar los N casos.

### Acceptance Scenarios

1. **Given** una corrida headless en curso, **When** envío SIGINT (Ctrl+C), **Then** el caso en vuelo se descarta (no produce resultado), los pendientes no se lanzan, y la corrida se cierra y persiste con los casos completados.
2. **Given** una corrida en el dashboard en curso, **When** presiono "Frenar", **Then** no se lanzan más casos y la corrida se cierra y persiste con los casos completados hasta ese momento; el detalle indica que fue una parada manual.
3. **Given** una parada manual con K de N casos completados, **When** se persiste, **Then** el run contiene exactamente K `TestResult` y las métricas se computan sobre esos K (igual que una corrida de longitud K).
4. **Given** una parada manual sin ningún caso completado, **When** freno, **Then** el sistema no persiste un run vacío y lo informa.

**Edge Cases:**

- MUST: La corrida parcial es un `SuiteResult` válido de longitud K, indistinguible en formato de una corrida de K casos (round-trip de persistencia intacto).
- **Diferencia de granularidad documentada (esperada, no un defecto):** en headless el caso en vuelo se **aborta** (Ctrl+C es asincrónico y corta el `wait_for_completion`); en el dashboard el caso en curso al momento del click **termina y se incluye**, y se frena antes del siguiente (el framework de UI no interrumpe un caso en curso). En ambos, los casos que no completaron y los pendientes quedan fuera.

### Functional Requirements

- **FR-US3-001**: MUST: El runner headless captura SIGINT (Ctrl+C) durante la ejecución batch; el caso en vuelo se descarta sin resultado, los pendientes no se lanzan, y `run_batch` devuelve los `TestResult` acumulados.
- **FR-US3-002**: MUST: Tras una parada, el entrypoint headless construye y persiste el `SuiteResult` con los casos completados (la misma ruta que una corrida normal) e informa por consola cuántos de los N solicitados se completaron.
- **FR-US3-003**: MUST: El dashboard ejecuta el batch de forma **interrumpible** (un caso a la vez, cediendo el control a la interfaz entre casos) y expone un control "Frenar" que cierra la corrida con los casos completados.
- **FR-US3-004**: MUST: La finalización (armar `SuiteResult` + persistir) es **idéntica** venga de una corrida completa o de una parada manual; la corrida parcial es un `SuiteResult` de longitud K sin campos especiales que la distingan en el detalle persistido.
- **FR-US3-005**: MUST: Una parada sin casos completados **no** persiste un run vacío y se informa al usuario.
- **FR-US3-006**: MUST: invariante [[SPEC-000-naming]] — ningún identificador nombra el framework de UI ni el mecanismo de señal del SO.

### Key Entities

- **run_batch (runner)**: corta limpio ante `KeyboardInterrupt`, devolviendo los resultados acumulados (parada cooperativa por descarte del caso en vuelo).
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
| FR-US3-001, SC-US3-001 | `except KeyboardInterrupt: break` en `run_batch` + test con interrupción simulada (K resultados, caso en vuelo descartado) |
| FR-US3-002 | rama de corrida parcial en `main` (mensaje + persistencia) + test de `build_suite` parcial |
| FR-US3-003 | ejecución por casos interrumpible + botón "Frenar" en `src/dashboard/app.py` |
| FR-US3-004, SC-US3-002 | finalización compartida (`SuiteResult.create` + `FileRunRepository.save`) + test de round-trip del run parcial |
| FR-US3-005 | guarda de "sin casos completados" en `main` (headless) y en `_finalize_batch` (dashboard) |
| FR-US3-006 | `tools/check_naming.py` |
| SC-US3-003 | verificación funcional en la app real |

### Fuera de alcance

- Reanudar (resume) una corrida frenada desde donde quedó: acá solo se cierra con lo hecho.
- Interrumpir un caso individual en curso en el dashboard (el framework de UI no lo permite sin threads; se acepta que el caso actual termina).

---

## Historial

- **2026-05-25** — Spec creada en formato híbrido. Absorbe el viejo SPEC-004-batch-input + la parte de ejecución del viejo SPEC-005-runner; métricas avanzadas (matriz, por-clase) separadas a SPEC-008.
- **2026-05-26** — Añadida User Story 2 (estadística de corridas a pedido); `estadistica-corridas.csv` trasladado desde SPEC-005 porque el accuracy agregado sólo tiene sentido con N casos. Indeterminado en accuracy → dos columnas: `accuracy_bruta` (denominador = total) y `accuracy_efectiva` (denominador = total − indeterminado, `null` si es cero).
- **2026-05-26** — Resueltos los 4 `[NEEDS CLARIFICATION]` con el usuario: filas inválidas se reportan sin abortar; runner headless `python -m src.runner`; formato batch = CSV plano con separador autodetectado y columnas = nombres planos de `TestCase` (referencia de schema `intake_clasificacion.csv`); regeneración completa e idempotente del CSV de corridas. Evaluación Fast Gate por pregunta → deuda fuera de alcance.
- **2026-05-26** — Implementada y cerrada (`draft` → `active`). Agregados acordados durante la implementación: progreso en vivo por caso (headless + dashboard), respuesta cruda por caso, separador `;` en los CSV, detalle batch `run-<ts>.json`, fila `TOTAL` vía `aggregate_runs`. Pipeline VERDE; headless y dashboard verificados en la app real.
- **2026-05-27** — Migrada al **estándar multi-HU** (`docs/SPEC-FORMAT.md`): cada HU encapsulada con sus secciones y FR/SC prefijados por historia. Renumeración sin cambio de comportamiento (mapeo completo FR-viejo→FR-USn en el commit de la migración; las entradas previas del historial se reescribieron después sin la numeración vieja).
- **2026-06-01** — Añadida **User Story 3 — Parada manual** (P3): headless corta ante Ctrl+C descartando el caso en vuelo; dashboard interrumpible por casos + botón "Frenar"; finalización compartida. Diferencia de granularidad headless/dashboard documentada como deliberada (Edge Cases).
- **2026-06-07** — Por [ADR-005](../docs/ARCHITECTURE.md) la orquestación (`run_one`, `run_batch`, `build_suite`, `execution_failure`) se movió a `src/application/run_suite.py`; `src/runner` queda como entrypoint headless y composition root (FR-US1-006 sin cambio de comportamiento). Las menciones a `run_batch` en los FR se leen como "el use-case en `application/`". Implementado.
- **2026-06-07** — Pase de consistencia spec↔código (`/analyze`): SC-US3-003 marcado tras verificación funcional; mapping de FR-US2-006 hecho veraz (garantía estructural en vez de test inexistente). Deuda: US1 sin SC funcional propio para FR-US1-008/009; FR-US2-006 reforzable con test-espía.
- **2026-07-05** — Reescritura editorial al formato compacto (convenciones de `docs/SPEC-FORMAT.md`): notas separadas de reglas en los FR, coverage agrupado, historial podado y ordenado cronológicamente. **Sin cambio normativo**: IDs de FR/SC y su semántica intactos.
