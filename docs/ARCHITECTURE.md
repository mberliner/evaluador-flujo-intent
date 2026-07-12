# ARCHITECTURE — Capas, dependencias y ADRs

SSOT de las decisiones arquitectónicas. Cualquier cambio estructural debe actualizar este documento.

## Visión general

Aplicación Python por capas, estilo Clean Architecture. Capas con dependencia unidireccional hacia el dominio:

```
┌────────────────────────────────────────────────────────┐
│ dashboard/  (UI — composition root)                    │
└─────────────────────────┬──────────────────────────────┘
                          │ compone adapters + invoca dominio
                          ▼
┌────────────────────────────────────────────────────────┐
│ domain/  (reglas + modelos + puertos)  ← SSOT          │
└─────────────────────────▲──────────────────────────────┘
                          │ implementa puertos
┌─────────────────────────┴──────────────────────────────┐
│ adapters/  (proveedores concretos)                     │
└────────────────────────────────────────────────────────┘
```

**Regla de oro**: `domain/` no importa de `adapters/` ni `dashboard/`. Validado por `import-linter` (contrato en `pyproject.toml`). Ver ADR-001.

## Capas

### `src/domain/`

Núcleo del sistema. Contendrá modelos, lógica de evaluación, métricas y puertos (interfaces abstractas). Sin I/O, sin red, sin frameworks — testeable como código puro. Ningún otro paquete interno puede reemplazar este rol.

### `src/adapters/`

Implementaciones concretas de los puertos del dominio. Todo I/O con el mundo externo vive aquí: red, filesystem, variables de entorno. Cambiar de proveedor implica reescribir el adapter correspondiente y nada más.

### `src/dashboard/`

Interfaz de usuario interactiva. El framework concreto queda encapsulado dentro de este paquete. Compone `domain` + `adapters` para ejecutar casos y visualizar resultados.

### `src/build/`

Transformación de datos entre formatos: construcción de payloads hacia el agente y parsing de archivos de entrada del usuario. Funciones puras sin I/O — la serialización y el acceso a disco ocurren en los adapters.

## Decisiones (ADR-style)

### ADR-001 — Nomenclatura agnóstica a tecnología

Aplicada transversalmente. Detalle en `specs/SPEC-000-naming.md`. El cliente del agente remoto (`RemoteAgentClient`, en `src/adapters/`) usará un proveedor concreto, pero el endpoint, el formato del payload y el flujo de auth quedan confinados a ese adapter: es el nombre agnóstico el que aísla al proveedor. Cambiar de proveedor implica reescribir el adapter y su spec, nada más.

### ADR-002 — Datos cargados en runtime por interfaz, no versionados

Los datos de prueba **no viven en el repo**. El usuario los carga en cada ejecución:

- **Modo simple** (primero): un caso ingresado por pantalla en el dashboard.
- **Modo batch** (posterior): archivo cargado por interfaz estable (file uploader o selector de path).

Razón: los datasets son operativos y sensibles del dominio; el repo contiene **código y specs**, no **datos**.

**Referencias externas (no versionadas, solo schema/modelo):** el CSV/JSON ubicados en el workspace padre (`c:\AA\Proyectos\Claude\test_circuito_intents\intake_clasificacion.{csv,json}`) son referencia del schema y modelos de ejemplo, **no fuente operativa**: el usuario los usa como plantilla para llenar el formulario (modo simple) o construir el archivo batch (modo múltiple). `data/` es directorio de trabajo local gitignored; solo `data/.gitkeep` se versiona.

Este ADR es el SSOT del detalle de la política de datos; la `CONSTITUTION.md` (principio IV) declara el invariante y apunta aquí.

### ADR-003 — Evaluación determinista por extracción + match exacto

El veredicto de cualquier caso se obtiene extrayendo la respuesta del agente y comparándola de forma **exacta y determinista** contra el esperado del caso. No se aceptan variantes equivalentes ni LLM-as-judge. Las métricas auxiliares (p. ej. similaridad de texto) pueden reportarse como información pero **no graduan** el veredicto. Si una extracción no captura una respuesta válida, se ajusta la extracción, no el criterio de match.

Este ADR es el **SSOT enumerativo** de los evaluadores del sistema (la `CONSTITUTION.md` principio III declara el invariante agnóstico y apunta aquí). La tabla de evaluadores concretos se poblará a medida que se implementen.
