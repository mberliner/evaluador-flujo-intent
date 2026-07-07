# ARCHITECTURE — Capas, dependencias y ADRs

SSOT de las decisiones arquitectónicas. Cualquier cambio estructural debe actualizar este documento.

## Visión general

Aplicación Python por capas, estilo Clean Architecture. Capas con dependencia unidireccional hacia el dominio (la enumeración completa y la matriz de dependencias están abajo, en «Capas» y ADR-005):

```
┌──────────────────────────┐   ┌──────────────────────────┐
│ dashboard/  (UI)         │   │ runner.py  (CLI headless)│  ← composition roots
└────────────┬─────────────┘   └────────────┬─────────────┘
             │  componen adapters + invocan use-cases    │
             ▼                                           ▼
┌────────────────────────────────────────────────────────┐
│ application/  (use-cases de orquestación)              │
└─────────────────────────┬──────────────────────────────┘
                          │ depende de
                          ▼
┌────────────────────────────────────────────────────────┐
│ domain/  (reglas + modelos + puertos)  ← SSOT          │
└─────────────────────────▲──────────────────────────────┘
                          │ implementa puertos
┌─────────────────────────┴──────────────────────────────┐
│ adapters/  (proveedores concretos)                     │
└────────────────────────────────────────────────────────┘
```

**Regla de oro**: `domain/` no importa de `adapters/`, `application/`, `dashboard/` ni `runner`. `application/` no importa de `adapters/` (concretos), `dashboard/` ni `runner` — sólo de `domain/` y `build/`. Validado por `import-linter`. Ver ADR-005.

## Capas

### `src/domain/`

Núcleo del sistema. Contiene modelos, lógica de evaluación, métricas y puertos (interfaces abstractas). Sin I/O, sin red, sin frameworks — testeable como código puro. Ningún otro paquete interno puede reemplazar este rol.

_Ejemplo representativo:_ `ClassificationEvaluator` evalúa un `TestResult` por extracción regex + match exacto; `ports.py` declara los `Protocol` que los adapters implementan; `metrics.py` agrega resultados de corridas en `SuiteMetrics`.

### `src/adapters/`

Implementaciones concretas de los puertos del dominio. Todo I/O con el mundo externo vive aquí: red, filesystem, variables de entorno. Cambiar de proveedor implica reescribir el adapter correspondiente y nada más.

_Ejemplo representativo:_ `RemoteAgentClient` encapsula el protocolo HTTP del agente externo; `SyncHttpAgentClient` hace lo propio con la plataforma alternativa síncrona y `AgentClientFactory` elige entre ambos según la config (SPEC-013); `FileRunRepository` persiste y lee corridas en `runs/`; `PlatformConfig` es la única lectora de `os.environ`.

### `src/dashboard/`

Interfaz de usuario interactiva. El framework concreto (hoy Streamlit) queda encapsulado dentro de este paquete. Compone `domain` + `adapters` para ejecutar casos y visualizar resultados, trazas y métricas.

_Ejemplo representativo:_ `trace_panel.py` renderiza la traza de ejecución de un caso; `app.py` orquesta el flujo completo de la sesión.

### `src/build/`

Transformación de datos entre formatos: construye payloads hacia el agente y parsea archivos de entrada del usuario. Funciones puras sin I/O — la serialización y el acceso a disco ocurren en los adapters.

_Ejemplo representativo:_ `message_builder.py` convierte un `TestCase` en el dict `{"form": {...}}` que espera el agente; `batch_loader.py` parsea un archivo tabular y mapea columnas a `TestCase` con autodetección de separador.

### `src/application/`

Use-cases de orquestación. Coordina `domain` + puertos para ejecutar y evaluar corridas (un caso o N), reportando progreso por callback. Sin framework de UI, sin parsing de CLI, sin I/O directo: recibe los puertos por parámetro. La comparten los dos composition roots (`dashboard/` y `runner.py`), de modo que la secuencia de negocio "enviar → esperar → leer respuesta final → evaluar → agregar" vive en un solo lugar. Importa sólo de `domain/` y `build/` — nunca de adapters concretos, `dashboard/` ni `runner`.

_Ejemplo representativo:_ `run_suite.py` expone `run_one`, `run_batch`, `build_suite` (con `on_result: ProgressCallback`), `execution_failure` y la captura de traza por caso (`_capture_trace`, SPEC-010).

### `src/runner.py`

Punto de entrada CLI/headless y **composition root** del modo no interactivo. Cablea los adapters concretos (`RemoteAgentClient`, `FileRunRepository`, `TokenProvider`, `PlatformConfig`), parsea args, invoca los use-cases de `application/` y genera reportes (ej. `--estadistica` produce la matriz de confusión en pantalla y en CSV). El formateo de reportes (`format_metrics_*`) permanece aquí (fuera del alcance de ADR-005). No pertenece a ninguna capa de negocio.

## Decisiones (ADR-style)

### ADR-001 — Nomenclatura agnóstica a tecnología

Aplicada transversalmente. Detalle en `specs/SPEC-000-naming.md`. **El `RemoteAgentClient` usa Watson Orchestrate**: el endpoint, el formato del payload y el flujo de auth están confinados a `adapters/remote_agent_client.py` + `adapters/token_provider.py`. Desde [[SPEC-013-client-adapter-selection]] la plataforma es además **seleccionable por configuración**: `AGENT_CLIENT_TYPE` decide el adaptador (`remote_async` → `RemoteAgentClient`; `sync_http` → `SyncHttpAgentClient`, REST síncrono con llave por header) y `adapters/agent_client_factory.py` centraliza ese condicional junto con la resolución del `CredentialProvider`. Cambiar/agregar un proveedor implica escribir un adaptador que cumpla el puerto `AgentClient`, registrarlo en el factory y en la requeridad condicional de `PlatformConfig`, nada más: los composition roots solo conocen el puerto.

### ADR-002 — Datos cargados en runtime por interfaz, no versionados

Los datos de prueba **no viven en el repo**. El usuario los carga en cada ejecución:

- **Modo simple** (Iter 1): un caso ingresado por pantalla en el dashboard.
- **Modo batch** (Iter 6): archivo cargado por interfaz estable (file uploader o selector de path).

Razón: los datasets son operativos y sensibles del dominio; el repo contiene **código y specs**, no **datos**.

**Referencias externas (no versionadas, solo schema/modelo):** el CSV/JSON ubicados en el workspace padre (`c:\AA\Proyectos\Claude\test_circuito_intents\intake_clasificacion.{csv,json}`) son referencia del schema y modelos de ejemplo, **no fuente operativa**: el usuario los usa como plantilla para llenar el formulario (modo simple) o construir el archivo batch (modo múltiple). `data/` es directorio de trabajo local gitignored; solo `data/.gitkeep` se versiona.

Este ADR es el SSOT del detalle de la política de datos; la `CONSTITUTION.md` (principio IV) declara el invariante y apunta aquí.

### ADR-003 — Evaluación determinista por extracción + match exacto

El veredicto de cualquier caso se obtiene extrayendo la respuesta del agente y comparándola de forma **exacta y determinista** contra el esperado del caso. No se aceptan variantes equivalentes ni LLM-as-judge. Las métricas auxiliares (p. ej. similaridad de texto) pueden reportarse como información pero **no graduan** el veredicto. Si una extracción no captura una respuesta válida, se ajusta la extracción, no el criterio de match.

Este ADR es el **SSOT enumerativo** de los evaluadores del sistema (la `CONSTITUTION.md` principio III declara el invariante agnóstico y apunta aquí). La lista crece con cada perfil de agente bajo prueba ([[SPEC-011-agent-under-test]]):

| Evaluador | Spec | Estado | Extracción | Match | Test |
|---|---|---|---|---|---|
| Clasificación | SPEC-003 | **implementado** | regex sobre la respuesta | clase detectada == clase esperada | `tests/unit/test_classification_evaluator.py` |
| Traducción | SPEC-012 | **draft — sin implementar** | `{form}` JSON de la respuesta | taxonomías exactas + completitud poblado/vacío; similaridad fuzzy **informativa** | `tests/unit/test_translation_evaluator.py` *(se crea al implementar)* |

Cada evaluador concreto cumple el puerto `Evaluator` y retorna el supertipo `EvaluatedResult` ([[SPEC-011-agent-under-test]]). Agregar un evaluador es agregar una fila a esta tabla, no enmendar la constitución.

### ADR-004 — Persistencia de runs

Cada ejecución se persiste en `runs/` sin acoplarse a una base de datos, separando **detalle** de **estadística**:

```
runs/
  detail/
    run-YYYYMMDDTHHMMSS-<token>-<case_id>.json   ← corrida unitaria (1 caso): sufijo con el case_id
    run-YYYYMMDDTHHMMSS-<token>.json             ← corrida batch (N casos): sólo el run_id
  stats/
    estadistica-casos.csv                ← una fila por caso × corrida (append; separador ';')
    estadistica-corridas.csv             ← una fila por corrida, con accuracy (regen on-demand; separador ';')
    estadistica-matriz.csv               ← matriz de confusión agregada (generada por --estadistica; separador ';')
  .gitkeep
```

- **`run_id`** = `run-YYYYMMDDTHHMMSS-<token>` identifica la corrida y vincula el archivo de detalle con sus filas en los CSV. El `<token>` es un sufijo único corto (hex) que evita la colisión de dos corridas terminadas en el mismo segundo —p. ej. dos sesiones simultáneas escribiendo en `runs/`—; el prefijo de timestamp preserva el orden por recencia. En modo unitario (SPEC-005) la corrida tiene un caso; en batch (SPEC-006), N.
- **Nombre del detalle**: lleva el sufijo `-<case_id>` **sólo** cuando la corrida tiene exactamente un caso (identifica unívocamente ese caso). En batch el archivo es `run-<ts>-<token>.json` sin sufijo de caso, porque la corrida representa muchos casos, no uno.
- **Detalle (`detail/*.json`)**: metadata de la corrida + resultados por caso + bloque `summary` con totales. SSOT por corrida.
- **`estadistica-casos.csv`**: granularidad caso × corrida; sin accuracy (a nivel caso el accuracy es redundante con el veredicto). Generado por SPEC-005 al persistir.
- **`estadistica-corridas.csv`**: granularidad corrida; incluye `accuracy_bruta` y `accuracy_efectiva`. Tiene sentido sólo agregando N casos, por lo que lo genera SPEC-006 a pedido del usuario desde la interfaz.
- **Separador de los CSV de estadística**: `;` (punto y coma), coherente con el archivo batch de entrada y con el export de planilla en español.
- El identificador del repositorio es agnóstico al formato (`RunRepository` / `FileRunRepository`), nunca nombra `json` ni `csv` (SPEC-000-naming).

### ADR-005 — Capa de aplicación: use-cases entre presentación y dominio

Los use-cases de orquestación viven en `src/application/`, no en los composition roots. `runner.py` y `dashboard/app.py` son composition roots delgados: cablean adapters concretos, traducen su canal (args vs widgets) e invocan use-cases. `application/` recibe los puertos por parámetro, reporta progreso por callback (`ProgressCallback`), y no tiene framework de UI, parsing de CLI ni I/O directo.

- **Vive en `application/run_suite.py`:** `run_one`, `run_batch`, `build_suite`, `execution_failure`, `is_execution_failure`, `_capture_trace`, `ProgressCallback`, `PhaseCallback`.
- **El flujo simple del dashboard también pasa por `run_one`** (2026-07-07; antes `_send_and_evaluate` duplicaba la orquestación): `run_one` acepta `on_phase: PhaseCallback` — callback agnóstico `(fase, detalle)` con fases `"enviando"` / `"esperando_flow"` — que cada composition root traduce a su canal (widget de estado vs. stdout). El fetch de mensajes crudos del thread (`get_thread_messages`, display del canal UI) y la persistencia siguen en el root; `is_execution_failure` permite al dashboard distinguir el fallo de ejecución sin conocer su representación interna.
- **Queda en `dashboard/`:** el stepping batch (`_run_batch_step` / `_finalize_batch`) — es control de flujo dirigido por la presentación (un caso por tick para atender "Frenar", SPEC-006 US3), no un use-case; reutiliza `application.run_one`.
- **Conocimiento del formato del archivo de caso → a `build/`** (2026-07-07): la detección/inyección de `clasificacion_esperada` ausente vive en `build/case_loader.py` (`needs_expected_classification` / `with_expected_classification`, SPEC-004 FR-007); el dashboard solo presenta el selectbox.
- **Queda en `runner.py`:** el formateo de reportes (`format_metrics_*`, `_md_table`) — presentación de texto del canal CLI.
- **Selección de respuesta final → al adapter (revisa [[SPEC-002-agent-client]]):** el filtrado del control message del agente es conocimiento del proveedor; se confina en `adapters/` (ADR-001), donde ya residía en `wait_for_completion`. El puerto `AgentClient` gana `get_final_response(thread_id, fallback_content) -> AgentResponse`; `run_one` lo invoca. `get_thread_messages` permanece crudo (display del dashboard).
- **Normalización de contenido → al dominio:** `extract_message_text` en `domain/message_text.py` (función pura ligada al contrato del puerto), importable por las tres capas.

**Enforcement:** contratos `import-linter` (`pyproject.toml`) — `application/` no importa `adapters`, `dashboard` ni `runner`; el contrato de `domain` se extiende para prohibir además `application` y `runner`.
