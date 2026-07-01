# SPEC-002-agent-client — Cliente de agente remoto agnóstico

**Estado:** active
**Iter:** 2 (revisada 2026-05-23 tras verificación e2e)
**Depende de:** [[SPEC-000-naming]], [[SPEC-001-single-case-input]]

## Propósito

Implementar el adapter que habla con el agente bajo test, encapsulando proveedor, auth,
transporte, formato de payload y recuperación del resultado. Cumple el puerto `AgentClient`
definido en el dominio.

El agente opera en modo **async**: la respuesta real no llega inline en el POST inicial sino
que el sistema lanza un flow, y el resultado se recupera leyendo el historial del thread una
vez que el flow completa. El mecanismo completo está documentado en `docs/AGENT-INVOCATION.md`.

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

`flows_url` y `threads_url` se derivan de `chat_url` quitando el segmento final (`/orchestrate/`
queda como base compartida). `from_env()` los construye internamente — no requieren var de
entorno propia.

**Único punto del sistema que conoce los nombres de las env vars del proveedor.**

### `src/adapters/token_provider.py`

Sin cambios respecto a Iter 2. `TokenProvider` cachea y refresca el token automáticamente e **implementa el puerto `CredentialProvider`** (`get() -> str`) del dominio. El identificador es agnóstico (SPEC-000-naming): el protocolo de auth concreto es detalle interno del adapter.

### `src/adapters/remote_agent_client.py`

`RemoteAgentClient` implementa el puerto `AgentClient`. Expone los siguientes métodos (`get_trace` se documenta en [[SPEC-007-agent-trace]] FR-005, no acá):

---

#### `send(form, conversation_id=None) -> AgentResponse`

Envía el payload construido por `MessageBuilder` al agente (ver [[SPEC-002b-message-builder]]).

- Recibe `form: dict` (estructura `{"form": {...}}`). La serialización a JSON ocurre dentro del adapter (`json.dumps(form, ensure_ascii=False)`), no en el caller.
- Construye payload: `{ "messages": [{ "role": "user", "content": [{ "response_type": "text", "text": <json> }] }], "stream": "false" }`. Agrega `"thread_id"` si `conversation_id` viene seteado.
- POST a `{chat_url}{agent_id}/chat/completions`.
- Extrae `data["choices"][0]["message"]["content"]` y `data.get("thread_id")`.
- Devuelve `AgentResponse(content, conversation_id)`.

El `content` devuelto cuando el agente lanza un flow es siempre:
`"A new flow has started. This chat session is currently dedicated to the flow and will resume once the flow is complete."`

Ese texto **no es la clasificación** — es la señal de que el flow arrancó. La clasificación
se obtiene con los métodos siguientes.

---

#### `wait_for_completion(thread_id, timeout_seconds) -> bool`

Hace polling en `/threads/{thread_id}/messages` hasta que aparece la respuesta final del agente.

- Consulta `GET {threads_url}/{thread_id}/messages` en intervalos de 10 s.
- Considera "respuesta final" cualquier mensaje `role=assistant` cuyo texto no contenga
  `"A new flow has started"`.
- Usa `_extract_text(content)` para normalizar el campo `content` (puede ser string o lista).
- Retorna `True` en cuanto detecta el mensaje final, `False` si agota el timeout.

> **Por qué no `/flows`**: el `thread_id` devuelto por `chat/completions` ≠ `agent_thread_id`
> en `/flows` — son dos sistemas de IDs distintos. Ver `docs/AGENT-INVOCATION.md` sección 2.

---

#### `get_thread_messages(thread_id) -> list[dict]`

Recupera el historial completo del thread.

- `GET {threads_url}/{thread_id}/messages`.
- Devuelve la lista de mensajes sin filtrado ni parsing.
- El campo `content` puede ser string o lista de objetos `[{"response_type":"text","text":"..."}]`.
  Usar `extract_message_text(content)` (dominio) para normalizar.

#### `get_final_response(thread_id, fallback_content) -> AgentResponse`

Devuelve la respuesta final del agente, encapsulando el conocimiento del control message.

- Lee los mensajes del thread y elige el primer `role=assistant` cuyo texto **no** contenga el control message (`"a new flow has started"`).
- Si ninguno califica, usa `fallback_content` (el `content` del `send` inicial).
- Devuelve `AgentResponse(content, conversation_id=thread_id)`.
- **El filtrado del control message vive aquí, en el adapter** (ADR-001: conocimiento del proveedor confinado en `adapters/`; ya residía en `wait_for_completion`). Los callers (`application.run_one`, dashboard) no conocen el texto del control message.

#### `extract_message_text(content) -> str` — vive en `domain/message_text.py`

Normaliza el campo `content` de un mensaje (string o lista de bloques) a string plano. Función pura ligada al contrato del puerto, en el dominio. La usan el adapter (interno + `get_final_response`), el dashboard (display) y herramientas. *(Antes era `_extract_text`, privada en `remote_agent_client.py`; movida al dominio por ADR-005.)*

---

### `src/domain/ports.py`

**Superficie completa del puerto `AgentClient`** — esta tabla es el SSOT de la interfaz (el detalle de `get_trace` lo gobierna [[SPEC-007-agent-trace]] FR-005; el resto, esta spec):

| Método | Owner | Rol |
|--------|-------|-----|
| `send(form, conversation_id=None) -> AgentResponse` | SPEC-002 / [[SPEC-002b-message-builder]] | Envía el payload y devuelve el control message inicial |
| `wait_for_completion(thread_id, timeout_seconds) -> bool` | SPEC-002 | Polling hasta que el flow completa |
| `get_thread_messages(thread_id) -> list[dict]` | SPEC-002 | Historial crudo del thread |
| `get_final_response(thread_id, fallback_content) -> AgentResponse` | SPEC-002 | Respuesta final descartando el control message |
| `get_trace(thread_id) -> AgentTrace` | [[SPEC-007-agent-trace]] | Traza interna de sub-agentes |

> **Puerto de credenciales.** El dominio define además el puerto `CredentialProvider` (`get() -> str`) en el mismo `domain/ports.py`, implementado por el adapter `TokenProvider` (ver abajo). Su SSOT es esta spec.

### `src/domain/` — extracción de clasificación

> **Responsabilidad de [[SPEC-003-classification-evaluator]]**, no de esta spec. Se documenta aquí solo como referencia del formato observado del mensaje del agente.

`extract_classification(messages: list[dict]) -> str | None` vive en `src/domain/classification_evaluator.py`:

- Recorre los mensajes buscando el primero con `role == "assistant"` cuyo `content` empiece con `"riesgo:"` (case-insensitive).
- Extrae el valor con regex: `r"riesgo:\s*(VERDE|AMARILLO|ROJO|NEGRO)"` (RECHAZADO no usa este prefijo — se detecta por `ClassificationEvaluator.extract`).
- Devuelve la forma canónica de la paleta o `None`.

Formato observado del mensaje de clasificación:

```
riesgo: VERDE

FastGate Preguntas:
1. <pregunta>
<"false" si el factor de riesgo no aplica>
...
```

### `tools/connection_check.py`

Sin cambios funcionales. El smoke de conexión sigue siendo válido (verifica auth + endpoint).

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
- **2026-05-23** — Revisión completa. Confirmado modelo async. Se implementó polling de `/flows` con `agent_thread_id`.
- **2026-05-24** — Corrección crítica: `thread_id` del chat ≠ `agent_thread_id` en `/flows` — son dos sistemas de IDs distintos. El polling de `/flows` nunca correlacionaba. Reemplazado por polling de `/threads/{thread_id}/messages`. Descubierto que `content` en mensajes del thread puede ser lista; agregado `_extract_text()`. `flows_url` permanece en `PlatformConfig` para uso de SPEC-007 (traza).
- **2026-05-25** — Sincronización con implementación: `send()` renombrado `prompt→form` (recibe `dict` de `MessageBuilder`, serializa internamente). Ejemplo de flujo actualizado. `extract_classification` aclarada como responsabilidad de SPEC-003. Sección "Revisión pendiente" eliminada (SPEC-002b cerrada).
- **2026-06-07** — Revisión por ADR-005 (capa de aplicación). El puerto `AgentClient` gana `get_final_response(thread_id, fallback_content)`: el filtrado del control message del agente se confina en el adapter (antes en `runner.select_final_response`). `_extract_text` (privado en el adapter) se mueve al dominio como `extract_message_text` en `domain/message_text.py`. `get_thread_messages` sigue crudo (display del dashboard).
- **2026-06-08** — Reconciliación spec↔código: `get_final_response` está implementado (`src/domain/ports.py`, `src/adapters/remote_agent_client.py`) y sus tres criterios se marcan `[x]` (figuraban pendientes pese a estar hechos).
- **2026-07-01** — Reconciliación documental (sin cambio de código): la sección `domain/ports.py` pasa a listar la **superficie completa** del puerto `AgentClient` (5 métodos, con `get_trace` referido a [[SPEC-007-agent-trace]]) como SSOT de la interfaz; el bloque incremental previo enumeraba solo 3 y el encabezado decía "tres métodos". Se registra el puerto **`CredentialProvider`** (implementado por `TokenProvider`), que existía en el código y que [[SPEC-011-agent-under-test]]/[[SPEC-013-client-adapter-selection]] citan como "puerto existente" sin que ninguna spec lo gobernara (cierre de gap de trazabilidad, Principio V).
