---
description: Análisis read-only de consistencia y cobertura de una spec contra tests, registro y constitución (capa semántica del Principio V).
argument-hint: <SPEC-NNN-slug> (o vacío para la spec declarada en .sdd/current-spec)
allowed-tools: Read, Grep, Glob
---

# /analyze — análisis de adecuación de una spec

Adaptado de GitHub Spec Kit (`/speckit.analyze`) a la estructura de este
proyecto. Complementa a `tools/check_traceability.py`: ese check es
**determinista** (estructura, consistencia registro, FR sin cobertura); este
comando aporta el juicio **semántico** de *adecuación* que un script no puede
dar. Ver `docs/SDD-ENFORCEMENT.md`.

## Operación

**ESTRICTAMENTE READ-ONLY**: no modifiques ningún archivo. Producí un reporte.

## Entrada

Spec objetivo: `$ARGUMENTS`. Si está vacío, leé la primera SPEC declarada en
`.sdd/current-spec`. Si no hay ninguna, pedí al usuario el ID y detené.

## Pasos

1. **Cargar artefactos** (solo lo necesario):
   - La spec `specs/$ARGUMENTS.md`: User Stories, Functional Requirements (`FR-NNN`), Success Criteria (`SC-NNN`), Coverage mapping, Edge Cases.
   - `specs/SPECS_REGISTRY.md`: estado y formato de la spec.
   - `CONSTITUTION.md`: los 5 principios (para validar conflictos).
   - `tests/`: tests que cubren la capacidad (buscá por nombre/keywords y por las referencias del Coverage mapping).
   - `docs/SPEC-FORMAT.md`: formato esperado.

2. **Pasos de detección** (alta señal, máx. 50 hallazgos):
   - **Cobertura semántica**: ¿cada `FR-NNN` mapea a un test que realmente lo ejercita (no solo aparece en la tabla)? ¿hay requisitos *implícitos* en el comportamiento que no tienen FR? (este es el gap que dejó pasar el caso `run_id`).
   - **Ambigüedad**: adjetivos vagos sin criterio medible (rápido, robusto, seguro); marcadores `[NEEDS CLARIFICATION]` sin resolver.
   - **Subespecificación**: FR con verbo pero sin objeto o resultado medible; User Story sin Acceptance Scenarios alineados.
   - **Conflicto constitucional**: cualquier FR o decisión que choque con un principio MUST (I naming, II capas, III determinismo, IV datos, V trazabilidad). Estos son CRITICAL.
   - **Inconsistencia**: deriva de terminología; entidades referidas en el código pero ausentes de la spec (o viceversa).

3. **Reporte** (Markdown, sin escribir archivos):

   | ID | Categoría | Severidad | Ubicación | Resumen | Recomendación |
   |----|-----------|-----------|-----------|---------|---------------|

   Severidad: **CRITICAL** (viola principio MUST / FR sin ninguna cobertura) ·
   **HIGH** (FR sin test que lo ejercite, atributo medible ausente) ·
   **MEDIUM** (deriva de terminología, edge case subespecificado) ·
   **LOW** (redacción).

   Cerrá con: total de FR, % con test, conteo de ambigüedades, issues CRITICAL,
   y "Próximas acciones" (qué resolver antes de implementar; sugerí `/clarify` si
   hay ambigüedades de alto impacto).

## Reglas

- NUNCA modifiques archivos (read-only).
- NUNCA inventes secciones ausentes: si faltan, reportalo.
- Priorizá conflictos constitucionales (siempre CRITICAL).
- Reportá cero issues con gracia (reporte de éxito con cobertura).
