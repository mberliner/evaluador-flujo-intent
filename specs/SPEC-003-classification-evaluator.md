# SPEC-003-classification-evaluator — Evaluador de clasificación

**Estado:** active
**Iter:** 3
**Depende de:** [[SPEC-001-single-case-input]], [[SPEC-002-agent-client]]

## Propósito

Comparar la respuesta del agente contra el ground truth del caso y emitir un veredicto pass/fail. Cierra la primera tajada vertical útil del modo simple: el usuario carga un caso, lo envía, ve la respuesta del agente y el veredicto.

## Reglas de evaluación

1. **Extracción**: regex case-insensitive busca la primera ocurrencia de un término de `PALETA_CLASIFICACION` (`Verde`, `Amarillo`, `Rojo`, `Negro` y `Rechazado` —este último lo agrega [[SPEC-003b-rejected-response]]—) en la respuesta cruda del agente. Bordes de palabra (`\b`) para no matchear substrings (ej. "Rojizo" no cuenta como "Rojo").
2. **Normalización**: el match se compara en su forma canónica de la paleta (capitalización exacta: `"Verde"`, `"Amarillo"`, `"Rojo"`, `"Negro"`). El regex es insensible a mayúsculas pero el output siempre devuelve la forma canónica.
3. **Comparación**: match exacto contra `test_case.clasificacion_esperada`. Una sola respuesta válida por caso (no se admiten variantes — ver historial del proyecto).
4. **Sin match → indeterminado**: si el regex no encuentra ningún término, el resultado es `classification=None`, `passed=None`. Esto cubre el caso de respuestas no-clasificatorias (mensajes de control de flow del agente, preguntas de clarificación, errores). El usuario decide qué hacer (reintento, descarte, ajuste de prompt).

## Modelos de dominio

### `src/domain/result.py`

```python
@dataclass(frozen=True, slots=True)
class TestResult:
    case_id: str
    expected: str                  # color esperado de la paleta
    actual_response: str           # respuesta cruda del agente
    extracted_classification: str | None  # color detectado o None
    passed: bool | None            # True/False si pudo extraer, None si no
    conversation_id: str | None = None
    notes: str = ""
```

### `src/domain/classification_evaluator.py`

```python
class ClassificationEvaluator:
    def extract(self, response: str) -> str | None: ...
    def evaluate(self, case: TestCase, agent_response: AgentResponse) -> TestResult: ...
```

- `extract`: regex `r"\b(verde|amarillo|rojo|negro|rechazado)\b"` (case-insensitive; `rechazado` lo añade [[SPEC-003b-rejected-response]] FR-002). Devuelve la primera ocurrencia normalizada a la paleta canónica, o `None`.
- `evaluate`: combina la extracción con `case.clasificacion_esperada` para producir el `TestResult`.

## Integración con el dashboard (modo simple)

Al cerrar SPEC-003 el dashboard cubre la tajada vertical completa:

1. Usuario carga form → `Validar caso`.
2. Si validó, aparece botón `Enviar al agente`.
3. Click → construye `PlatformConfig.from_env()`, `TokenProvider`, `RemoteAgentClient`.
4. `client.send(form)` donde `form = message_builder.build(case)` → captura `thread_id` de la respuesta inmediata (content = control message).
5. `client.wait_for_completion(thread_id, timeout=300)` → polling en `/threads/{thread_id}/messages` hasta que aparece un mensaje `role=assistant` que no es el control message (~10-45 s).
6. `client.get_thread_messages(thread_id)` → lista cruda de mensajes del thread.
7. Localiza el primer mensaje `role=assistant` cuyo `content` empiece con `"riesgo:"` → construye `AgentResponse(content=classification_msg_content, conversation_id=thread_id)`.
8. `ClassificationEvaluator.evaluate(case, agent_response)` → `TestResult`.
9. Pantalla muestra: badge verde "Pass" / rojo "Fail" / amarillo "Indeterminado", respuesta cruda colapsable, clasificación extraída, ground truth.

El framework UI sigue encapsulado: dashboard importa `streamlit as ui`.

> **Nota:** `extract_classification(messages)` (función pura de dominio, SPEC-002) puede usarse para verificar rápidamente si hay clasificación antes de construir el `AgentResponse`.

## Criterios de aceptación

- [x] `ClassificationEvaluator.extract` cubre paleta completa y devuelve `None` cuando no hay match.
- [x] `extract` detecta el primer match cuando hay varios (decisión documentada: "primer match").
- [x] `extract` respeta bordes de palabra (no matchea substrings).
- [x] `extract` case-insensitive en input, output canónico.
- [x] `evaluate` produce `TestResult` consistente para los 4 colores × pass/fail × indeterminado.
- [x] `TestResult` es frozen + slots; serializable a dict (`to_dict()`) y con propiedad `verdict`.
- [x] Dashboard integra `PlatformConfig` + `TokenProvider` + `RemoteAgentClient` + `ClassificationEvaluator`; muestra pass/fail/indeterminado, esperado vs detectado, respuesta cruda, `conversation_id` y `TestResult` completo.
- [x] 33 tests del evaluador (96 totales en el proyecto). Paleta cubierta × pass/fail/indeterminado, case insensitivity, bordes de palabra, sin match, RECHAZADO.
- [x] `ruff check`, `ruff format --check`, `tools/check_naming.py`: verde.
- [x] **Verificación funcional end-to-end con el agente real**: verificado 2026-05-24 — dashboard lanzado, caso TC-V-01 enviado, veredicto observado correctamente.

**Pendiente (rev.2026-05-25):**
- [x] Botón **"Evaluar otro caso"** visible en dos posiciones: antes de "Enviar al agente" y al pie de los resultados. Al pulsarlo el formulario vuelve a su estado inicial vacío sin necesidad de recargar la página.

## Fuera de alcance

- **Polling de respuestas multi-turno** del agente (cuando el primer envío devuelve mensaje de control de flow): se evalúa al final de esta iter si la spec necesita revisarse. Si el agente requiere conversación multi-turno para clasificar, se agregará `RetryingAgentClient` o similar en una iter posterior. Mientras tanto, la respuesta de control de flow cae en "indeterminado" y el usuario reintenta manualmente.
- Persistencia de runs en `runs/*.json` → [[SPEC-005-run-persistence]].
- Modo batch → [[SPEC-006-batch-suite]].

## Historial

- **Iter 3** — Spec creada. Se observó (Iter 2, smoke real) que el agente puede devolver respuestas de control de flow que no contienen clasificación. La spec lo absorbe como caso "indeterminado" sin agregar polling todavía: decisión revisable si el patrón se confirma en uso real.
- **rev.2026-05-25** — Agregado criterio pendiente: botón "Evaluar otro caso" post-envío para resetear el formulario sin recargar la página.
- **2026-06-08** — Reconciliación spec↔código: el snippet del regex de `extract` y la regla 1 mostraban solo 4 términos; el código real (`src/domain/classification_evaluator.py`) incluye `rechazado` desde [[SPEC-003b-rejected-response]]. Se actualizó el cuerpo a los 5 términos atribuyendo el quinto a SPEC-003b (sin duplicar su ownership). Sin cambio de comportamiento.
