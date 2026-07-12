# SPECS_REGISTRY — Single Source of Truth de specs

Este archivo lista todas las specs vigentes del proyecto. Cada spec describe una capacidad concreta del sistema, sus criterios de aceptación y su estado. Toda implementación debe poder mapearse a una spec aquí registrada.

> Las specs son **vivas**: se actualizan tras cada iteración (spec → ejecución → observación → ajuste).

## Convenciones

- Estado: `draft` | `active` | `superseded` | `archived` | `notas` (referencia fuera de secuencia).
- Cada spec tiene un ID estable (`SPEC-NNN-slug`) y un archivo en este directorio.
- Una spec puede tener `Depende de:` y `Relacionada con:` (links `[[id]]`).
- Cierre de iteración → bloque `[SDD-Check]` en el commit citando specs leídas, includes/excludes verificados, SSOTs afectados.

## Specs vigentes

| ID | Título | Estado | Iter | Formato | Archivo |
|---|---|---|---|---|---|
| 00-INDEX | Índice de navegación global | active | 0 | casero | [00-INDEX.md](../00-INDEX.md) |
| SPEC-000-naming | Nomenclatura agnóstica a tecnología | active | 0 | casero | [SPEC-000-naming.md](SPEC-000-naming.md) |
| SPEC-000-bootstrap | Bootstrap del proyecto y tooling | active | 0 | casero | [SPEC-000-bootstrap.md](SPEC-000-bootstrap.md) |

## Spec: 00-INDEX

- `path`: `00-INDEX.md`
- `proposito`: índice de navegación global — punto de entrada único para orientarse en documentación, código y SSOTs.
- `ssot_level`: `operativo`
- `incluye`:
  - ruta de lectura recomendada con links a README, CLAUDE.md, SPECS_REGISTRY, ARCHITECTURE, CONTRIBUTING, DEVELOPMENT, PRODUCT
  - estructura del proyecto: tabla de directorios con su contenido (`src/`, `tests/`, `specs/`, `docs/`, `tools/`, `runs/`, `data/`, `historial/`)
  - mapa de SSOTs: tabla tema → archivo autoritativo
- `excluye`:
  - definiciones conceptuales extensas
  - contenido duplicado de cualquier SSOT
- `validacion`:
  - [ ] enlaces vigentes
  - [ ] link a `CLAUDE.md` presente
  - [ ] link a `specs/SPECS_REGISTRY.md` presente
  - [ ] sin duplicación de contenido de SSOTs

## Política de datos

Los datasets de entrada **no se versionan**. El detalle completo (referencias externas, `data/.gitkeep`) es SSOT en `docs/ARCHITECTURE.md` §ADR-002. En cada ejecución el usuario carga los datos vía la interfaz —

- **Modo simple**: un caso ingresado por pantalla.
- **Modo batch**: archivo de múltiples casos cargado por interfaz estable.

## Roadmap de iteraciones

El log evolutivo se registra en `historial/sdd.md` a partir de la primera iteración. El plan completo está en el documento de planificación que originó el proyecto.
