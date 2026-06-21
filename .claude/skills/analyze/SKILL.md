---
name: analyze
description: Análisis read-only de consistencia y cobertura de una spec contra tests, registro y constitución (capa semántica del Principio V). Usar antes de implementar una capacidad o cuando se pide auditar la adecuación de una SPEC-NNN.
allowed-tools: Read, Grep, Glob
---

# analyze — wrapper Claude del playbook de adecuación de specs

Leé y seguí **`docs/playbooks/analyze.md`** (SSOT del procedimiento, agnóstico de
asistente). Este wrapper solo lo enlaza para Claude Code; no dupliques su
contenido.

- **Entrada**: el SPEC-ID que pase el usuario, o la primera spec de
  `.sdd/current-spec` si no pasa ninguno (lo detalla el playbook).
- **Restricción**: read-only. No edites archivos; producí el reporte en Markdown.
