# SPEC-002-agent-client — Cliente de agente remoto agnóstico

**Estado:** active
**Iter:** 2 (revisada 2026-05-23 tras verificación e2e)
**Depende de:** [[SPEC-000-naming]], [[SPEC-001-single-case-input]]

**Resumen:** SSOT del puerto `AgentClient` (5 métodos) y del puerto `CredentialProvider`, y spec del adaptador asíncrono original: `PlatformConfig`, `TokenProvider` y `RemoteAgentClient` con su protocolo real (POST lanza un flow → polling del thread → respuesta final descartando el control message). Activa, verificada e2e.

## Propósito

Implementar el adapter que habla con el agente bajo test, encapsulando proveedor, auth, transporte, formato de payload y recuperación del resultado. Cumple el puerto `AgentClient` definido en el dominio.

El agente opera en modo **async**: la respuesta real no llega inline en el POST inicial; el sistema lanza un flow y el resultado se recupera leyendo el historial del thread cuando el flow completa. Mecanismo completo: `docs/AGENT-INVOCATION.md`.

## Alcance

### `src/adapters/platform_config.py`

`PlatformConfig` (frozen dataclass) con los campos:

| Campo | Descripción |
|-------|-------------|
| `chat_url` | URL base de chat completions, con trailing slash. Ej: `.../v1/orchestrate/` |
| `token_url` | Endpoint de obtención de token IAM |
| `agents_url` | Endpoint de descubrimiento de agentes (usado por el smoke) |
| `flows_url` | Endpoint de consulta de flows: `{instance_url}/v1/orchestrate/flows` |
| `threads_url` | Endpoint de historial de threads: `{instance_url}/v1/orchestrate/threads` |
| `api_key` | Credencial |
| `agent_id` | ID del agente bajo test (fijo por configuración) |
| `accuracy_threshold` | Opcional, default 0.0 |

`flows_url` y `threads_url` se derivan de `chat_url` quitando el segmento final; `from_env()` los construye internamente, sin var de entorno propia. **Único punto del sistema que conoce los nombres de las env vars del proveedor.**

### `src/adapters/token_provider.py`

`TokenProvider` cachea y refresca el token automáticamente e **implementa el puerto `CredentialProvider`** (`get() -> str`) del dominio. Identificador agnóstico (SPEC-000-naming): el protocolo de auth concreto es detalle interno del adapter.

### `src/adapters/remote_agent_client.py`

`RemoteAgentClient` implementa el puerto `AgentClient` (`get_trace` se documenta en [[SPEC-007-agent-trace]] FR-005, no acá):

#### `send(form, conversation_id=None) -> AgentResponse`

- Recibe `form: dict` (estructura `{"form": {...}}`) construido por `MessageBuilder` ([[SPEC-002b-message-builder]]); la serialización a JSON ocurre dentro del adapter (`ensure_ascii=False`), no en el caller.
- Payload: `{ "messages": [{ "role": "user", "content": [{ "response_type": "text", "text": <json> }] }], "stream": "false" }`; agrega `"thread_id"` si `conversation_id` viene seteado.
- POST a `{chat_url}{agent_id}/chat/completions`; extrae `data["choices"][0]["message"]["content"]` y `data.get("thread_id")` → `AgentResponse(content, conversation_id)`.

> Cuando el agente lanza un flow, el `content` devuelto es siempre `"A new flow has started. This chat session is currently dedicated to the flow and will resume once the flow is complete."` — es la señal de arranque, **no la clasificación**; ésta se obtiene con los métodos siguientes.

#### `wait_for_completion(thread_id, timeout_seconds) -> bool`

- Polling de `GET {threads_url}/{thread_id}/messages` en intervalos de 10 s.
- "Respuesta final" = cualquier mensaje `role=assistant` cuyo texto no contenga `"A new flow has started"`; normaliza `content` (string o lista) con `extract_message_text`.
- Retorna `True` al detectar el mensaje final, `False` si agota el timeout.

> **Por qué no `/flows`**: el `thread_id` de `chat/completions` ≠ `agent_thread_id` en `/flows` — dos sistemas de IDs distintos. Ver `docs/AGENT-INVOCATION.md` sección 2.

#### `get_thread_messages(thread_id) -> list[dict]`

- `GET {threads_url}/{thread_id}/messages`; devuelve la lista de mensajes cruda, sin filtrado ni parsing. El campo `content` puede ser string o lista de bloques `[{"response_type":"text","text":"..."}]` — normalizar con `extract_message_text` (dominio).

#### `get_final_response(thread_id, fallback_content) -> AgentResponse`

- Lee los mensajes del thread y devuelve el primer `role=assistant` cuyo texto **no** contiene el control message; si ninguno califica, usa `fallback_content` (el `content` del `send` inicial). Devuelve `AgentResponse(content, conversation_id=thread_id)`.

> El filtrado del control message vive aquí, en el adapter (ADR-001: conocimiento del proveedor confinado en `adapters/`). Los callers (`application.run_one`, dashboard) no conocen el texto del control message.

#### `extract_message_text(content) -> str` — vive en `domain/message_text.py`

Normaliza el campo `content` de un mensaje (string o lista de bloques) a string plano. Función pura ligada al contrato del puerto; la usan el adapter, el dashboard (display) y herramientas. *(Antes `_extract_text`, privada del adapter; movida al dominio por ADR-005.)*

### `src/domain/ports.py`

**Superficie completa del puerto `AgentClient`** — esta tabla es el SSOT de la interfaz (el detalle de `get_trace` lo gobierna [[SPEC-007-agent-trace]] FR-005; el resto, esta spec):

| Método | Owner | Rol |
|--------|-------|-----|
| `send(form, conversation_id=None) -> AgentResponse` | SPEC-002 / [[SPEC-002b-message-builder]] | Envía el payload y devuelve el control message inicial |
| `wait_for_completion(thread_id, timeout_seconds) -> bool` | SPEC-002 | Polling hasta que el flow completa |
| `get_thread_messages(thread_id) -> list[dict]` | SPEC-002 | Historial crudo del thread |
| `get_final_response(thread_id, fallback_content) -> AgentResponse` | SPEC-002 | Respuesta final descartando el control message |
| `get_trace(thread_id) -> AgentTrace` | [[SPEC-007-agent-trace]] | Traza interna de sub-agentes |

> **Puerto de credenciales.** El dominio define además el puerto `CredentialProvider` (`get() -> str`) en el mismo `domain/ports.py`, implementado por el adapter `TokenProvider`. Su SSOT es esta spec.

### `src/domain/` — extracción de clasificación

> **Responsabilidad de [[SPEC-003-classification-evaluator]]**, no de esta spec. Se documenta aquí solo la función auxiliar y el formato observado del mensaje del agente.

`extract_classification(messages: list[dict]) -> str | None` (`src/domain/classification_evaluator.py`): busca el primer mensaje `role == "assistant"` cuyo `content` empiece con `"riesgo:"` (case-insensitive) y extrae el valor con regex `r"riesgo:\s*(VERDE|AMARILLO|ROJO|NEGRO)"` (RECHAZADO no usa este prefijo — lo detecta `ClassificationEvaluator.extract`). Devuelve la forma canónica de la paleta o `None`.

Formato observado del mensaje de clasificación:

```
riesgo: VERDE

FastGate Preguntas:
1. <pregunta>
<"false" si el factor de riesgo no aplica>
...
```

### `tools/connection_check.py`

Sin cambios funcionales; el smoke de conexión sigue siendo válido (verifica auth + endpoint).

## Flujo de uso desde la capa de aplicación

El use-case `application.run_one` (ADR-005) compone el puerto así:

```python
# 1. Construir el payload y enviar
form = message_builder.build(case)          # MessageBuilder (SPEC-002b)
trigger = client.send(form)                 # adapter serializa a JSON internamente
thread_id = trigger.conversation_id

# 2. Esperar que el flow complete
completed = client.wait_for_completion(thread_id, timeout_seconds=300)

# 3. Obtener la respuesta final (el adapter descarta el control message)
response = client.get_final_response(thread_id, trigger.content)  # -> AgentResponse

# 4. Evaluar (dominio — SPEC-003). El dashboard, además, llama
#    get_thread_messages(thread_id) por separado para su panel de display crudo.
result = evaluator.evaluate(case, response)
```

## Criterios de aceptación

- [x] `PlatformConfig` construye `flows_url` y `threads_url` derivándolos de `chat_url` sin vars de entorno adicionales.
- [x] `wait_for_completion()` hace polling de `/threads/{thread_id}/messages` (no `/flows`).
- [x] `wait_for_completion()` retorna `True` cuando aparece un mensaje `role=assistant` sin "A new flow has started".
- [x] `wait_for_completion()` retorna `False` si agota el timeout.
- [x] `wait_for_completion()` ignora mensajes `role=user`.
- [x] `wait_for_completion()` acepta `content` como lista (vía `_extract_text`).
- [x] `get_thread_messages()` devuelve la lista cruda sin transformar.
- [x] `get_final_response()` devuelve el primer assistant que no es el control message, como `AgentResponse`.
- [x] `get_final_response()` usa `fallback_content` cuando ningún mensaje califica.
- [x] El texto del control message no es conocido por ningún caller (vive sólo en el adapter).
- [x] `extract_message_text()` (en `domain/message_text.py`) normaliza string y lista a string plano.
- [x] `extract_classification()` extrae correctamente `VERDE`, `AMARILLO`, `ROJO`, `NEGRO`.
- [x] `extract_classification()` devuelve `None` si ningún mensaje contiene el patrón.
- [x] `extract_classification()` ignora el mensaje `"A new flow has started..."`.
- [x] Tests unitarios cubren todos los criterios anteriores con stubs de `requests.Session`.
- [x] `ruff check` y `ruff format --check` verde.
- [x] `send()` arma payload con y sin `conversation_id`.
- [x] Errores HTTP devuelven `AgentResponse` con `content` que empieza con `"Error API:"`.
- [x] Smoke real ejecutado y validado (2026-05-23).

## Fuera de alcance

- Comparación de la clasificación extraída contra ground truth → [[SPEC-003-classification-evaluator]].
- Modo batch → [[SPEC-006-batch-suite]].

## Historial

- **Iter 2** — Spec creada. Modelo sincrónico (incorrecto — el agente es async).
- **2026-05-23** — Revisión completa: confirmado modelo async; polling de `/flows` con `agent_thread_id`.
- **2026-05-24** — Corrección crítica: `thread_id` del chat ≠ `agent_thread_id` en `/flows` (nunca correlacionaba) → reemplazado por polling de `/threads/{thread_id}/messages`. `content` puede ser lista → `_extract_text()`. `flows_url` permanece para SPEC-007 (traza).
- **2026-05-25** — Sincronización con implementación: `send()` renombrado `prompt→form` (recibe `dict`, serializa internamente); `extract_classification` aclarada como responsabilidad de SPEC-003.
- **2026-06-07** — Por ADR-005 el puerto gana `get_final_response(thread_id, fallback_content)`: el filtrado del control message se confina en el adapter (antes en `runner.select_final_response`); `_extract_text` se mueve al dominio como `extract_message_text`.
- **2026-06-08** — Reconciliación spec↔código: `get_final_response` ya implementado; sus tres criterios marcados `[x]`.
- **2026-07-01** — Reconciliación documental: la sección `domain/ports.py` pasa a listar la superficie completa del puerto (5 métodos) como SSOT de la interfaz, y se registra el puerto `CredentialProvider` que existía en código sin spec que lo gobernara (cierre de gap de trazabilidad, Principio V).
- **2026-07-05** — Reescritura editorial al formato compacto (convenciones de `docs/SPEC-FORMAT.md`): Resumen ejecutivo, narrativa condensada en notas, historial podado. **Sin cambio normativo**: contratos, tablas SSOT y criterios intactos.
