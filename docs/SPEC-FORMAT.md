# SPEC-FORMAT — Formato y convenciones de specs

SSOT del método de redacción de specs del proyecto. Aplica desde SPEC-004 en adelante.
Las specs SPEC-000 a SPEC-003 usan el formato casero previo (no migrar).

---

## Origen e hibridación

### Formato casero (SPEC-000 a SPEC-003)

Las primeras specs del proyecto se redactaron con un formato propio: secciones libres de propósito, alcance, criterios de aceptación e historial. Funcional para iters tempranas donde el alcance era pequeño y el equipo era el único lector.

### GitHub Spec Kit

El formato híbrido toma como base el **GitHub Spec Kit** — un método de especificación orientado a cortes verticales independientes, con User Stories priorizadas, requisitos funcionales con verbos modales (`MUST`/`SHOULD`/`MAY`) y criterios de éxito medibles en formato Given/When/Then. Su ventaja principal: cada User Story es demostrable y testeable de forma aislada, lo que obliga a pensar en MVP incremental en lugar de especificar funcionalidad monolítica.

> **Término canónico:** **corte vertical** — una capacidad que atraviesa todas las capas (UI → dominio → datos) y entrega valor demostrable de punta a punta (traducción de *vertical slice*). Es el vocabulario oficial del proyecto; no usar "tajada" ni "rebanada".

### Por qué hibridar

El GitHub Spec Kit está diseñado para productos de software general. Este proyecto agrega tres capas que el kit no cubre:

| Necesidad del proyecto | Extensión añadida |
|------------------------|-------------------|
| Nomenclatura agnóstica a proveedor/framework | Regla explícita en FR/SC: sin nombres de tecnología |
| Trazabilidad SDD (spec → código → test) | Coverage mapping obligatorio |
| Historial evolutivo de decisiones | Sección Historial con fechas absolutas y motivaciones |
| Ciclo de vida de la spec | Estados `draft/active/superseded/archived/notas` con criterios de transición |
| SSOT único por tema | Convención de links `[[SPEC-NNN]]` y política de no duplicar información |

### Cuándo se decidió

El corte se acordó el **2026-05-25** al redactar SPEC-002b y SPEC-003b — las primeras specs que describían comportamiento nuevo sobre una base ya implementada, donde el formato casero resultaba insuficiente para expresar los contratos de interfaz y los criterios de cobertura de tests.

---

## Corte de formato

| Rango | Formato | Motivo |
|-------|---------|--------|
| SPEC-000 a SPEC-003 | Casero (secciones libres) | Redactadas antes de adoptar el método híbrido |
| SPEC-004 en adelante | **Híbrido** (este documento) | Acordado 2026-05-25 |

---

## Estructura de una spec híbrida

```
# SPEC-NNN-slug — Titulo corto

**Estado:** draft | active | superseded | archived
**Iter:** NNN
**Formato:** Híbrido
**Depende de:** [[SPEC-NNN-slug]], ...          ← omitir si no hay
**Relacionada con:** [[SPEC-NNN-slug]], ...     ← omitir si no hay

## User Story (Priority: P1 | P2 | P3)

[Quién necesita qué y por qué — en lenguaje de negocio, no técnico]

**Why this priority:** [Por qué este nivel; qué se bloquea si no está]

**Independent Test:** [Cómo validar esta historia sola, sin el resto del sistema]

## Acceptance Scenarios

1. **Given** [estado inicial], **When** [acción], **Then** [resultado esperado]
2. ...

## Functional Requirements

- **FR-001**: MUST: [Sujeto] [comportamiento concreto y verificable en presente]
- **FR-002**: ...

  > Marcar ambigüedades: **FR-003**: [NEEDS CLARIFICATION: descripcion del gap]

## Key Entities   ← incluir solo si la spec introduce o modifica modelos de datos

- **NombreEntidad**: qué representa, atributos clave, relaciones.

## Success Criteria

- [ ] **SC-001**: [Criterio medible y binario — pasa o no pasa]
- [ ] **SC-002**: ...

  > Marcar como [x] al cerrar la iteración.

## Assumptions

- [Supuesto de alcance, entorno o dependencia externa]

## Coverage mapping

| Requisito | Cubierto por |
|-----------|-------------|
| FR-001 | archivo o test que lo verifica |
| SC-001 | test o comando concreto |

## Fuera de alcance

- [Qué no hace esta spec y dónde va si aplica — link a otra spec]

## Historial

- **YYYY-MM-DD** — [Qué cambió y por qué]
```

---

## Estructura de una spec con múltiples User Stories (estándar multi-HU)

Cuando una spec contiene **dos o más User Stories**, cada historia es un corte vertical independiente y se redacta **encapsulada de inicio a fin**: lleva sus propios `Acceptance Scenarios`, `Functional Requirements`, `Key Entities`, `Success Criteria`, `Assumptions`, `Coverage mapping` y `Fuera de alcance`. Sólo el **header** (`Estado`/`Iter`/`Formato`/`Depende de`/`Relacionada con`) y el **`Historial`** son globales.

Reglas:

- **Numeración prefijada por HU**: los FR y SC reinician en cada historia con el prefijo de la historia — `FR-US1-001`, `SC-US1-001`, `FR-US2-001`, … Así una referencia cruzada (en el coverage, en otra spec o en el historial) es inequívoca sin tener que aclarar a qué HU pertenece.
- Cada HU debe poder leerse y testearse aislada: su `Independent Test` y su `Coverage mapping` no dependen de otra historia.
- Las secciones opcionales (`Key Entities`, `Edge Cases`) se incluyen sólo en las HUs que las necesitan.
- Una spec de **una sola** User Story usa el template simple de arriba (sin prefijo de HU).

Esqueleto:

```
# SPEC-NNN-slug — Título corto

[header global: Estado / Iter / Formato / Depende de / Relacionada con]

---

## User Story 1 — Título (Priority: PX)

Narrativa + **Why this priority:** + **Independent Test:**

### Acceptance Scenarios
### Functional Requirements      (FR-US1-001, FR-US1-002, …)
### Key Entities                 ← si aplica
### Success Criteria             (SC-US1-001, …)
### Assumptions
### Coverage mapping
### Fuera de alcance

---

## User Story 2 — Título (Priority: PX)

…mismo set, numerado FR-US2-001 / SC-US2-001…

---

## Historial   (global)

- **YYYY-MM-DD** — [qué cambió y por qué]
```

Referencia viva: [specs/SPEC-010-batch-trace.md](../specs/SPEC-010-batch-trace.md) es la primera spec redactada en este estándar.

---

## Reglas de redacción

### Identificadores y naming

Toda spec respeta **SPEC-000-naming**: los nombres de módulos, clases y funciones que aparecen en la spec no pueden contener referencias a proveedor, framework UI, formato o protocolo de auth. Si la spec menciona una implementación concreta, hacerlo en el cuerpo o en el historial, nunca en el título ni en los FR/SC.

### User Stories y numeración

- Una spec con **2+ User Stories** es **estándar multi-HU** (obligatorio): cada HU se encapsula de inicio a fin con sus propias secciones y los FR/SC se **prefijan por historia** (`FR-US1-001`, `SC-US2-001`). Ver «Estructura de una spec con múltiples User Stories».
- Una spec con **una sola** User Story usa el template simple, con `FR-001` / `SC-001` sin prefijo.
- El estándar multi-HU rige desde su adopción (2026-05-27). Specs multi-HU previas se migran a este formato; no conviven dos estilos.

### FR (Functional Requirements)

- Usar `MUST` para obligatorio, `SHOULD` para recomendado, `MAY` para opcional.
- **El keyword va siempre al inicio de la descripción del FR**, seguido de dos puntos: `MUST: [sujeto + verbo en presente]`. Nunca en el medio de la frase.
  - Bien: `- **FR-001**: MUST: El sistema acepta un archivo de caso y construye un TestCase.`
  - Mal: `- **FR-001**: El sistema MUST aceptar un archivo de caso.`
- La frase posterior al keyword es español legible en presente de indicativo (no infinitivo).
- Un FR por línea, verificable de forma independiente.
- En specs multi-HU, prefijar por historia: `FR-US1-001`, `FR-US2-001` (ver «User Stories y numeración»).
- Si un FR no está claro al momento de redactar, marcarlo `[NEEDS CLARIFICATION: ...]` en lugar de asumir.

### SC (Success Criteria)

- Binarios: o pasan o no pasan. Sin "mayormente", "generalmente", "debería".
- Tecnológicamente agnósticos: describir el comportamiento, no la implementación.
  - Bien: "El formulario vuelve a su estado inicial vacío sin recargar la página."
  - Mal: "El `session_state` se limpia con `form_gen += 1` y se llama `ui.rerun()`."
- Marcar `[x]` al cerrar la iteración, nunca antes.
- **Toda spec con UI MUST incluir un SC de verificación funcional en la aplicación real** — no basta con tests unitarios. Ese SC es el último en marcarse `[x]` y es requisito de cierre.

### Acceptance Scenarios

- Formato estricto Given / When / Then.
- Cada scenario debe poder convertirse en un test unitario o de integración directamente.

### Coverage mapping

- Cada FR y SC debe tener al menos una entrada en el coverage mapping.
- Actualizar el mapping cuando la implementación difiere de lo planeado.

### Estado y ciclo de vida

| Estado | Significado |
|--------|-------------|
| `draft` | Spec escrita, implementación pendiente |
| `active` | Implementada y todos los SC marcados [x] |
| `superseded` | Reemplazada por otra spec (indicar cuál) |
| `archived` | Descartada (indicar motivo en historial) |
| `notas` | Referencia futura sin fecha de inicio comprometida |

Una spec pasa de `draft` a `active` cuando:
1. Todos los SC están marcados `[x]`, **incluyendo el SC de verificación funcional en la app real** (obligatorio para specs con UI).
2. `pytest`, `ruff`, `mypy --strict` y `check_naming.py` pasan en verde.
3. El historial registra el cierre con fecha.
4. `SPECS_REGISTRY.md` refleja el nuevo estado.

### Historial

- Una entrada por evento relevante: creación, revisión de comportamiento, cierre.
- Fecha absoluta (`YYYY-MM-DD`), no relativa ("ayer", "esta semana").
- Incluir la motivación del cambio, no solo el qué.

---

## Ejemplo mínimo (SPEC-003b como referencia)

Ver [specs/SPEC-003b-rejected-response.md](../specs/SPEC-003b-rejected-response.md) — primera spec redactada en formato híbrido para este proyecto (una sola User Story).

Para el estándar **multi-HU** (2+ User Stories encapsuladas, numeración prefijada): [specs/SPEC-010-batch-trace.md](../specs/SPEC-010-batch-trace.md).

---

## Template copiable

Copiar este bloque completo al crear una spec nueva. Reemplazar los placeholders `NNN`, `slug`, `PX` y el contenido entre corchetes. Borrar las secciones opcionales que no apliquen (`Key Entities`, `Edge Cases`).

```markdown
# SPEC-NNN-slug — Título corto

**Estado:** draft
**Iter:** NNN
**Formato:** Híbrido
**Depende de:** [[SPEC-NNN-slug]]
**Relacionada con:** [[SPEC-NNN-slug]]

## User Story (Priority: PX)

Como [rol], quiero [capacidad], para [beneficio].

**Why this priority:** [por qué este nivel; qué se bloquea si no está]

**Independent Test:** [cómo validar esta historia sola, sin el resto del sistema]

## Acceptance Scenarios

1. **Given** [estado inicial], **When** [acción], **Then** [resultado esperado]
2. **Given** [estado inicial], **When** [acción], **Then** [resultado esperado]

### Edge Cases  ← eliminar si no hay

- MUST: [caso borde obligatorio]

## Functional Requirements

- **FR-001**: MUST: [sujeto + comportamiento concreto en presente]
- **FR-002**: MUST: [sujeto + comportamiento concreto en presente]
- **FR-003**: SHOULD: [sujeto + comportamiento recomendado]

## Key Entities  ← eliminar si la spec no introduce ni modifica modelos

- **NombreEntidad**: qué representa, atributos clave, relaciones.

## Success Criteria

- [ ] **SC-001**: [criterio medible y binario]
- [ ] **SC-002**: [criterio medible y binario]

## Assumptions

- [supuesto de alcance, entorno o dependencia externa]

## Coverage mapping

| Requisito | Cubierto por |
|-----------|-------------|
| FR-001 | [archivo o test que lo verifica] |
| FR-002 | [archivo o test que lo verifica] |
| SC-001 | [test o comando concreto] |
| SC-002 | [test o comando concreto] |

## Fuera de alcance

- [qué no hace esta spec → [[SPEC-NNN-slug]] si aplica]

## Historial

- **YYYY-MM-DD** — Spec creada. [motivación]
```
