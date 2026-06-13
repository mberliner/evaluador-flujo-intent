# SPEC-001-single-case-input — Entrada de un caso por pantalla

**Estado:** active
**Iter:** 1 rev.2026-05-25
**Depende de:** [[SPEC-000-naming]], [[SPEC-000-bootstrap]]

## Propósito

Permitir al usuario cargar **un caso de prueba por pantalla** mediante un formulario, validarlo contra el schema del dominio y dejarlo listo para envío al agente (envío real se aborda en [[SPEC-002-agent-client]]).

Es la primera tajada vertical útil del producto y arranca el modo simple del dashboard.

## Alcance

### Modelo de dominio (`src/domain/test_case.py`)

Clase `TestCase` (inmutable, sin dependencias externas) con campos:

- **Identificación**
  - `id: str` — identificador único del caso (string, no vacío). El schema del agente no lo requiere; es correlación interna entre envío y resultado. El dashboard lo acepta como campo opcional y genera uno automáticamente si se deja vacío.
  - `nombre_iniciativa: str`.

- **Tipo de intent** (al menos uno debe ser `True`)
  - `intent_negocio: bool`
  - `intent_operativo: bool`
  - `intent_capacidad_equipos: bool`
  - `intent_tecnico_arquitectural: bool`

- **Declaración**
  - `declaracion_intent: str` (no vacío).
  - `area_proponente: str`.
  - `flujo_de_valor: str`.
  - `metricas_de_exito: str`.
  - `impacto_personas: str`.

- **Datos requeridos** (booleans; al menos uno debe ser `True`)
  - `datos_ninguno: bool`
  - `datos_publicos: bool`
  - `datos_operativos: bool`
  - `datos_personales: bool`
  - `datos_confidenciales: bool`
  - `datos_otros: bool`
  - `datos_otros_mensaje: str` — descripción libre cuando `datos_otros=True`; default `"N/A"` cuando `datos_otros=False`. Corresponde a `datos_requeridos.otros.message` en el schema del agente (`FI_Orquestador_Input.schema.json`).

- **Contexto**
  - `supuesto_riesgo: str`.
  - `restricciones: str`.
  - `sponsor: str`.
  - `mail_contacto: str`.

- **Esperado** (ground truth)
  - `clasificacion_esperada: str` ∈ `{"Verde", "Amarillo", "Rojo", "Negro", "Rechazado"}`. Una sola opción válida (no se admiten variantes). `"Rechazado"` indica que se espera que el agente rechace el caso — ver [[SPEC-003b-rejected-response]].
  - `marcadores: tuple[str, ...]` — lista de tags asociados (puede estar vacía).

### Validación

Al construir un `TestCase`:

- Todos los `str` requeridos no pueden estar vacíos (`""` o solo whitespace).
- `id` se normaliza a `.strip()` y debe quedar no vacío.
- Al menos un `intent_*` debe ser `True`.
- Al menos un `datos_*` debe ser `True`.
- `clasificacion_esperada` debe pertenecer a la paleta exacta (case-sensitive).
- Si `datos_otros=False`, `datos_otros_mensaje` se fuerza a `"N/A"` independientemente del valor recibido.
- Si `datos_otros=True`, `datos_otros_mensaje` no puede estar vacío (`""` o solo whitespace).
- Si la validación falla → `ValueError` con mensaje específico del campo afectado.

La paleta vive como constante pública `PALETA_CLASIFICACION: tuple[str, ...]` en el módulo del dominio.

### Puertos (`src/domain/ports.py`)

Definir los `Protocol`s aunque sus implementaciones lleguen en iters siguientes:

- `AgentClient` con método `send(form: dict, conversation_id: str | None) -> AgentResponse` (mensaje + thread devuelto). El `form` lo construye `MessageBuilder` y el adapter serializa internamente — ver [[SPEC-002b-message-builder]].
- `TestCaseRepository` con métodos `load(case_id: str) -> TestCase` y `save(case: TestCase) -> None`.
- `CredentialProvider` con método `get() -> str` (token utilizable por el cliente del agente). El protocolo de auth concreto es detalle del adapter — ver [[SPEC-000-naming]] y [[SPEC-002-agent-client]].

Los Protocol son contratos, no exigen implementación todavía.

### Dashboard (`src/dashboard/app.py`)

Página con un formulario que reproduce los campos del `TestCase`. Comportamiento:

1. Render del formulario con campos agrupados (identificación, intent, declaración, datos, contexto, esperado).
2. Botón **"Validar caso"** construye un `TestCase`; si falla la validación, muestra el error.
3. Si valida OK, muestra el payload resultante (JSON serializado del form) y un banner verde "Caso listo para envío".
4. **No** envía al agente en esta iteración (eso es [[SPEC-002-agent-client]]).
5. El framework UI concreto se encapsula dentro de este módulo; ningún identificador expuesto contiene el nombre del framework (ver [[SPEC-000-naming]]).

## Criterios de aceptación

- [x] `TestCase` definido con todos los campos y reglas de validación listadas arriba.
- [x] Constante `PALETA_CLASIFICACION` exportada.
- [x] `ports.py` con `AgentClient`, `TestCaseRepository` y `CredentialProvider` como `Protocol`.
- [x] Dashboard renderiza el formulario completo y muestra el caso validado.
- [x] Tests unitarios cubren: construcción válida; cada validación que falla (id vacío, sin intent, sin datos, clasificación inválida, campo string vacío); paleta completa admitida; inmutabilidad; `datos_otros_mensaje`. (30 tests)
- [x] `mypy --strict src` verde. (mypy + types-requests instalados en el venv; streamlit override en pyproject.toml)
- [x] `ruff check src tests tools` verde.
- [x] `ruff format --check src tests tools` verde.
- [x] `python tools/check_naming.py src` y `tools/check_naming.py tests` verde.
- [x] Cobertura de `src/domain/test_case.py`: 100%.

**Pendiente (rev.2026-05-25 — datos_otros_mensaje):**
- [x] `datos_otros_mensaje: str` agregado a `TestCase` con default `"N/A"`.
- [x] Regla: si `datos_otros=False` → `datos_otros_mensaje` forzado a `"N/A"`.
- [x] Regla: si `datos_otros=True` → `datos_otros_mensaje` no vacío.
- [x] Tests unitarios nuevos: `datos_otros=True` con mensaje vacío falla; `datos_otros=False` fuerza `"N/A"` sin importar input; construcción válida con `datos_otros=True` y mensaje no vacío.
- [x] Dashboard: campo de texto `datos_otros_mensaje` visible y habilitado solo cuando `datos_otros=True`.
- [x] `mypy --strict src` verde post-cambio.

**Pendiente (rev.2026-05-25 — paleta Rechazado):**
- [x] `"Rechazado"` agregado a `PALETA_CLASIFICACION`. Ver [[SPEC-003b-rejected-response]].

**rev.2026-05-25 — id opcional en el dashboard:**
- [x] El campo `id` en el formulario es opcional: si se deja vacío, el dashboard genera un identificador interno antes de construir el `TestCase`. El dominio no cambia (`id` sigue siendo no vacío en `TestCase`).

## Fuera de alcance (próximas iters)

- Envío al agente → [[SPEC-002-agent-client]]
- Comparación de respuesta vs esperado → [[SPEC-003-classification-evaluator]]
- Carga múltiple de casos → [[SPEC-006-batch-suite]]
- Persistencia entre sesiones → [[SPEC-005-run-persistence]]

## Historial

- **Iter 1** — Spec creada. Origen del schema: referencia tomada del JSON modelo del workspace padre.
- **rev.2026-05-25** — El schema oficial del agente se incorporó al proyecto en `schemas/FI_Orquestador_Input.schema.json` (versionado). Agregado `datos_otros_mensaje: str` al modelo tras comparar `TestCase` contra el schema oficial. Ver SPEC-002b.
- **rev.2026-05-25** — Agregado `datos_otros_mensaje: str` al modelo. Origen: comparación contra `FI_Orquestador_Input.schema.json` (schema oficial del agente) al redactar SPEC-002b. El campo `datos_requeridos.otros.message` existía en la firma pero no en `TestCase`. Cambio necesario para que `MessageBuilder` (SPEC-002b) pueda construir el payload completo sin inventar valores.
- **rev.2026-05-25** — `id` declarado como correlación interna; el dashboard lo genera automáticamente si el usuario lo deja vacío. El dominio no cambia.
- **rev.2026-05-27** — Sincronización de docs: la firma del puerto `AgentClient.send()` se actualiza de `prompt: str` a `form: dict` (ya cambiada en SPEC-002/SPEC-002b); las referencias cruzadas obsoletas `[[SPEC-004-batch-input]]`/`[[SPEC-005-runner]]` se reapuntan a `[[SPEC-006-batch-suite]]`/`[[SPEC-005-run-persistence]]`. Sin cambio de comportamiento.
