---
description: Detecta áreas subespecificadas en una spec y hace hasta 5 preguntas dirigidas, escribiendo las respuestas en la propia spec.
argument-hint: <SPEC-NNN-slug> (o vacío para la spec declarada en .sdd/current-spec)
allowed-tools: Read, Grep, Glob, Edit
---

# /clarify — reducir ambigüedad de una spec antes de implementar

Adaptado de GitHub Spec Kit (`/speckit.clarify`) a este proyecto. Se ejecuta
ANTES de codear (Principio V). Es la contraparte interactiva de `/analyze`:
detecta huecos y los resuelve grabando las respuestas en la spec.

## Entrada

Spec objetivo: `$ARGUMENTS`. Si está vacío, usá la primera SPEC de
`.sdd/current-spec`. Si no hay, pedí el ID y detené. Si el archivo no existe,
indicá crear la spec primero (no la crees aquí).

## Pasos

1. **Escaneo de ambigüedad** sobre `specs/$ARGUMENTS.md` usando esta taxonomía;
   marcá cada categoría como Clara / Parcial / Ausente:
   - Alcance funcional y comportamiento; out-of-scope explícito; roles.
   - Modelo de datos: entidades, atributos, **reglas de identidad y unicidad**, ciclo de vida, supuestos de volumen/escala.
   - Interacción y flujos; estados de error/vacío/carga.
   - Atributos no funcionales: rendimiento, **concurrencia / edición simultánea**, confiabilidad, observabilidad, seguridad/privacidad.
   - Integraciones y dependencias externas; formatos.
   - Edge cases y manejo de fallos; **resolución de conflictos (ediciones concurrentes)**; rate limiting.
   - Restricciones y trade-offs; alternativas rechazadas.
   - Terminología y consistencia; criterios de aceptación testeables.

   (Las categorías en negrita son las que más fácilmente dejan pasar requisitos
   implícitos: prestales atención especial.)

2. **Cola priorizada** (máx. 5 preguntas): solo las que cambien materialmente
   arquitectura, modelo de datos, decomposición en tareas, diseño de tests o
   comportamiento. Ordená por (Impacto × Incertidumbre).

3. **Preguntas, una por vez** (no reveles las siguientes):
   - Opción múltiple (2–5 opciones mutuamente excluyentes) con tu recomendación arriba, o respuesta corta (`<=5 palabras`).
   - Validá la respuesta antes de avanzar.

4. **Integración tras cada respuesta aceptada**:
   - Asegurá una sección `## Clarifications` con un subtítulo `### Session YYYY-MM-DD`.
   - Agregá `- Q: <pregunta> → A: <respuesta>`.
   - Aplicá la aclaración a la sección correspondiente (Functional Requirements, Success Criteria como métrica, Edge Cases, etc.). Si convierte un requisito implícito en explícito, **agregá el `FR-NNN` correspondiente** (esto es lo que previene el antipatrón del requisito implícito sin FR).
   - Guardá la spec tras cada integración (Edit).

5. **Cierre**: número de preguntas, secciones tocadas, y si quedan categorías
   sin resolver, recomendá re-correr `/clarify` o `/analyze`.

## Reglas

- Máximo 5 preguntas. Si no hay ambigüedades de impacto: "No hay ambigüedades críticas" y sugerí proceder.
- No toques `src/` (esto edita la spec, no el código).
- No reordenes secciones ajenas; mantené la jerarquía de encabezados.
