# Protocolo SDD para asistentes IA

> **SSOT del protocolo del agente.** Este archivo es la fuente única; los
> asistentes que buscan `AGENTS.md` por convención (opencode, Cursor, Codex,
> Aider, Gemini CLI…) lo leen directo. Claude Code lo recibe vía `@AGENTS.md`
> en `CLAUDE.md`. El workflow humano (Definition of done, bloque `[SDD-Check]`,
> code review) es SSOT de [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md).

Cuando trabajes en este proyecto, sigue este protocolo:

## Antes de cualquier cambio

1. Lee `CONSTITUTION.md`. Ningún cambio ni spec nueva puede violar un principio constitucional; si una spec entra en conflicto con un principio, se ajusta la spec, no el principio.
2. Lee `00-INDEX.md` para orientarte en la estructura de documentación y SSOTs.
3. Lee `specs/SPECS_REGISTRY.md` para entender qué specs están vigentes.
4. Identifica a qué spec(s) corresponde el cambio. Si no hay spec, créala antes de codear.
5. Lee `specs/SPEC-000-naming.md` y aplica la regla de nomenclatura agnóstica en todo identificador nuevo.
6. Lee `docs/ARCHITECTURE.md` para respetar las capas (`domain/` no importa de `adapters/` ni `dashboard/`).

## Durante el cambio

- Actualiza la spec si el comportamiento implementado difiere de lo especificado (las specs son vivas).
- Mantén el SSOT único por tema: no dupliques información entre `docs/`, `specs/` y README.
- Cualquier cambio que toque comportamiento requiere test correspondiente en `tests/unit/` o `tests/integration/`.

## Al cerrar una iteración

1. Corre `bash tools/pipeline_local.sh` y asegúrate que esté verde (constitución, trazabilidad SDD, lint, format, mypy, naming, capas, bandit, pytest unit e integration). Si el pipeline no está disponible, corre `pre-commit run --all-files` como mínimo.
2. Actualiza `specs/SPECS_REGISTRY.md` con el estado actual de las specs.
3. Agrega una entrada en `historial/sdd.md` con fecha, scope, decisiones tomadas, deuda arrastrada.
4. El commit de cierre incluye bloque `[SDD-Check]`:

```
[SDD-Check]
- Specs leídas: SPEC-NNN-x, SPEC-NNN-y
- Includes/excludes verificados: ...
- SSOTs afectados: ...
```

## Qué NO hacer

- No introducir nombres con `watson`, `streamlit`, `json`, `iam`, etc. en `src/` (ver SPEC-000-naming).
- No mergear con specs desactualizadas.
- No agregar dependencias sin justificación en `docs/DEVELOPMENT.md`.
- No duplicar SSOT.
