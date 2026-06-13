# Constitución del proyecto

**Versión:** 0.5.2 | **Ratificada:** 2026-05-26 | **Última enmienda:** 2026-06-13

## Preámbulo

- **Qué es:** lista curada de los principios no-negociables del **sistema** construido. No es documentación de referencia ni protocolo del agente: es lo que nunca cede.
- **Cómo se usa:** leer antes de diseñar una spec o un cambio. Si una spec o una decisión de implementación entra en conflicto con un principio, **se ajusta la spec, no el principio**.
- **Alcance:** cada principio declara un **invariante** estable y autocontenido. El detalle operativo (que evoluciona) vive en el SSOT referenciado en `Detalle:`. La constitución nunca duplica ese detalle: solo declara el invariante y apunta.

## Principios

### I. Nomenclatura agnóstica a tecnología

Ningún identificador de módulo, clase, función, método o archivo de código contiene nombres de proveedor/plataforma, framework de UI, formato de serialización ni protocolo de autenticación. El nombre describe *qué* hace el sistema, no *con qué* lo hace.

- **Enforcement:** `tools/check_naming.py`
- **Detalle:** `specs/SPEC-000-naming.md`

### II. Capas limpias con dependencia unidireccional

El núcleo del sistema vive en `src/domain/` como código puro —sin I/O, red ni frameworks— y no depende de ninguna otra capa. Las dependencias entre capas apuntan en una sola dirección, hacia el dominio; los proveedores concretos viven detrás de puertos, en `adapters/`. La enumeración de capas y la matriz de dependencias permitidas es detalle operativo: vive en el SSOT.

- **Enforcement:** `lint-imports`
- **Detalle:** `docs/ARCHITECTURE.md`

### III. Evaluación determinista

El veredicto de un caso se obtiene por extracción + comparación determinista y exacta contra el esperado del caso. Ningún evaluador del sistema usa LLM-as-judge ni acepta variantes equivalentes; las métricas auxiliares (p. ej. similaridad de texto) pueden informar pero nunca graduar el veredicto. Cuando una extracción no captura una respuesta válida, se ajusta la extracción, no el criterio de match. La enumeración de los evaluadores concretos y sus técnicas de extracción es detalle operativo que crece con cada perfil: vive en el SSOT, no acá.

- **Enforcement:** suite de tests de los evaluadores en `tests/unit/`
- **Detalle:** `docs/ARCHITECTURE.md`

### IV. Datos no versionados

El repositorio contiene código y specs, no datasets. Los datos de prueba se cargan en runtime por la interfaz; nunca se commitean. Los archivos de referencia externos son schema y modelos, no fuente operativa.

- **Enforcement:** `.gitignore`
- **Detalle:** `docs/ARCHITECTURE.md`

### V. Trazabilidad spec↔código

Toda capacidad del **producto** está descrita por una spec registrada antes de implementarse. El código deriva de la spec, no al revés; cuando el código diverge, se reconcilia la spec (las specs son vivas). Un cambio de comportamiento sin spec vigente que lo gobierne no se integra. Los cambios al propio método/framework SDD (gobernanza, enforcement, formato de spec) no se describen con specs de producto: se rigen por esta constitución y los documentos de método en `docs/`.

- **Enforcement:** `tools/check_traceability.py` (pipeline) + `tools/sdd_gate.py` (hook PreToolUse sobre src/)
- **Detalle:** `specs/SPECS_REGISTRY.md`, `docs/SDD-ENFORCEMENT.md`

## Governance

- **Versionado semver:** MAJOR remueve o redefine un principio; MINOR agrega un principio o sección; PATCH aclara redacción sin cambiar el invariante.
- **Fase pre-1.0:** el proyecto está en fase pre-madura; MUST NOT declararse `1.0.0` hasta alcanzar madurez sostenida (criterio acordado por el equipo). Mientras tanto la serie es `0.y.z`: lo que tras `1.0.0` sería MAJOR o MINOR sube `y` (`0.y.0`); lo que sería PATCH sube `z` (`0.0.z`). Todo artefacto versionado nuevo del proyecto MUST iniciar en `0.1.0`.
- **Procedimiento de enmienda:**
  1. Subir la versión según la regla de arriba y actualizar "Última enmienda".
  2. Registrar el cambio en `historial/sdd.md` (qué principio, por qué).
  3. Revisar los SSOTs referenciados por el principio afectado.
  4. Correr `python tools/check_constitution.py CONSTITUTION.md` y confirmar que pasa.
- **Precedencia:** un principio constitucional prevalece sobre cualquier spec o decisión de implementación. El protocolo del agente (`CLAUDE.md`) referencia esta constitución, pero no la contiene: si se cambia de asistente, la constitución sigue vigente.
