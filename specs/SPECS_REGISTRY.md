# SPECS_REGISTRY — Single Source of Truth de specs

Este archivo lista todas las specs vigentes del proyecto. Cada spec describe una capacidad concreta del sistema, sus criterios de aceptación y su estado. Toda implementación debe poder mapearse a una spec aquí registrada.

> Las specs son **vivas**: se actualizan tras cada iteración (spec → ejecución → observación → ajuste).

## Convenciones

- Estado: `draft` | `active` | `superseded` | `archived` | `notas` (referencia fuera de secuencia).
- Cada spec tiene un ID estable (`SPEC-NNN-slug`) y un archivo en este directorio.
- Una spec puede tener `Depende de:` y `Relacionada con:` (links `[[id]]`).
- Cierre de iteración → bloque `[SDD-Check]` en el commit citando specs leídas, includes/excludes verificados, SSOTs afectados.
- **Formato de spec**: SPEC-000..003 usan el formato propio ("casero"). **Desde SPEC-004 las specs usan formato híbrido** (anatomía GitHub Spec Kit: User Story con prioridad + `FR-NNN MUST` + `SC-NNN` medibles + Given/When/Then + coverage mapping). El corte de método se acordó el 2026-05-25: hasta SPEC-003 casero (terminado), SPEC-004+ híbrido. Ver template de referencia: [docs/SPEC-FORMAT.md](../docs/SPEC-FORMAT.md).

## Specs vigentes

| ID | Título | Estado | Iter | Formato | Archivo |
|---|---|---|---|---|---|
| 00-INDEX | Índice de navegación global | active | 0 | casero | [00-INDEX.md](../00-INDEX.md) |
| SPEC-000-naming | Nomenclatura agnóstica a tecnología | active | 0 | casero | [SPEC-000-naming.md](SPEC-000-naming.md) |
| SPEC-000-bootstrap | Bootstrap del proyecto y tooling | active | 0 | casero | [SPEC-000-bootstrap.md](SPEC-000-bootstrap.md) |
| SPEC-001-single-case-input | Entrada de un caso por pantalla (modo simple) | active | 1 rev.2026-05-25 | casero | [SPEC-001-single-case-input.md](SPEC-001-single-case-input.md) |
| SPEC-002-agent-client | Cliente de agente remoto agnóstico (async) | active | 2 rev.2026-06-07 | casero | [SPEC-002-agent-client.md](SPEC-002-agent-client.md) |
| SPEC-002b-message-builder | Constructor del payload hacia el agente | active | 2b | híbrido | [SPEC-002b-message-builder.md](SPEC-002b-message-builder.md) |
| SPEC-003-classification-evaluator | Evaluador de clasificación por extracción + match exacto | active | 3 | casero | [SPEC-003-classification-evaluator.md](SPEC-003-classification-evaluator.md) |
| SPEC-003b-rejected-response | Detección y evaluación de respuesta RECHAZADO | active | 3b | híbrido | [SPEC-003b-rejected-response.md](SPEC-003b-rejected-response.md) |
| SPEC-004-single-case-file | Carga de un caso unitario desde archivo (modo simple) | active | 4 | híbrido | [SPEC-004-single-case-file.md](SPEC-004-single-case-file.md) |
| SPEC-005-run-persistence | Persistencia y revisión del resultado de una ejecución | active | 5 rev.2026-06-07 | híbrido | [SPEC-005-run-persistence.md](SPEC-005-run-persistence.md) |
| SPEC-006-batch-suite | Ejecución batch y estadística de corridas | active | 6 rev.2026-06-07 | híbrido | [SPEC-006-batch-suite.md](SPEC-006-batch-suite.md) |
| SPEC-007-agent-trace | Visor de traza de ejecución del agente | active | 7 | híbrido | [SPEC-007-agent-trace.md](SPEC-007-agent-trace.md) |
| SPEC-008-suite-metrics | Métricas de suite: matriz de confusión y accuracy por clase | active | 8 impl.2026-05-27 | híbrido | [SPEC-008-suite-metrics.md](SPEC-008-suite-metrics.md) |
| SPEC-009-parallel-execution | Ejecución paralela de casos con concurrencia configurable | draft | 9 | híbrido | [SPEC-009-parallel-execution.md](SPEC-009-parallel-execution.md) |
| SPEC-010-batch-trace | Traza de ejecución por caso en corridas batch | active | 10 rev.2026-06-07 | híbrido | [SPEC-010-batch-trace.md](SPEC-010-batch-trace.md) |
| SPEC-011-agent-under-test | Selección del agente bajo prueba (perfiles) | draft | 11 | híbrido | [SPEC-011-agent-under-test.md](SPEC-011-agent-under-test.md) |
| SPEC-012-translation-evaluator | Evaluador de traducción de intents | draft | 12 rev.2026-06-13 (3 US) | híbrido | [SPEC-012-translation-evaluator.md](SPEC-012-translation-evaluator.md) |

## Spec: 00-INDEX

- `path`: `00-INDEX.md`
- `proposito`: índice de navegación global — punto de entrada único para orientarse en documentación, código y SSOTs.
- `ssot_level`: `operativo`
- `incluye`:
  - ruta de lectura recomendada con links a README, CLAUDE.md, SPECS_REGISTRY, ARCHITECTURE, CONTRIBUTING, DEVELOPMENT, PRODUCT
  - estructura del proyecto: tabla de directorios con su contenido (`src/`, `tests/`, `specs/`, `docs/`, `tools/`, `runs/`, `data/`, `historial/`)
  - mapa de SSOTs: tabla tema → archivo autoritativo
- `excluye`:
  - definiciones conceptuales extensas
  - contenido duplicado de cualquier SSOT
- `validacion`:
  - [ ] enlaces vigentes
  - [ ] link a `CLAUDE.md` presente
  - [ ] link a `specs/SPECS_REGISTRY.md` presente
  - [ ] sin duplicación de contenido de SSOTs

## Política de datos

Los datasets de entrada **no se versionan**. El detalle completo (referencias externas, `data/.gitkeep`) es SSOT en `docs/ARCHITECTURE.md` §ADR-002. Mapeo a specs: en cada ejecución el usuario carga los datos vía la interfaz —

- **Modo simple**: un caso ingresado por pantalla (SPEC-001) o cargado desde archivo (SPEC-004).
- **Modo batch** (SPEC-006): archivo de múltiples casos cargado por interfaz estable (file uploader del dashboard u otro mecanismo).

## Roadmap de iteraciones

Ver `historial/sdd.md` para el log evolutivo. El plan completo está en el documento de planificación que originó el proyecto.
