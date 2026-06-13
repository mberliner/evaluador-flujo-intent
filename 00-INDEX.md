# 00-INDEX — Navegación del proyecto

## Ruta recomendada

1. [README.md](README.md) — qué es el proyecto y cómo arrancarlo
2. [CONSTITUTION.md](CONSTITUTION.md) — principios no-negociables del sistema (leer antes de diseñar)
3. [CLAUDE.md](CLAUDE.md) — protocolo SDD para asistentes IA
4. [specs/SPECS_REGISTRY.md](specs/SPECS_REGISTRY.md) — specs vigentes y estado de cada capacidad
5. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — capas y reglas de dependencia
6. [docs/AGENT-INVOCATION.md](docs/AGENT-INVOCATION.md) — cómo conectarse al agente, flujo de mensajes y traza interna
7. [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) — workflow, commits y code review
8. [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) — setup local y comandos clave
9. [docs/PRODUCT.md](docs/PRODUCT.md) — producto y métricas
10. [docs/SPEC-FORMAT.md](docs/SPEC-FORMAT.md) — template y convenciones para escribir specs (leer antes de crear una spec nueva)

## Estructura del proyecto

| Directorio / archivo | Contenido |
|---|---|
| `src/domain/` | Lógica de negocio pura: modelos, puertos, evaluadores |
| `src/adapters/` | Implementaciones concretas: cliente de agente, token, config |
| `src/dashboard/` | Interfaz de usuario (modo simple) |
| `src/build/` | Builders y ensambladores |
| `tests/unit/` | Tests rápidos sin red ni filesystem |
| `tests/integration/` | Tests con marker `smoke` que golpean el agente real |
| `specs/` | Specs de comportamiento por capacidad (SPEC-NNN-*.md) |
| `docs/` | Arquitectura, desarrollo, producto, contributing |
| `tools/` | Utilidades de validación (check_naming, etc.) |
| `schemas/` | Contratos de interfaz externos — versionados (ej. schema del agente) |
| `runs/` | Salidas de ejecuciones — gitignored |
| `data/` | Datasets locales de trabajo — gitignored |
| `historial/` | Log evolutivo de iteraciones SDD |

## Mapa de SSOTs

| Tema | SSOT |
|---|---|
| Principios no-negociables del sistema | `CONSTITUTION.md` |
| Protocolo del agente (asistentes IA) | `CLAUDE.md` (`AGENTS.md` apunta aquí) |
| Specs de comportamiento | `specs/SPECS_REGISTRY.md` |
| Arquitectura | `docs/ARCHITECTURE.md` |
| Conexión y flujo de mensajes del agente | `docs/AGENT-INVOCATION.md` |
| Setup y comandos | `docs/DEVELOPMENT.md` |
| Producto y métricas | `docs/PRODUCT.md` |
| Workflow y commits | `docs/CONTRIBUTING.md` |
| Nomenclatura agnóstica | `specs/SPEC-000-naming.md` |
| Formato y template de specs | `docs/SPEC-FORMAT.md` |
| Enforcement de trazabilidad (Principio V) | `docs/SDD-ENFORCEMENT.md` |
| Historial de iteraciones | `historial/sdd.md` |
| Schema del agente (contrato externo) | `schemas/FI_Orquestador_Input.schema.json` |
