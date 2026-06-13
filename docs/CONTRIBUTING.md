# CONTRIBUTING — Cómo trabajar en este proyecto

SSOT del workflow. Si algo no está aquí, no es regla.

## Filosofía: SDD adaptativo

Cada capacidad del sistema vive en una spec en `specs/SPEC-NNN-*.md`. Las specs son **vivas**: cada ejecución de la suite es un experimento que puede ajustar la spec del evaluador, del cliente, del builder, etc. No hay specs estáticas.

Ciclo por iteración:

```
escribir/actualizar spec  →  implementar  →  ejecutar  →  observar  →  ajustar spec
```

## Mapa de SSOTs

Ver [`00-INDEX.md`](../00-INDEX.md) para el mapa completo de documentación.

Toda otra documentación enlaza al SSOT correspondiente, **no duplica**.

## Flujo de cambios

### Cambios pequeños (< 100 líneas, sin riesgo arquitectónico)

Commit directo a trunk con `pre-commit` verde.

### Cambios grandes (≥ 100 líneas o arquitectónicos)

1. Branch `feat/SPEC-NNN-slug` o `fix/short-desc`.
2. Actualizar/crear la spec correspondiente **antes** de codear.
3. PR con descripción que enlace la spec y el SDD-Check.
4. Merge tras `pre-commit` verde y revisión.

## Definition of done por iteración

Una iteración cierra cuando:

- [ ] Spec(s) afectadas actualizadas en `specs/`.
- [ ] `SPECS_REGISTRY.md` refleja el estado real.
- [ ] Todos los criterios de aceptación de la spec marcados.
- [ ] `pre-commit run --all-files` verde.
- [ ] `historial/sdd.md` registra el cierre con fecha y resumen.
- [ ] El último commit incluye bloque `[SDD-Check]`:

```
[SDD-Check]
- Specs leídas: SPEC-NNN-x, SPEC-NNN-y
- Includes/excludes verificados: <qué se respetó del scope de la spec>
- SSOTs afectados: <archivos SSOT que cambiaron>
```

## Code review

Lista mínima:

1. ¿El cambio mapea a una spec registrada?
2. ¿Los nombres respetan `SPEC-000-naming`?
3. ¿`domain/` sigue libre de imports de `adapters/`/`dashboard/`?
4. ¿Hay tests cubriendo el cambio (unit y, si aplica, integración)?
5. ¿La spec se actualizó si el comportamiento cambió?

## Qué NO hacer

- **No** duplicar SSOT (si algo ya vive en `ARCHITECTURE.md`, no replicarlo en una spec ni viceversa; enlazar).
- **No** introducir nombres específicos de proveedor/framework en `src/` (ver SPEC-000-naming).
- **No** mergear sin spec actualizada si el comportamiento cambió.
- **No** silenciar el linter sin justificación documentada en la spec.
