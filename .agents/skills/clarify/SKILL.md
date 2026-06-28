---
name: clarify
description: Detecta áreas subespecificadas en una spec y hace hasta 5 preguntas dirigidas, grabando las respuestas en la propia spec (capa semántica del Principio V). Usar antes de implementar cuando una SPEC-NNN tiene ambigüedades de impacto.
allowed-tools: Read, Grep, Glob, Edit, AskUserQuestion
opencode-description: Desambigua una spec con hasta 5 preguntas y graba las respuestas en ella (Principio V).
opencode-constraint: "Hacé las preguntas una por vez; editás la spec, nunca `src/`."
---

# clarify — adaptador del playbook de desambiguación de specs

Leé y seguí **`docs/playbooks/clarify.md`** (SSOT del procedimiento, agnóstico de
asistente). Este archivo solo enlaza el playbook; no dupliques su contenido.

- **Entrada**: el SPEC-ID que pase el usuario, o la primera spec de
  `.sdd/current-spec` si no pasa ninguno (lo detalla el playbook).
- **Preguntas**: si tu asistente ofrece UI de opción múltiple (p. ej.
  `AskUserQuestion` en Claude Code), usala; si no, preguntá en texto. Una por vez.
- **Restricción**: editás la spec, nunca `src/`.
