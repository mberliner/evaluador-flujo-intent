# SPEC-009-parallel-execution — Ejecución paralela de casos con concurrencia configurable

**Estado:** draft
**Iter:** 9
**Formato:** Híbrido
**Depende de:** [[SPEC-006-batch-suite]], [[SPEC-002-agent-client]], [[SPEC-003-classification-evaluator]]
**Relacionada con:** [[SPEC-008-suite-metrics]], [[SPEC-005-run-persistence]]

**Resumen:** Agrega ejecución paralela de casos con concurrencia configurable (`ConcurrencyLimit`, default 1 = secuencial) sobre el modelo batch de [[SPEC-006-batch-suite]], sin cambiar el esquema de resultados. Dos cortes: **US1** concurrencia en el runner headless con drenaje ante parada manual (P2); **US2** concurrencia en el dashboard reconciliada con el control "Frenar" (P3). En `draft`, pendiente de implementación; habilitarla exige antes resolver la correlación de trazas bajo paralelismo (ver [[SPEC-010-batch-trace]]).

## Clarifications

### Session 2026-06-09

- Q: Con `concurrency=K`, al frenar la corrida batch (parada manual, SPEC-006 US3), ¿qué pasa con los casos ya en vuelo? → A: **Drenar los en vuelo** — se dejan terminar e incluir los hasta-K casos ya despachados; no se lanzan los pendientes (coherente con el dashboard actual, donde el caso en curso termina). Ver FR-US1-009.
- Q: FR-008 pedía exponer `concurrency` en headless y en el dashboard, pero el dashboard ejecuta un caso por tick (`fragment`) para ser interrumpible (SPEC-006 US3). ¿Dónde aplica la concurrencia? → A: **Se separa en dos User Stories** — US1 concurrencia headless (P2, MVP sin conflicto con el stepping de UI) y US2 concurrencia en el dashboard (P3, que encapsula la reconciliación con el modelo cooperativo de SPEC-006 US3). La spec se migra al estándar multi-HU (numeración `FR-USx-NNN`).
- Q: SC-US1-001 decía "tarda significativamente menos" (no binario). ¿Qué criterio medible se usa? → A: **No medir tiempo** — la afirmación de speedup es ruidosa y se elimina como criterio de éxito. SC-US1-001 verifica de forma binaria que se respeta el máximo de K envíos en vuelo (límite de concurrencia). El beneficio de tiempo se valida informalmente, no como SC.

---

## User Story 1 — Concurrencia en ejecución headless (Priority: P2)

Como usuario quiero ejecutar una suite de N casos **desde el runner headless** con un número configurable de envíos simultáneos al agente, para reducir el tiempo total de corrida cuando el agente tolera carga concurrente, sin perder trazabilidad ni determinismo en la evaluación.

**Why this priority:** la ejecución secuencial de un batch grande es el cuello de botella principal de la herramienta una vez que existe el modo batch (SPEC-006). La concurrencia configurable en headless permite calibrar la carga contra el agente sin cambiar el modelo de resultados, y es el corte de mayor valor y menor riesgo: no toca el modelo de interacción de la UI.

**Independent Test:** ejecuto N casos con `concurrency=K` desde `python -m src.runner --concurrency K` → los K primeros se despachan al mismo tiempo → el run resultante tiene N `TestResult` con los mismos veredictos que la ejecución secuencial (determinismo garantizado por Principio III). Verificable sin el dashboard.

### Acceptance Scenarios

1. **Given** una suite de N casos y `concurrency=K`, **When** se ejecuta, **Then** en todo momento hay como máximo K envíos al agente en curso simultáneamente.
2. **Given** `concurrency=1`, **When** se ejecuta, **Then** el comportamiento es idéntico a la ejecución secuencial de SPEC-006 (retrocompatibilidad).
3. **Given** `concurrency=N+1` (más slots que casos), **When** se ejecuta, **Then** el sistema usa como máximo N slots sin error.
4. **Given** un valor inválido de `concurrency` (cero, negativo, no-entero), **When** se intenta ejecutar, **Then** el sistema rechaza la entrada con un mensaje descriptivo antes de iniciar cualquier envío.
5. **Given** que K envíos corren en paralelo y uno falla, **When** se procesa el error, **Then** los demás K−1 envíos continúan y el caso fallido se marca como fallido (coherente con SPEC-006 FR-US1-010).
6. **Given** una suite ejecutada con `concurrency=K`, **When** se persiste el run, **Then** el `SuiteResult` es estructuralmente idéntico al de una ejecución secuencial (mismo esquema, SPEC-005).
7. **Given** una corrida headless con `concurrency=K` y K casos en vuelo, **When** el usuario frena la corrida (SIGINT / Ctrl+C, SPEC-006 US3), **Then** los hasta-K casos en vuelo se drenan y se incluyen, no se despacha ningún pendiente, y la corrida se cierra y persiste con los casos completados.

### Functional Requirements

- **FR-US1-001**: MUST: El coordinador acepta un parámetro entero positivo `concurrency` que fija el número máximo de envíos simultáneos al agente.
- **FR-US1-002**: MUST: El coordinador garantiza que en ningún momento hay más de `concurrency` llamadas al agente en vuelo.
- **FR-US1-003**: MUST: Con `concurrency=1` el comportamiento es semánticamente equivalente al secuencial de SPEC-006 (mismos veredictos en el mismo `SuiteResult`, sin alteración).
- **FR-US1-004**: MUST: Un valor `concurrency <= 0` o no-entero produce un error de validación antes de cualquier envío; el sistema no comienza la ejecución.
- **FR-US1-005**: MUST: El mecanismo de paralelismo vive en la **capa de aplicación** (`src/application/`, donde reside la orquestación `run_batch` desde ADR-005); `src/domain/` permanece sin conocimiento de concurrencia. El mecanismo concreto (asyncio, threadpool, etc.) queda a criterio de la implementación y no aparece en ningún identificador (Principio I).
- **FR-US1-006**: MUST: El fallo de un caso individual no interrumpe los demás casos en vuelo ni los pendientes (coherente con SPEC-006 FR-US1-010).
- **FR-US1-007**: MUST: El `SuiteResult` producido (SPEC-005) no depende del orden de llegada de las respuestas; los resultados se asignan al `TestCase` correspondiente por identidad de caso, no por posición en la cola.
- **FR-US1-008**: MUST: El runner headless expone `concurrency` por argumento de línea de comandos (`python -m src.runner --concurrency K`).
- **FR-US1-009**: MUST: Ante una parada manual (SPEC-006 US3, SIGINT) con `concurrency=K`, los casos ya despachados **se drenan**: el coordinador espera a que los hasta-K casos en vuelo completen y los incluye, no despacha ningún caso pendiente, y la corrida se cierra y persiste con los casos completados. El `SuiteResult` resultante es coherente con SPEC-006 FR-US3-004 (indistinguible en formato de una corrida de esa longitud).
- **FR-US1-010**: MAY: El sistema registra en los logs de la corrida el valor de `concurrency` usado, para reproducibilidad.
- **FR-US1-011**: MUST: Ausente el argumento `--concurrency`, el `ConcurrencyLimit` por defecto es 1 (ejecución secuencial), de modo que el runner sin el flag reproduce el comportamiento de SPEC-006 (base de la retrocompatibilidad de FR-US1-003).

### Key Entities

- **ConcurrencyLimit**: entero positivo (≥ 1) que representa el máximo de envíos simultáneos. Valor por defecto: 1 (secuencial). Forma parte del contexto de ejecución del runner, no del `TestCase` ni del `TestResult`.
- **Coordinador de ejecución**: componente de la **capa de aplicación** (`src/application/`) responsable de despachar `TestCase` al `RemoteAgentClient` respetando el `ConcurrencyLimit` y recolectar los `TestResult`. No pertenece a `domain/`.

### Success Criteria

- [ ] **SC-US1-001**: una suite ejecutada con `concurrency=K` nunca tiene más de K envíos al agente en vuelo simultáneamente; verificado por test unitario con un stub que registra el máximo de llamadas concurrentes observado (criterio binario: el máximo observado ≤ K). No se mide tiempo de ejecución.
- [ ] **SC-US1-002**: el `SuiteResult` de `concurrency=5` y `concurrency=1` sobre los mismos casos produce los mismos veredictos (determinismo de evaluación — Principio III).
- [ ] **SC-US1-003**: `concurrency=0` y `concurrency=-1` producen error de validación antes de iniciar cualquier envío; verificado por test unitario.
- [ ] **SC-US1-004**: `concurrency=1` en la interfaz headless produce exactamente el mismo `SuiteResult` que SPEC-006 sin el flag; verificado por test de regresión.
- [ ] **SC-US1-005**: una parada manual con K casos en vuelo drena esos K, no lanza pendientes, y persiste un `SuiteResult` que los incluye; verificado por test con SIGINT/`KeyboardInterrupt` simulado.
- [ ] **SC-US1-006**: `check_naming.py` y el pipeline `tools/pipeline_local.sh` pasan en verde sobre el código introducido (lint, mypy, naming, capas, pytest).

### Assumptions

- El `RemoteAgentClient` (SPEC-002) es seguro para invocaciones concurrentes: no mantiene estado compartido mutable entre llamadas. Si esto no es cierto al implementar, se ajusta el adapter antes de este sprint (riesgo de alto impacto: validar la reentrada del adapter primero).
- El agente remoto no impone un límite de concurrencia inferior al que el usuario configure; si lo hace, la gestión de ese error pertenece al adapter (SPEC-002), no a esta spec.
- El `ConcurrencyLimit` aplica a nivel de proceso único (no distribuido).

### Coverage mapping

| Requisito | Cubierto por |
|-----------|-------------|
| FR-US1-001, FR-US1-002, SC-US1-001 | coordinador de ejecución en `src/application/` + test unitario con stub del agente que registra el máximo de llamadas concurrentes observado (máximo ≤ K) |
| FR-US1-003, SC-US1-002 | tests de regresión y determinismo: misma suite, `concurrency=1` vs. secuencial de SPEC-006; mismos casos, distinta concurrencia, mismos veredictos |
| FR-US1-004, SC-US1-003 | test unitario: valores inválidos de `concurrency` → excepción antes de cualquier envío |
| FR-US1-005 | `lint-imports` + inspección de `src/domain/` (sin referencias al coordinador) |
| FR-US1-006 | test de batch con fallo puntual simulado en medio de ejecución concurrente |
| FR-US1-007 | test unitario: respuestas desordenadas → `TestResult` asignados por identidad de caso |
| FR-US1-008 | test de integración headless con `--concurrency K` |
| FR-US1-009, SC-US1-005 | test de parada manual (SIGINT/`KeyboardInterrupt` simulado) con K en vuelo: el coordinador drena los despachados, no lanza pendientes, y el `SuiteResult` contiene los drenados + previos |
| FR-US1-010 | inspección del log de corrida (opcional) |
| FR-US1-011, SC-US1-004 | test del runner: sin `--concurrency`, el `ConcurrencyLimit` resuelto es 1 y el `SuiteResult` coincide con la corrida secuencial de SPEC-006 |
| SC-US1-006 | `tools/check_naming.py` + `tools/pipeline_local.sh` en cierre de iter |

### Fuera de alcance

- Concurrencia en el dashboard → User Story 2.
- Distribución de carga entre múltiples procesos o máquinas.
- Configuración de límites impuesta por el agente remoto (pertenece a [[SPEC-002-agent-client]]).
- Throttling por tiempo (rate-limiting con ventana deslizante).
- Métricas de tiempo de ejecución por caso o histograma de latencias → posible extensión de [[SPEC-008-suite-metrics]].

---

## User Story 2 — Concurrencia en el dashboard (Priority: P3)

Como usuario quiero configurar la concurrencia **desde el dashboard** y que la corrida batch despache hasta K casos en paralelo, manteniendo el control "Frenar" de SPEC-006 US3, para acelerar las corridas interactivas largas sin perder la capacidad de pararlas.

**Why this priority:** P3 porque el valor de destrabar el cuello de botella ya lo entrega US1 (headless); el dashboard es usable sin concurrencia. Además depende de **reconciliar la concurrencia con el modelo cooperativo de SPEC-006 US3**: hoy el dashboard ejecuta un caso por tick (`fragment`) cediendo control entre casos para atender "Frenar". Correr K casos en vuelo exige rediseñar ese stepping sin perder la interrumpibilidad — un riesgo de diseño que conviene aislar de US1.

**Independent Test:** en el dashboard fijo `concurrency=K`, lanzo una corrida batch, observo que hay hasta K casos en vuelo a la vez, y al presionar "Frenar" los K en vuelo se drenan y la corrida se cierra con esos resultados. Verificable en la app real, independiente de la ruta headless.

### Acceptance Scenarios

1. **Given** el dashboard con un batch cargado y `concurrency=K`, **When** ejecuto la corrida, **Then** hay como máximo K casos en vuelo simultáneamente y el progreso se reporta por caso a medida que cada uno completa (coherente con SPEC-006 FR-US1-008).
2. **Given** una corrida en el dashboard con K casos en vuelo, **When** presiono "Frenar", **Then** los K en vuelo se drenan e incluyen, no se despacha ningún pendiente, y la corrida se cierra y persiste con los casos completados (misma semántica de drenaje que FR-US1-009).
3. **Given** `concurrency=1` en el dashboard, **When** ejecuto, **Then** el comportamiento es el stepping secuencial interrumpible actual de SPEC-006 US3 (retrocompatibilidad).

### Functional Requirements

- **FR-US2-001**: MUST: El dashboard expone un control para fijar `concurrency` y lo pasa al coordinador de ejecución de US1, sin duplicar la lógica de límite.
- **FR-US2-002**: MUST: La ejecución batch del dashboard concilia la concurrencia con el control "Frenar" de SPEC-006 US3: corre hasta K casos en vuelo y, al frenar, drena los en vuelo (FR-US1-009) sin despachar pendientes, preservando la interrumpibilidad.
- **FR-US2-003**: MUST: Con `concurrency=1` el dashboard preserva el comportamiento de stepping interrumpible de SPEC-006 US3 (retrocompatibilidad).
- **FR-US2-004**: MUST: invariante [[SPEC-000-naming]] — ningún identificador nombra el framework de UI ni el mecanismo de concurrencia.

### Key Entities

- **ConcurrencyLimit** (de US1): reutilizado; el dashboard solo provee el valor configurado por el operador.
- **Coordinador de ejecución** (de US1): reutilizado tal cual; el dashboard es un composition root que lo invoca, sin reimplementar el límite.

### Success Criteria

- [ ] **SC-US2-001** *(verificación funcional en la app real)*: en el dashboard fijo `concurrency=K`, ejecuto un batch, observo hasta K casos en vuelo, presiono "Frenar" y el run guardado contiene los casos drenados + previos, sin pendientes. Último SC en cerrarse.
- [ ] **SC-US2-002**: `concurrency=1` en el dashboard reproduce el stepping interrumpible de SPEC-006 US3 (verificable con la corrida secuencial actual).

### Assumptions

- El coordinador de US1 es reutilizable desde el dashboard sin cambios (recibe el `ConcurrencyLimit` por parámetro, ADR-005).
- El modelo `fragment` de Streamlit admite un rediseño que despache K casos por tick manteniendo la cesión de control para "Frenar"; si no, se documenta la limitación al implementar.

### Coverage mapping

| Requisito | Cubierto por |
|-----------|-------------|
| FR-US2-001 | control de concurrencia en `src/dashboard/app.py` que pasa el valor al coordinador + test del cableado |
| FR-US2-002, SC-US2-001 | ejecución batch del dashboard con drenaje al frenar + verificación funcional en la app real (último SC en cerrarse) |
| FR-US2-003, SC-US2-002 | test/verificación de `concurrency=1` ≡ stepping interrumpible de SPEC-006 US3 (retrocompatibilidad) |
| FR-US2-004 | `tools/check_naming.py` sobre `src/` |

### Fuera de alcance

- El coordinador de concurrencia en sí (vive en US1, `src/application/`).
- Rediseño general del modelo de ejecución del dashboard más allá de lo necesario para conciliar concurrencia + "Frenar".

---

## Historial

- **2026-05-26** — Spec creada: correr suites grandes con N envíos simultáneos configurables. Agnóstica al mecanismo de concurrencia (Principio I); agrega sólo el parámetro de paralelismo sobre el batch secuencial de SPEC-006.
- **2026-06-09** — Pase de `/analyze` + `/clarify`: decisión de **drenaje** ante parada manual (FR-US1-009); **migración a estándar multi-HU** (US1 headless P2 / US2 dashboard P3, renumeración sin cambio de comportamiento — mapeo en el commit); fix de capa (coordinador en `src/application/`, coherente con ADR-005); SC-US1-001 pasa de speedup no medible a invariante binario "máximo K en vuelo"; se explicita FR-US1-011 (default `concurrency=1`), base de la retrocompatibilidad de FR-US1-003.
- **2026-07-05** — Reescritura editorial al formato compacto (convenciones de `docs/SPEC-FORMAT.md`): Resumen ejecutivo, coverage agrupado, historial podado. **Sin cambio normativo**.
