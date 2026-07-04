# SPEC-008-suite-metrics — Métricas de suite: matriz de confusión y accuracy por clase

**Estado:** active
**Iter:** 8 impl.2026-05-27
**Formato:** Híbrido
**Depende de:** [[SPEC-006-batch-suite]], [[SPEC-005-run-persistence]]
**Relacionada con:** [[SPEC-003-classification-evaluator]], [[SPEC-010-batch-trace]]

## User Story (Priority: P2)

Como analista quiero ver, sobre una corrida batch, la **matriz de confusión** (expected × predicted sobre la paleta canónica de 5 clases, más una columna para casos sin clasificación extraíble), el **accuracy por clase** y el **% de casos sin clasificación extraíble**, para identificar dónde el agente confunde y ajustar prompt o dataset. (Tu "matriz y otras".)

**Why this priority:** es el valor analítico final del producto (`docs/PRODUCT.md` caso de uso 3: "análisis de debilidades"). Llega después de tener ejecución batch y resultados persistidos (SPEC-006), sobre los que opera sin re-ejecutar.

**Independent Test:** sobre un run batch existente, el sistema computa y muestra la matriz + accuracy por clase + % sin clasificación, coincidiendo con el cálculo manual. Verificable a partir de un run persistido, sin llamar al agente.

## Acceptance Scenarios

1. **Given** un run con N `TestResult`, **When** computo las métricas, **Then** obtengo una matriz cuyas **filas** son las 5 clases de `PALETA_CLASIFICACION` (`{Verde, Amarillo, Rojo, Negro, Rechazado}`) y cuyas **columnas** son esas 5 clases más una columna `Sin clasificación`, con conteos expected × predicted.
2. **Given** el mismo run, **When** computo accuracy por clase, **Then** obtengo, por cada color esperado, `aciertos_de_la_clase / casos_de_la_clase`.
3. **Given** casos Indeterminados (sin clasificación extraíble, `predicted = None`), **When** computo métricas, **Then** caen en la columna `Sin clasificación` de la matriz (cada caso ocupa exactamente una celda; la suma de la matriz es el total) **y** además se reportan como `% sin clasificación` aparte. *(Decisión 2026-05-27: los Indeterminados entran como columna extra, no se excluyen de la matriz.)*
4. **Given** un run, **When** lo visualizo, **Then** la matriz y los accuracies se renderizan en el dashboard de suite.

### Edge Cases

- MUST: La clase esperada con 0 casos en el run produce accuracy N/A, no división por cero.
- MUST: El run de un solo caso computa métricas sin error (matriz mayormente vacía).
- MUST: Una corrida persistida corrupta/ilegible en el agregado se omite y se reporta aparte, sin abortar el cómputo del resto (FR-009, alineado con [[SPEC-006-batch-suite]]).

## Clarifications

### Session 2026-06-07

- Q: PRODUCT.md §Métricas lista «Accuracy efectiva» = `pass/(total−indeterminado)`, pero `SuiteMetrics` no la incluye. ¿Hueco o fuera de alcance? → A: Fuera de alcance de `SuiteMetrics`. La accuracy efectiva pertenece a la estadística de corridas ([[SPEC-006-batch-suite]], atributo `SuiteResult.accuracy_efectiva`) y el dashboard la presenta desde ahí (bloque «Todas las corridas», `overall.accuracy_efectiva`), no desde `SuiteMetrics`. SPEC-008 cubre matriz + accuracy bruta (global y por clase) + % sin clasificación.
- Q: ¿Qué hace el agregado (FR-007/FR-008) ante una corrida persistida corrupta/ilegible? → A: Conducta resiliente consistente con [[SPEC-006-batch-suite]] (entradas inválidas se reportan aparte y el resto continúa, no se aborta el conjunto): se **omite** la corrida ilegible, se computa el agregado con las legibles y se **reporta cuáles/cuántas** se omitieron. (Ver FR-009; el `load_all()` actual aborta —fail-fast— y debe reconciliarse.)

## Functional Requirements

- **FR-001**: MUST: El cómputo de métricas (matriz, accuracy global y por clase, % sin clasificación) son **funciones puras en `domain/`** sobre un `SuiteResult`, sin I/O.
- **FR-002**: MUST: Las filas de la matriz son la paleta canónica completa (`PALETA_CLASIFICACION` de SPEC-001/003b: 5 clases, incluida `Rechazado`), reutilizando esa constante, no una lista nueva. Las columnas son esa misma paleta más una columna `Sin clasificación` para `predicted = None`.
- **FR-003**: MUST: Las definiciones de métricas coinciden con `docs/PRODUCT.md` §Métricas (SSOT). Si esta spec necesita una métrica no listada allí, MUST: la métrica se propone primero en `PRODUCT.md`.
- **FR-004**: MUST: El dashboard renderiza la matriz y los accuracies a partir de los agregados de `domain/`, sin recalcular en la capa de UI.
- **FR-005**: MUST: El accuracy por clase maneja clases sin casos como N/A.
- **FR-006**: MUST: Las métricas se pueden ver sobre **una corrida persistida cualquiera** (no solo la recién ejecutada): el dashboard ofrece un selector de `run_id` entre las corridas guardadas (`runs/detail/`) y muestra la matriz de la elegida, sin invocar al agente. Por defecto, la más reciente.
- **FR-007**: MUST: Existe una **matriz general agregada** sobre todos los casos de todas las corridas persistidas, computada por una función pura en `domain/` (`aggregate_suite_metrics`) que trata los `TestResult` de N corridas como una sola población y toma su accuracy global de `aggregate_runs` (mismo cómputo que la fila `TOTAL` de `estadistica-corridas.csv`, sin duplicar la fórmula). El dashboard la expone como una opción («Todas las corridas») del **mismo selector** de FR-006, renderizándola con el mismo bloque que la matriz de una corrida.
- **FR-008**: MUST: El runner headless (`python -m src.runner`) ofrece un **modo exclusivo** (`--estadistica`) que, sin ejecutar la suite ni invocar al agente, computa la matriz general (FR-007) sobre las corridas guardadas en `--out` y la entrega en **dos formatos a la vez**: (a) **a pantalla en Markdown** (tablas alineadas legibles a simple vista: título + matriz + resumen de estadística + accuracy por clase), vía `format_metrics_markdown`; (b) **a archivo CSV** delimitado por `;` en `runs/stats/estadistica-matriz.csv`, vía `format_metrics_report` + `save_metrics_report` (repositorio, capa `adapters`). Ambos formateadores son funciones puras. La salida a pantalla evita caracteres fuera de cp1252 por compatibilidad de consola en Windows. Ningún identificador nombra el formato de serialización (SPEC-000-naming).

- **FR-010**: MUST: El control del dashboard que regenera `estadistica-corridas.csv` ([[SPEC-006-batch-suite]] FR-US2-003) también actualiza `estadistica-matriz.csv` en la misma operación, invocando `save_metrics_report` sobre el agregado de todas las corridas. Ambos archivos quedan sincronizados tras cada disparo del control.

- **FR-009**: MUST: El agregado (FR-007/FR-008) sobre las corridas persistidas es **resiliente a una corrida corrupta/ilegible**, consistente con el invariante de [[SPEC-006-batch-suite]] (una entrada inválida no aborta el conjunto: se reporta aparte y el resto continúa). La corrida ilegible se **omite** del cómputo, el agregado se calcula con las legibles, y se **informa** cuáles/cuántas se omitieron (en pantalla para `--estadistica`, en el dashboard para el bloque «Todas las corridas»). *(Estado: el `FileRunRepository.load_all()` actual aborta con `RunPersistenceError` ante el primer archivo ilegible —fail-fast—; este FR formaliza la conducta objetivo y queda como deuda de reconciliación con el código.)*

## Key Entities

- **SuiteResult** (de SPEC-005/006): entrada de las métricas de una corrida.
- **SuiteMetrics** (nuevo, `domain/metrics.py`): matriz de confusión, accuracy global (= bruta), accuracy por clase, % sin clasificación. Estructura de salida pura, serializable (`to_dict`). La producen `compute_suite_metrics(run)` (una corrida) y `aggregate_suite_metrics(runs)` (agregado sobre varias). **No incluye `accuracy_efectiva`**: esa métrica pertenece a `SuiteResult` ([[SPEC-006-batch-suite]]) y el dashboard la renderiza desde ahí (ver Clarifications 2026-06-07).
- **aggregate_suite_metrics** (nuevo, `domain/metrics.py`): matriz general sobre todos los casos de N corridas; reutiliza `aggregate_runs` para el accuracy global.
- **PALETA_CLASIFICACION** (existente, SPEC-001/003b): eje de la matriz; se reutiliza completa (5 clases).

## Success Criteria

- [x] **SC-001**: la matriz y los accuracies coinciden con el cálculo manual sobre un run de fixture conocido.
- [x] **SC-002**: el % de casos sin clasificación extraíble se reporta y es comparable contra el objetivo de `docs/PRODUCT.md` (< 5%).
- [x] **SC-003**: las métricas se computan sobre un run persistido sin volver a invocar al agente.

## Assumptions

- Los runs persistidos (SPEC-005/006) contienen toda la información necesaria (esperado + detectado por caso) para computar las métricas offline.
- La paleta canónica (5 clases: Verde, Amarillo, Rojo, Negro, Rechazado) es estable (ADR-003: una sola respuesta válida por caso).

## Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-001, FR-002, FR-005 | `domain/metrics.py` + tests con runs de fixture (incl. clase vacía, run unitario) |
| FR-003 | revisión cruzada contra `docs/PRODUCT.md` §Métricas |
| FR-004, FR-006 | render en `src/dashboard/` (matriz post-corrida + selector de run guardado) + verificación funcional visual confirmada por el usuario (2026-05-28) |
| FR-007 | `aggregate_suite_metrics` en `domain/metrics.py` + test de agregado sobre varias corridas + render general en el dashboard + verificación visual «Todas las corridas» confirmada por el usuario (2026-05-28) |
| FR-008 | `format_metrics_report` (puro) + `--estadistica` en `src/runner.py` + `save_metrics_report` en `adapters` + tests (formato, modo a pantalla/CSV, sin corridas, --in obligatorio) + verificación funcional CLI |
| FR-010 | **pendiente**: llamada a `save_metrics_report` desde `_render_run_stats_control` en `src/dashboard/app.py` (gap identificado; implementación diferida al análisis de ubicación de `format_metrics_report`) |
| FR-009 | **pendiente**: reconciliar `FileRunRepository.load_all()` (hoy fail-fast) hacia omitir+reportar la corrida ilegible + test de agregado con una corrida corrupta entre legibles |
| SC-001 | test con run de fixture de conteo conocido (cubierto por FR-001/FR-002) |
| SC-002 | test con run de fixture que incluye casos Indeterminados (cubierto por FR-001) |
| SC-003 | test que carga un run persistido (SPEC-005) y computa métricas sin llamar al agente |

## Fuera de alcance

- Comparación de **tendencias** entre runs (evolución temporal, deltas run-a-run). La matriz **general agregada** (FR-007) sí está incluida, pero es una sola foto sobre la unión de todos los casos, no una comparación entre corridas.
- Recomendación automática de ajustes de prompt (solo se expone la matriz para análisis humano).
- Traza del agente por caso (incluida en batch) → [[SPEC-010-batch-trace]].
- **Accuracy efectiva** (`pass/(total−indeterminado)`): es atributo de `SuiteResult` y se gobierna en [[SPEC-006-batch-suite]]; el dashboard la muestra desde ahí. No forma parte de `SuiteMetrics` de esta spec.

## Historial

- **2026-05-25** — Spec creada en formato híbrido con ID nuevo (SPEC-008): el viejo SPEC-006-dashboard-suite se dividió — la ejecución batch quedó en SPEC-006-batch-suite y las métricas analíticas aquí, para mantener slices independientemente testeables. `[NEEDS CLARIFICATION]` sobre el tratamiento de Indeterminados en la matriz, a resolver al implementar (decisión del usuario, 2026-05-25).
- **2026-06-07** — `/clarify`: resueltas 2 ambigüedades de impacto. (1) **Accuracy efectiva** → confirmada fuera de alcance de `SuiteMetrics`; pertenece a `SuiteResult`/[[SPEC-006-batch-suite]] y el dashboard la renderiza desde ahí (sin cambio de código). (2) **Corrida corrupta en el agregado** → conducta objetivo = omitir+reportar (resiliente, alineada con SPEC-006), formalizada en **FR-009 nuevo**; el `load_all()` actual es fail-fast y queda como deuda de reconciliación (FR-009 en estado pendiente).
- **2026-05-27** — Implementada y cerrada (`draft` → `active`). Resueltas dos decisiones con el usuario: (1) **ejes de la matriz** → se usa `PALETA_CLASIFICACION` completa (5 clases, incluida `Rechazado` que SPEC-003b agregó), reconciliando la contradicción "4×4" de la versión draft contra FR-002 (reutilizar la constante, no derivar una sublista); (2) **Indeterminados** (resuelve el `[NEEDS CLARIFICATION]`) → caen en una columna `Sin clasificación` de la matriz (cada caso ocupa una celda, la suma de la matriz es el total) **y** además se reportan como `% sin clasificación` aparte. Implementación: `compute_suite_metrics` + `SuiteMetrics` en `src/domain/metrics.py` (puro, serializable), render en `_render_suite_metrics` de `src/dashboard/app.py` (solo lee agregados del dominio), 12 tests unitarios en `tests/unit/test_metrics.py`. `accuracy_global` delega en `SuiteResult.accuracy_bruta` para no duplicar la fórmula de `docs/PRODUCT.md`.
