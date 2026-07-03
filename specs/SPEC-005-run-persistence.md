# SPEC-005-run-persistence — Persistencia y revisión del resultado de una ejecución

**Estado:** active
**Iter:** 5
**Formato:** Híbrido
**Depende de:** [[SPEC-003-classification-evaluator]], [[SPEC-002-agent-client]]
**Relacionada con:** [[SPEC-006-batch-suite]], [[SPEC-008-suite-metrics]], [[SPEC-010-batch-trace]], [[SPEC-013-client-adapter-selection]]

## User Story (Priority: P1)

Como usuario quiero que el resultado de evaluar un caso **quede guardado**, no solo mostrado en pantalla, para poder revisarlo después y comparar entre ejecuciones.

**Why this priority:** sin persistencia cada ejecución se pierde. Es el cimiento sobre el que se apoyan batch (SPEC-006) y métricas (SPEC-008). Se resuelve en **modo unitario** (un caso) antes de escalar a lote, para fijar el esquema de `runs/` con el caso más simple.

**Independent Test:** ejecuto un caso → el resultado se escribe en `runs/` con esquema estructurado → puedo volver a abrirlo y ver el veredicto sin re-ejecutar. Verificable con un solo caso, sin batch ni métricas.

## Acceptance Scenarios

1. **Given** un caso evaluado (`TestResult` de SPEC-003), **When** termina la ejecución, **Then** el detalle se persiste en `runs/detail/run-YYYYMMDDTHHMMSS-<token>-<case_id>.json` (patrón de ADR-004) y se apendea una fila a `runs/stats/estadistica-casos.csv`.
2. **Given** un run persistido, **When** lo abro/listo, **Then** veo veredicto (pass/fail/indeterminado), esperado vs. detectado, respuesta cruda, `conversation_id`, `agent_id` y timestamp.
3. **Given** un fallo de escritura (permisos/disco), **When** intento persistir, **Then** la ejecución reporta el error explícitamente sin perder silenciosamente el resultado en pantalla.
4. **Given** el archivo `estadistica-casos.csv` ya existe con filas previas, **When** persisto una nueva corrida, **Then** se apendea una fila sin reescribir las anteriores ni duplicar el encabezado.

### Edge Cases

- MUST: El resultado **Indeterminado** (sin clasificación extraíble) se persiste igual, con `verdict = "indeterminado"` y `extracted_classification = null`.
- MUST: Si `runs/detail/` o `runs/stats/` no existen, el sistema los crea antes de escribir.

## Functional Requirements

- **FR-001**: MUST: El sistema persiste el detalle de cada corrida como un archivo en `runs/detail/`. En modo unitario (1 caso) el nombre lleva el sufijo del caso: `run-YYYYMMDDTHHMMSS-<token>-<case_id>.json`; en batch (SPEC-006, N casos) el archivo es `run-YYYYMMDDTHHMMSS-<token>.json` sin sufijo de caso (ADR-004). El `<token>` es un sufijo único corto que garantiza que dos corridas terminadas en el mismo segundo no compartan `run_id` ni nombre de archivo.
- **FR-002**: MUST: El detalle persistido contiene, a nivel corrida, `run_id`, `timestamp`, `agent_id` y `endpoint_url` (URL efectiva del endpoint/agente bajo test, requisito de [[SPEC-013-client-adapter-selection]] User Story 2; `""` por defecto para corridas previas a esa User Story, tolerado en `from_dict()` sin romper el round-trip); y por caso: `case_id`, esperado, clasificación detectada, veredicto, respuesta cruda y `conversation_id`. Incluye un bloque `summary` con `total`, `pass`, `fail`, `indeterminado`.
- **FR-003**: MUST: El sistema apendea una fila por caso a `runs/stats/estadistica-casos.csv` (separador `;`) con columnas `run_id`, `timestamp`, `case_id`, `expected`, `extracted_classification`, `verdict`. Sin columnas de accuracy (a nivel caso el accuracy es redundante con el veredicto).
- **FR-004**: MUST: El modelo de la corrida vive en `domain/` (`SuiteResult`), conteniendo uno o más `TestResult` y exponiendo los agregados del bloque `summary`. En modo unitario, una corrida envuelve **un** `TestResult`.
- **FR-005**: MUST: El dominio define un puerto de persistencia de runs en `domain/ports.py`; la escritura/lectura concreta de archivos vive en `adapters/` (`FileRunRepository`). El dominio no importa el adapter.
- **FR-006**: MUST: Ningún identificador de código nombra el formato de serialización (`json`, `csv`) ni el framework de UI (SPEC-000-naming). El repositorio se llama `RunRepository` / `FileRunRepository`.
- **FR-007**: MUST: El dashboard permite visualizar un run persistido (al menos el más reciente) sin re-ejecutar el caso.
- **FR-008**: MUST: Un fallo de I/O al persistir se propaga como error explícito (`RunPersistenceError`) al composition root que invoca la persistencia (`dashboard`, `runner`); no se traga silenciosamente. La persistencia se orquesta en el composition root, no en `application/` (que orquesta sólo la ejecución y permanece libre de I/O de disco).

## Key Entities

- **TestResult** (existente, SPEC-003): unidad de resultado por caso. Esta spec NO cambia su shape; sí agrega `verdict` a `to_dict()` (hoy es solo `@property` y no se serializa).
- **SuiteResult** (nuevo, `domain/`): agregado de una corrida — `run_id`, `timestamp`, `agent_id`, `endpoint_url` (default `""`, ver FR-002 y [[SPEC-013-client-adapter-selection]] User Story 2), lista de `TestResult` y `summary` (totales por veredicto). En unitario, la lista tiene longitud 1.
- **Puerto de persistencia de runs** (nuevo, `domain/ports.py`): `Protocol` con `save(run) -> path/id` y `load(run_id) -> SuiteResult`.

## Success Criteria

- [x] **SC-001**: tras ejecutar un caso, existe un archivo en `runs/detail/` que reconstruye el resultado sin pérdida de información (round-trip save→load).
- [x] **SC-002**: tras ejecutar un caso, `runs/stats/estadistica-casos.csv` contiene una fila nueva con el veredicto correcto; ejecutar otro caso apendea sin reescribir el encabezado.
- [x] **SC-003**: un run persistido se vuelve a visualizar en el dashboard sin llamar al agente.
- [x] **SC-004**: 0% de ejecuciones que muestran resultado en pantalla pero no quedan persistidas, salvo error de escritura explícitamente reportado.
- [x] **SC-005**: verificación funcional en la app real — ejecuto un caso, cierro y reabro la vista, y el resultado sigue disponible desde disco.

## Assumptions

- `runs/` ya existe y está gitignored (solo `.gitkeep` versionado), consistente con la política de datos (Constitución IV).
- El esquema de detalle y de `estadistica-casos.csv` definidos aquí los reusa el modo batch (SPEC-006) extendido a N casos sin cambios de fondo.
- `estadistica-corridas.csv` (con accuracy) NO se genera en esta spec — se difiere a SPEC-006, donde una corrida agrega N casos y el accuracy tiene sentido.

## Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-001, FR-002 | `adapters/` (`FileRunRepository`) + test round-trip (save→load) del detalle JSON |
| FR-003 | `adapters/` (append a `estadistica-casos.csv`) + test de append (encabezado único, filas acumuladas) |
| FR-002 (campo `endpoint_url`) | `tests/unit/test_result.py` (round-trip `SuiteResult` con y sin `endpoint_url`, default retrocompatible) — requisito originado en [[SPEC-013-client-adapter-selection]] User Story 2 |
| FR-004 | `domain/` `SuiteResult` + test de construcción y de `summary` |
| FR-005 | puerto en `domain/ports.py` + `import-linter` (domain no importa adapters) |
| FR-006 | `tools/check_naming.py` + revisión de identificadores del módulo de persistencia |
| FR-007 | integración en `src/dashboard/app.py` + verificación funcional |
| FR-008 | test de error de I/O simulado en el adapter |
| SC-001 | test round-trip con un `TestResult` real (incl. caso Indeterminado) |
| SC-002 | test de append sobre CSV preexistente |
| SC-003 | integración en `src/dashboard/app.py` (cubierto por FR-007) |
| SC-004 | test de escritura + manejo explícito de error (cubierto por FR-008) |
| SC-005 | verificación funcional en la app real |

## Fuera de alcance

- Ejecución de **múltiples** casos y orquestación batch → [[SPEC-006-batch-suite]].
- `estadistica-corridas.csv` y el cálculo de `accuracy_bruta` / `accuracy_efectiva` → [[SPEC-006-batch-suite]].
- Matriz de confusión / accuracy por clase → [[SPEC-008-suite-metrics]].
- Comparación histórica entre runs (solo se sientan las bases del esquema).
- Persistencia de la traza del agente por caso → [[SPEC-010-batch-trace]] US2 (extensión de este esquema).

## Historial

- **2026-05-25** — Spec creada en formato híbrido. Re-corte: el viejo SPEC-005-runner se reparte entre esta spec (persistencia, en modo unitario) y SPEC-006 (ejecución batch). Esquema de run y agrupación marcados `[NEEDS CLARIFICATION]`.
- **2026-05-26** — Resueltos los `[NEEDS CLARIFICATION]` con el usuario: (a) un archivo de detalle por corrida en `runs/detail/`, nombrado `run-<ts>-<case_id>.json`; (b) estadística tabular separada en `runs/stats/`, con `estadistica-casos.csv` (una fila por caso × corrida, sin accuracy) generada aquí; (c) `estadistica-corridas.csv` con accuracy se difiere a SPEC-006 porque a nivel caso unitario el accuracy es redundante con el veredicto. ADR-004 actualizado con la nueva estructura de carpetas.
- **2026-05-26** — Implementada y cerrada (`draft` → `active`). `SuiteResult` + factory `create()` en `domain/`; puerto `RunRepository`; adapter `FileRunRepository` (detalle JSON + append a `estadistica-casos.csv` + `load`/`load_latest` + `RunPersistenceError`); integración en el dashboard (persistencia tras evaluar + vista del último run desde disco). Pipeline local VERDE 8/8; SC-005 verificado en la app real por el usuario.
- **2026-05-26** — Ajuste de comportamiento (spec viva, durante implementación de SPEC-006): (a) `estadistica-casos.csv` pasa a separador `;` (coherencia con el archivo batch y Excel en español); (b) el nombre del detalle lleva el sufijo `-<case_id>` sólo en modo unitario; en batch es `run-<ts>.json` sin sufijo, porque la corrida representa N casos. ADR-004 y `load()` (acepta ambos patrones) actualizados.
- **2026-06-07** — Por [ADR-005](../docs/ARCHITECTURE.md) el use-case unitario `run_one` se movió a `src/application/run_suite.py` (antes en `src/runner`), junto con `run_batch`/`build_suite`; los composition roots (`runner`, `dashboard`) lo importan desde ahí. La ejecución la orquesta `application/`; la **persistencia** (`FileRunRepository.save`) se invoca en los composition roots (`dashboard/app.py`, `runner.py`), que es donde se captura `RunPersistenceError` (FR-008). La persistencia y el esquema de run no cambian. Implementado.
- **2026-06-07** — Desambiguado FR-008 (hallazgo `/analyze` A2): "la capa que orquesta" se precisa como el **composition root** que invoca la persistencia (`dashboard`, `runner`), donde se captura `RunPersistenceError`. `application/` orquesta sólo la ejecución y permanece libre de I/O de disco. Sin cambios de código (el comportamiento ya era ése); se reconcilia la redacción con la implementación.
- **2026-07-03** — Ampliación de esquema (spec viva) a pedido de [[SPEC-013-client-adapter-selection]] User Story 2: `SuiteResult` y el detalle persistido agregan el campo `endpoint_url` (FR-002, Key Entities) — la URL efectiva del endpoint/agente bajo test, resuelta por `PlatformConfig.effective_endpoint_url`. Default `""`, con retrocompatibilidad garantizada en `from_dict()` para runs previos sin la clave. SPEC-005 sigue siendo el único SSOT del esquema de `SuiteResult`; SPEC-013 sólo consume el campo. **Implementado** el 2026-07-03 (campo `endpoint_url` en `domain/result.py`, round-trip retrocompatible verificado en `test_result.py`).
