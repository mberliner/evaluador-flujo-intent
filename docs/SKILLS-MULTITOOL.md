# Skills multi-asistente (Claude Code · Codex · Antigravity · opencode)

> **SSOT de este tema.** Describe cómo una misma skill sirve a los cuatro
> asistentes sin duplicar contenido ni usar symlinks. El contenido del
> procedimiento de cada skill vive en `docs/playbooks/`; este documento solo
> define el mecanismo de adaptación.

## Problema

No existe un formato de skill común a los cuatro asistentes. Lo que sí existe es
una fuerte convergencia:

| Asistente | Carpeta de skills (proyecto) | Formato | Descubrimiento |
|---|---|---|---|
| **Codex** | `.agents/skills/<n>/SKILL.md` | `SKILL.md` · `name`+`description` | auto por `description` (+ `/skills`, `$nombre`) |
| **Antigravity** | `.agents/skills/<n>/SKILL.md` | `SKILL.md` · `description` (name opcional) | auto por `description` |
| **Claude Code** | `.claude/skills/<n>/SKILL.md` | `SKILL.md` · `name`+`description`+`allowed-tools` | auto por `description` |
| **opencode** | `.opencode/command/<n>.md` | command md · `description` | solo explícito `/comando` |

Codex y Antigravity comparten **ruta y formato idénticos**. Claude usa el mismo
`SKILL.md` en otra carpeta. opencode es el único divergente (commands, sin
auto-descubrimiento).

## Modelo de capas

```
docs/playbooks/<n>.md              ← SSOT del CONTENIDO (a mano, agnóstico)
.agents/skills/<n>/SKILL.md        ← SSOT del WRAPPER  (a mano) → lo leen Codex + Antigravity directo
        │  tools/gen_skill_adapters.py
        ├──→ .claude/skills/<n>/SKILL.md     (generado, committeado)
        └──→ .opencode/command/<n>.md        (generado, committeado)
```

- **Sin symlinks.** Se generan archivos reales para que funcione igual en
  Windows y Linux (los symlinks de git requieren Developer Mode en Windows).
- **Dos lugares editables** por skill: el playbook (contenido) y el `SKILL.md`
  fuente en `.agents/skills/` (metadata + cuerpo del wrapper). El resto son
  artefactos generados con cabecera `NO EDITAR A MANO`.

## Frontmatter del SKILL.md fuente

```yaml
---
name: analyze                      # id de la skill
description: <largo>               # usado por auto-discovery (Claude/Codex/Antigravity)
allowed-tools: Read, Grep, Glob    # solo lo usa Claude; los demás lo ignoran
opencode-description: <corto>      # solo para el command de opencode (opcional)
opencode-constraint: <línea>       # restricción que se anexa al command (opcional)
---
```

Los campos `opencode-*` solo alimentan al generador; nunca se filtran al
`SKILL.md` de Claude. El playbook se referencia por convención:
`docs/playbooks/<name>.md`.

## Generador

```bash
python tools/gen_skill_adapters.py            # regenera los adaptadores
python tools/gen_skill_adapters.py --check    # falla si hay drift (lo corre el pipeline)
```

`--check` está cableado en `tools/pipeline_local.sh` (paso «skills multi-tool»),
así nadie edita a mano `.claude/skills/` ni `.opencode/command/` sin que el
pipeline lo detecte. Los EOL se fuerzan a LF vía `.gitattributes` para que el
check sea determinista entre SO.

## Agregar una skill nueva

1. Escribí el procedimiento en `docs/playbooks/<n>.md` (agnóstico de asistente).
2. Creá `.agents/skills/<n>/SKILL.md` con el frontmatter de arriba y un cuerpo
   que solo enlace el playbook.
3. Corré `python tools/gen_skill_adapters.py`.
4. Commiteá fuente + generados juntos.

## Qué NO está unificado

- El **always-on** (instrucciones de protocolo) ya está cubierto por `AGENTS.md`,
  que los cuatro asistentes leen — no pasa por este generador.
- El **auto-descubrimiento** existe en Claude/Codex/Antigravity pero no en
  opencode; ahí la skill se invoca con `/comando`.
