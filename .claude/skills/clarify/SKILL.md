---
name: clarify
description: Detecta áreas subespecificadas en una spec y hace hasta 5 preguntas dirigidas, grabando las respuestas en la propia spec (capa semántica del Principio V). Usar antes de implementar cuando una SPEC-NNN tiene ambigüedades de impacto.
allowed-tools: Read, Grep, Glob, Edit, AskUserQuestion
---

# clarify — wrapper Claude del playbook de desambiguación de specs

Leé y seguí **`docs/playbooks/clarify.md`** (SSOT del procedimiento, agnóstico de
asistente). Este wrapper solo lo enlaza para Claude Code; no dupliques su
contenido.

- **Entrada**: el SPEC-ID que pase el usuario, o la primera spec de
  `.sdd/current-spec` si no pasa ninguno (lo detalla el playbook).
- **Binding Claude**: usá `AskUserQuestion` para las preguntas de opción múltiple
  (paso 3 del playbook), una por vez.
- **Restricción**: editás la spec, nunca `src/`.
