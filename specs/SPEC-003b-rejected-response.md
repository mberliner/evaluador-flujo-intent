# SPEC-003b-rejected-response — Detección y evaluación de respuesta RECHAZADO

**Estado:** active
**Iter:** 3b
**Formato:** Híbrido
**Depende de:** [[SPEC-003-classification-evaluator]], [[SPEC-001-single-case-input]]
**Relacionada con:** [[SPEC-006-batch-suite]]

## User Story (Priority: P1)

Como autor de casos de prueba, quiero poder marcar un caso como "se espera que el agente lo rechace", para verificar que el agente detecta correctamente inputs incompletos o inconsistentes y no emite una clasificación de riesgo sobre ellos.

**Why this priority:** sin esta capacidad, los casos que el agente rechaza caen siempre en "indeterminado", ocultando si el rechazo fue correcto o incorrecto. Es necesario para que la suite pueda probar el comportamiento negativo del agente (rechazar lo que debe rechazar).

**Independent Test:** dado un caso con `clasificacion_esperada="Rechazado"` y un agente que responde con "RECHAZADO", el evaluador produce `passed=True`. Verificable sin red usando stubs.

## Acceptance Scenarios

1. **Given** un caso con `clasificacion_esperada="Rechazado"` y una respuesta del agente que contiene `"RECHAZADO"`, **When** se evalúa, **Then** `passed=True` (verde).
2. **Given** un caso con `clasificacion_esperada="Rechazado"` y una respuesta del agente con una clasificación de riesgo (`"riesgo: VERDE"`), **When** se evalúa, **Then** `passed=False` (rojo).
3. **Given** un caso con `clasificacion_esperada="Verde"` y una respuesta del agente que contiene `"RECHAZADO"`, **When** se evalúa, **Then** `passed=False` (rojo).
4. **Given** cualquier caso y una respuesta del agente sin patrón reconocible, **When** se evalúa, **Then** `passed=None` (amarillo / indeterminado).

## Functional Requirements

- **FR-001**: MUST: `PALETA_CLASIFICACION` incluye `"Rechazado"` como valor válido para `clasificacion_esperada` (cambio en SPEC-001 rev).
- **FR-002**: MUST: `ClassificationEvaluator.extract()` detecta la palabra `RECHAZADO` (case-insensitive, borde de palabra) en la respuesta del agente y la devuelve normalizada como `"Rechazado"`.
- **FR-003**: MUST: La lógica de veredicto no cambia — sigue siendo exact match entre `extracted_classification` y `clasificacion_esperada`; no se introduce lógica especial para "Rechazado".
- **FR-004**: MUST: El dashboard muestra el resultado de un rechazo con el mismo mecanismo visual que cualquier otro veredicto (verde/rojo/amarillo según pass/fail/indeterminado).

## Key Entities

- **PALETA_CLASIFICACION** (SPEC-001): se extiende con `"Rechazado"`.
- **ClassificationEvaluator.extract()** (SPEC-003): se extiende el regex con `rechazado`.
- **TestResult** (SPEC-003): sin cambios — `passed=True/False/None` cubre todos los casos.

## Success Criteria

- [x] **SC-001**: `extract("El caso fue RECHAZADO por falta de campo")` devuelve `"Rechazado"`.
- [x] **SC-002**: `extract("riesgo: VERDE\n...")` devuelve `"Verde"` (sin regresión).
- [x] **SC-003**: `extract("texto sin patron")` devuelve `None` (sin regresión).
- [x] **SC-004**: caso con `clasificacion_esperada="Rechazado"` + respuesta RECHAZADO → `passed=True`.
- [x] **SC-005**: caso con `clasificacion_esperada="Rechazado"` + respuesta `"riesgo: VERDE"` → `passed=False`.
- [x] **SC-006**: caso con `clasificacion_esperada="Verde"` + respuesta RECHAZADO → `passed=False`.

## Assumptions

- El agente emite la palabra `RECHAZADO` de forma reconocible en su respuesta cuando rechaza un caso (confirmado por observación; puede refinarse si el formato cambia).
- `"Rechazado"` en la paleta no altera ninguna regla de negocio de `TestCase` más allá de ser un valor admitido en `clasificacion_esperada`.

## Coverage mapping

| Requisito | Cubierto por |
|-----------|-------------|
| FR-001 | `PALETA_CLASIFICACION` en `src/domain/test_case.py` + tests de paleta |
| FR-002 | regex extendido en `ClassificationEvaluator.extract()` + tests unitarios |
| FR-003 | sin cambio en `evaluate()` — tests existentes de pass/fail/indeterminado cubren la regresión |
| FR-004 | sin cambio en dashboard — mecanismo visual de SPEC-001 ya cubre todos los veredictos |
| SC-001..SC-006 | tests unitarios nuevos en `test_classification_evaluator.py` |

## Fuera de alcance

- Distinguir visualmente en el dashboard entre "rechazo correcto" y "rechazo incorrecto" — el verde/rojo de pass/fail es suficiente.
- Capturar la razón del rechazo del agente como campo estructurado — queda en `actual_response` del `TestResult`.

## Historial

- **2026-05-25** — Spec creada. Origen: el agente puede responder RECHAZADO ante inputs incompletos o inconsistentes; sin esta spec ese resultado cae en "indeterminado" y no es testeable intencionalmente.
- **2026-05-25** — Spec cerrada (draft → active). Implementación: regex extendido con `rechazado` en `ClassificationEvaluator.extract()`, `"Rechazado"` incorporado a `PALETA_CLASIFICACION`. SC-001..SC-006 verificados con tests unitarios.
