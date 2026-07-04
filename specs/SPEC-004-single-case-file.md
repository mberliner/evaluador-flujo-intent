# SPEC-004-single-case-file — Carga de un caso unitario desde archivo

**Estado:** active
**Iter:** 4
**Formato:** Híbrido
**Depende de:** [[SPEC-001-single-case-input]], [[SPEC-000-naming]]
**Relacionada con:** [[SPEC-006-batch-suite]], [[SPEC-002b-message-builder]]

## User Story (Priority: P1)

Como usuario que ya tiene casos en formato modelo, quiero **cargar un caso individual subiendo un archivo** (además de tipearlo en el formulario), para no re-ingresar a mano un caso que ya existe. Sigue siendo **modo simple**: un caso a la vez.

**Why this priority:** es la extensión más barata sobre SPEC-001 (reusa toda su validación de `TestCase`) y elimina la fricción de re-tipear, lo que habilita probar más casos por sesión. No depende de persistencia ni de batch.

**Independent Test:** subo un archivo con un caso → el sistema lo valida contra `TestCase` y muestra "listo para envío", idéntico al caso tipeado. Verificable sin tocar ejecución ni persistencia.

## Acceptance Scenarios

1. **Given** un archivo con un caso válido, **When** lo cargo, **Then** el caso se puebla, valida y se habilita "Enviar al agente" (mismo estado que el form tipeado).
2. **Given** un archivo con un caso inválido (campo requerido vacío, clasificación fuera de paleta, ningún `intent_*` en `True`), **When** lo cargo, **Then** se muestra el error específico del campo, reutilizando las reglas de validación de SPEC-001 — no se duplica lógica de validación.
3. **Given** un archivo mal formado (no parseable), **When** lo cargo, **Then** se muestra un error de formato claro y no se habilita el envío.
4. **Given** un archivo en formato puro del agente sin `clasificacion_esperada`, **When** lo cargo, **Then** el dashboard me pide elegir la clasificación esperada (selectbox con la paleta) y solo tras elegirla se construye el `TestCase` y se habilita el envío.

### Edge Cases

- Archivo con **múltiples casos** cargado en modo simple → se toma el primero silenciosamente; los restantes se ignoran. Modo batch requiere [[SPEC-006-batch-suite]].
- Campos extra no reconocidos en el archivo → se ignoran silenciosamente.
- `id` **ausente o vacío** en el archivo → el loader auto-genera un identificador de correlación interna (`TC-<hex>`). Nota de responsabilidad: el `id` es correlación interna (no lo exige el schema del agente, ver [[SPEC-001-single-case-input]]); la auto-generación en el loader (`build/`) es consistente con la que SPEC-001 hace en el dashboard para el formulario.
- **Lista vacía** (`[]`) → `CaseLoadError` ("archivo vacío"). **Raíz que no es objeto ni lista** (string, número) → `CaseLoadError` ("debe contener un objeto JSON"). Ambos son variantes específicas del Acceptance Scenario 3 (archivo no utilizable), ya cubiertas por tests.

## Clarifications

### Session 2026-06-07

- Q: El loader acepta dos formatos (plano + payload anidado del agente) pero la spec declaraba uno solo. ¿Cómo se reconcilia? → A: Ambos son contrato. El shape anidado es el del schema oficial (`FI_Orquestador_Input.schema.json`), ya gobernado por [[SPEC-002b-message-builder]] como salida de `MessageBuilder`; SPEC-004 cubre su **parseo de entrada** (dirección inversa). El formato plano queda como conveniencia. Se agrega **FR-006** y se actualizan Assumptions y Coverage mapping.
- Q: Los archivos en formato puro del agente no traen `clasificacion_esperada`; el dashboard ya la pide por selectbox pero ningún FR lo gobierna. ¿Se formaliza? → A: Sí. Se agrega **FR-007** + Acceptance Scenario 4 + fila de Coverage mapping. El comportamiento (detectar ausencia → solicitar con la paleta → inyectar antes de construir el `TestCase`) pasa de implícito a requisito MUST.
- Q: El loader auto-genera el `id` cuando falta o viene vacío, pero SPEC-001 lo ubica en el dashboard y SPEC-004 no lo cubría. ¿Cómo se formaliza? → A: Como **Edge Case** con nota de responsabilidad (no nuevo MUST): `id` ausente/vacío → auto-generado en la carga; correlación interna consistente con SPEC-001.
- Q: SC-002 afirma "100%" pero faltan tests (regla "al menos un `datos_*`" no ejercitada por loader; paritario compara solo 3 atributos). → A: Reforzar tests manteniendo el claim. Se anota como pendiente en SC-002; refuerzo de tests pendiente en `tests/unit/test_case_loader.py`.

## Functional Requirements

- **FR-001**: MUST: El sistema acepta un archivo de un caso y construye un `TestCase` a partir de su contenido.
- **FR-002**: MUST: El sistema reutiliza las reglas de validación de `TestCase` (SPEC-001) sin reimplementarlas; un caso inválido cargado por archivo produce el mismo error que el mismo caso ingresado por formulario.
- **FR-003**: MUST: El parseo del archivo vive en `src/build/` (capa reservada por ADR-002 para preparación de datos), no en `domain/` ni en `dashboard/`.
- **FR-004**: MUST: Ningún identificador del módulo de carga nombra el formato del archivo (ver SPEC-000-naming; `json` está en el allowlist pero se prefiere nombre semántico, p. ej. `case_loader`, no `json_loader`).
- **FR-005**: MUST: El dashboard ofrece la carga por archivo como alternativa al formulario, dejando ambos caminos disponibles en modo simple.
- **FR-006**: MUST: El loader acepta archivos en el **formato del schema oficial del agente** (`{"form": {...}}` con `tipo_intent`/`datos_requeridos` anidados, el inverso del payload que produce [[SPEC-002b-message-builder]] contra `FI_Orquestador_Input.schema.json`). Adicionalmente, por conveniencia (tests y entrada manual), acepta el **formato plano** (campos de `TestCase` en la raíz). Ambos producen el mismo `TestCase`. El shape anidado no se define aquí: es el contrato de SPEC-002b / el schema; esta spec solo gobierna su parseo de entrada.
- **FR-007**: MUST: Cuando el archivo no incluye `clasificacion_esperada` (caso típico de los archivos en formato puro del agente, donde el ground truth no es parte del payload), el dashboard la solicita al usuario —selectbox con `PALETA_CLASIFICACION`— y la inyecta antes de construir el `TestCase`. La carga no se habilita hasta que el usuario elige una clasificación válida. `clasificacion_esperada` no se infiere ni se deja vacía.
- **FR-008**: SHOULD: Una vez que el caso está cargado y validado, el expander "Cargar un caso desde archivo JSON" expone el botón "Enviar al agente" directamente dentro de sí mismo, permitiendo enviar sin cerrar el expander ni hacer scroll hasta la sección de envío.

## Key Entities

- **TestCase** (existente, SPEC-001): destino del parseo. Esta spec NO modifica su shape.
- **Archivo de caso**: documento estructurado con los campos de un `TestCase`. El schema de referencia es `schemas/FI_Orquestador_Input.schema.json` (contrato oficial del agente, versionado en el proyecto).

## Success Criteria

- [x] **SC-001**: un caso válido en formato modelo se carga y queda listo para envío sin edición manual. *(tests unitarios)*
- [x] **SC-002**: el 100% de las reglas de validación de SPEC-001 aplican igual por archivo que por formulario. *(tests unitarios)* — Respaldado por `test_sin_datos_levanta_value_error` (regla "al menos un `datos_*`") y por `test_mismo_testcase_que_construccion_directa`, que ahora compara **igualdad completa** del `TestCase` (frozen dataclass), no un subconjunto de atributos.
- [x] **SC-003**: un archivo inválido nunca habilita el envío. *(tests unitarios)*
- [x] **SC-004**: verificación funcional en el dashboard — subir un archivo JSON real, confirmar que el caso aparece cargado y el botón "Enviar al agente" se habilita.

## Assumptions

- El archivo puede venir en dos shapes (ver FR-006): el **formato del schema oficial del agente** (`{"form": {...}}` anidado, contrato de [[SPEC-002b-message-builder]]) o el **formato plano** (campos de `TestCase` en la raíz, conveniencia para tests/entrada manual). Ambos producen el mismo `TestCase`.
- La carga es local / por la interfaz; los datos no se versionan (ADR-002).

## Coverage mapping

| Requisito | Cubierto por |
|---|---|
| FR-001, FR-002 | módulo `src/build/case_loader.py` + tests unitarios (válido / inválido / mal formado) |
| FR-003, FR-004 | ubicación del módulo + `tools/check_naming.py` |
| FR-005 | integración en `src/dashboard/app.py` + verificación funcional |
| FR-006 | `test_formato_plano_se_carga`, `test_formato_payload_agente_anidado`, fixtures reales (`test_fixture_tc_v01_con_id_carga_correctamente`) |
| FR-007 | flujo de inyección en `src/dashboard/app.py` (`_file_needs_clasificacion` / `_inject_clasificacion`), ejercitado **directamente** por `tests/unit/test_dashboard_file_load.py` (detección de ausencia, inyección y round-trip end-to-end); las fixtures en `test_case_loader.py` invocan la `_inject_clasificacion` real; verificación funcional SC-004 |
| SC-001 | tests unitarios de carga de caso válido (cubierto por FR-001) |
| SC-002 | test que parsea por archivo y compara `TestCase` resultante vs. construcción directa |
| SC-003 | tests unitarios de archivo inválido (cubierto por FR-001) |
| FR-008 | botón "Enviar al agente" dentro del expander de carga por archivo en `src/dashboard/app.py` (bloque `stored_in_expander`); verificación funcional |
| SC-004 | verificación funcional en `src/dashboard/app.py` (cubierto por FR-005) |

## Fuera de alcance

- Carga de **múltiples** casos → [[SPEC-006-batch-suite]].
- Persistencia del resultado de la ejecución → [[SPEC-005-run-persistence]].
- Traza del agente → notas `SPEC-007` (fuera de secuencia activa).

## Historial

- **2026-07-04** — FR-008 agregado: botón "Enviar al agente" disponible dentro del expander de carga por archivo, evitando scroll hasta la sección de envío. Implementado en `src/dashboard/app.py` (bloque `stored_in_expander` al final del expander).

- **2026-05-25** — Spec creada en formato híbrido. Re-corte del roadmap: el viejo SPEC-004-batch-input se difiere a SPEC-006; esta spec toma el slice "carga unitaria por archivo" que antes no existía. `[NEEDS CLARIFICATION]` embebidos a resolver al implementar (decisión del usuario, 2026-05-25).
- **2026-05-25** — Implementación inicial: `src/build/case_loader.py` (`load()` + `CaseLoadError`), integración en `src/dashboard/app.py` (expander "Cargar caso desde archivo JSON"), 19 tests unitarios incluyendo 3 fixtures reales. Decisiones tomadas: lista con múltiples casos → toma el primero silenciosamente; campos extra → ignorados; id ausente o vacío → auto-generado.
- **2026-05-25** — Correcciones post-implementación: (1) loader reescrito para manejar formato payload del agente con `tipo_intent`/`datos_requeridos` anidados, además del formato plano; (2) dashboard ampliado con selectbox inline para `clasificacion_esperada` cuando el archivo no la incluye (archivos en formato puro de agente); (3) botón "Limpiar" del final movido a `main()` con resultado guardado en `session_state["eval_result"]` para que su handler siempre ejecute; (4) scroll al inicio via `scrollIntoView()` con anchor `<a name="inicio">`. SC-004 verificado funcionalmente. draft → active.
- **2026-06-07** — `/analyze` → resolución A1 (HIGH): los tests de FR-007 duplicaban la lógica de inyección con un helper local `_inject()`, dejando `_file_needs_clasificacion` / `_inject_clasificacion` (dashboard) sin cobertura real. Se eliminó la duplicación: `test_case_loader.py` ahora reusa la `_inject_clasificacion` real y se añadió `tests/unit/test_dashboard_file_load.py` que ejercita directamente ambas funciones (detección, inyección, round-trip y flujo end-to-end con fixture). Coverage mapping de FR-007 actualizado. Pipeline verde (238 tests). Sin cambio de comportamiento.
- **2026-06-07** — `/clarify`: reconciliación spec↔código (comportamientos implícitos → explícitos, Principio V). Se agregó **FR-006** (dual formato: schema oficial del agente + plano), **FR-007** (solicitud de `clasificacion_esperada` ausente) + Acceptance Scenario 4, Edge Cases (`id` auto-generado, lista vacía / raíz no-objeto), y `Relacionada con: [[SPEC-002b-message-builder]]`. Coverage mapping ampliado. SC-002 mantiene el claim "100%" y se reforzaron sus tests: `test_sin_datos_levanta_value_error` (regla "al menos un `datos_*`") y `test_mismo_testcase_que_construccion_directa` ampliado a igualdad completa del `TestCase`. Ver sección `## Clarifications`.
