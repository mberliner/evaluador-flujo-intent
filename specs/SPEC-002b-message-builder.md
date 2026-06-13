# SPEC-002b-message-builder — Constructor del payload hacia el agente

**Estado:** active
**Iter:** 2b
**Formato:** Híbrido
**Depende de:** [[SPEC-001-single-case-input]], [[SPEC-002-agent-client]]
**Relacionada con:** [[SPEC-004-single-case-file]], [[SPEC-006-batch-suite]]

## User Story (Priority: P1)

Como sistema que envía casos al agente, quiero construir el payload de envío a partir de un `TestCase` usando la firma oficial del agente (`FI_Orquestador_Input.schema.json`), para garantizar que el mensaje sea siempre válido y no dependa de serialización ad-hoc.

**Why this priority:** hoy `send()` recibe un string construido por el caller con `json.dumps(form)`, sin validación de estructura ni contrato explícito. Cualquier cambio en `TestCase` puede romper silenciosamente el payload. Formalizar el builder antes de SPEC-004 y SPEC-006 evita que ambas specs hereden ese problema.

**Independent Test:** dado un `TestCase` válido, `MessageBuilder.build()` devuelve un dict con la estructura `{form: {...}}` que pasa validación contra `FI_Orquestador_Input.schema.json`, sin campos extra (`id`, `clasificacion_esperada`, `marcadores`).

## Acceptance Scenarios

1. **Given** un `TestCase` válido con `datos_otros=False`, **When** se llama a `MessageBuilder.build(case)`, **Then** devuelve `{"form": {...}}` donde `datos_requeridos.otros == {"estado": false, "message": "N/A"}`.
2. **Given** un `TestCase` con `datos_otros=True` y `datos_otros_mensaje="dato sensible"`, **When** se llama a `MessageBuilder.build(case)`, **Then** devuelve `datos_requeridos.otros == {"estado": true, "message": "dato sensible"}`.
3. **Given** el payload construido, **When** se serializa a JSON, **Then** no contiene los campos `id`, `clasificacion_esperada` ni `marcadores`.
4. **Given** el payload construido, **When** se valida contra el schema `FI_Orquestador_Input.schema.json`, **Then** no hay errores de validación.

## Functional Requirements

- **FR-001**: MUST: `MessageBuilder.build(case: TestCase) -> dict` vive en `src/build/message_builder.py`. No en `domain/` ni en `adapters/`.
- **FR-002**: MUST: El payload tiene la estructura `{"form": {...}}` con los campos anidados que define el schema oficial.
- **FR-003**: MUST: El mapping TestCase → payload es:

  | TestCase | Payload |
  |----------|---------|
  | `nombre_iniciativa` | `form.nombre_iniciativa` |
  | `declaracion_intent` | `form.declaracion_intent` |
  | `area_proponente` | `form.area_proponente` |
  | `flujo_de_valor` | `form.flujo_de_valor` |
  | `metricas_de_exito` | `form.metricas_de_exito` |
  | `impacto_personas` | `form.impacto_personas` |
  | `supuesto_riesgo` | `form.supuesto_riesgo` |
  | `restricciones` | `form.restricciones` |
  | `sponsor` | `form.sponsor` |
  | `mail_contacto` | `form.mail_contacto` |
  | `intent_negocio` | `form.tipo_intent.negocio` |
  | `intent_operativo` | `form.tipo_intent.operativo` |
  | `intent_capacidad_equipos` | `form.tipo_intent.capacidad_equipos` |
  | `intent_tecnico_arquitectural` | `form.tipo_intent.tecnico_arquitectural` |
  | `datos_ninguno` | `form.datos_requeridos.ninguno` |
  | `datos_publicos` | `form.datos_requeridos.datos_publicos` |
  | `datos_operativos` | `form.datos_requeridos.datos_operativos` |
  | `datos_personales` | `form.datos_requeridos.datos_personales` |
  | `datos_confidenciales` | `form.datos_requeridos.datos_confidenciales` |
  | `datos_otros` | `form.datos_requeridos.otros.estado` |
  | `datos_otros_mensaje` | `form.datos_requeridos.otros.message` |
  | `id` | **excluido** |
  | `clasificacion_esperada` | **excluido** |
  | `marcadores` | **excluido** |

- **FR-004**: MUST: `send()` en `RemoteAgentClient` recibe el dict producido por `MessageBuilder` (no un string crudo). La serialización a JSON ocurre dentro del adapter, no en el caller.
- **FR-005**: MUST: Ningún identificador del módulo nombra el proveedor ni el formato (ver [[SPEC-000-naming]]).

## Key Entities

- **TestCase** (SPEC-001): fuente del mapping. Esta spec no modifica su shape.
- **MessageBuilder**: función pura o clase sin estado en `src/build/`. Recibe `TestCase`, devuelve `dict`.
- **Schema de referencia**: `schemas/FI_Orquestador_Input.schema.json` — contrato de interfaz del agente, versionado en el proyecto.

## Success Criteria

- [x] **SC-001**: `MessageBuilder.build(case)` produce un dict que pasa `jsonschema.validate()` contra `schemas/FI_Orquestador_Input.schema.json` para todo `TestCase` válido.
- [x] **SC-002**: Los campos `id`, `clasificacion_esperada` y `marcadores` nunca aparecen en el payload resultante.
- [x] **SC-003**: Tests unitarios cubren los 4 acceptance scenarios sin mocks de red.
- [x] **SC-004**: `send()` en `RemoteAgentClient` no construye el payload — solo lo serializa y lo envía.

## Assumptions

- El schema del agente (`schemas/FI_Orquestador_Input.schema.json`) es estable durante esta iteración. Si cambia, requiere revisión de esta spec y del builder.
- `jsonschema` puede agregarse como dependencia de desarrollo para los tests (no es dependencia de runtime).

## Coverage mapping

| Requisito | Cubierto por |
|-----------|-------------|
| FR-001, FR-002, FR-003 | `src/build/message_builder.py` + tests unitarios |
| FR-004 | ajuste en `src/adapters/remote_agent_client.py` + test de integración del flujo |
| FR-005 | `tools/check_naming.py` |
| SC-001 | test con `jsonschema.validate()` sobre el payload resultante |
| SC-002 | assertion explícita en tests: `assert "id" not in payload["form"]` etc. |
| SC-003 | mismos tests unitarios de los 4 acceptance scenarios (cubierto por FR-001/FR-002/FR-003) |
| SC-004 | ajuste en `src/adapters/remote_agent_client.py` (cubierto por FR-004) |

## Fuera de alcance

- Validación del payload de *respuesta* del agente → [[SPEC-003-classification-evaluator]].
- Carga desde archivo → [[SPEC-004-single-case-file]] (reutiliza `MessageBuilder` sin modificarlo).
- Versionado del schema del agente (fuera del roadmap actual).

## Historial

- **2026-05-25** — Spec creada. Origen: comparación de `FI_Orquestador_Input.schema.json` contra `TestCase` reveló que el payload se construía ad-hoc en el caller (`json.dumps(form)`) sin contrato explícito y que faltaba el campo `datos_requeridos.otros.message`. La corrección del campo se capturó en rev.2026-05-25 de SPEC-001.
- **2026-05-25** — Spec cerrada (draft → active). Implementación completa: `src/build/message_builder.py`, 8 tests unitarios (6 previos + 2 nuevos de validación jsonschema contra schema oficial). 98 tests totales verde.
