# AGENT-INVOCATION — Conexión, flujo de mensajes y trazabilidad interna

SSOT del mecanismo de invocación del agente "FI Orquestador" en Watson Orchestrate.
Cubre: cómo conectarse, el flujo de mensajes del cliente, y cómo leer la traza interna de sub-agentes.

---

## 1. Endpoints involucrados

| Rol | Método | URL |
|-----|--------|-----|
| Invocar al agente | `POST` | `{instance_url}/v1/orchestrate/{agent_id}/chat/completions` |
| Leer historial de mensajes | `GET` | `{instance_url}/v1/orchestrate/threads/{thread_id}/messages` |
| Leer traza de flows internos | `GET` | `{instance_url}/v1/orchestrate/flows?limit=50` |

Donde `instance_url` = `https://api.us-south.watson-orchestrate.cloud.ibm.com/instances/{instance_id}`.

El endpoint de mensajes **no lleva `agent_id` en el path** — opera a nivel de instancia.

---

## 2. Dos planos de identidad

Watson Orchestrate mantiene **dos sistemas de IDs** que no son intercambiables:

| Plano | ID | Cómo obtenerlo | Para qué sirve |
|-------|----|----------------|----------------|
| **Conversación** (cliente) | `thread_id` | Body del POST inicial | Leer mensajes del thread |
| **Ejecución de flows** (interno) | `agent_thread_id` / `wxo_thread_id` | Respuesta de `/flows` | Trazar sub-agentes internos |

**Estos UUIDs son distintos para la misma ejecución.** El `thread_id` del cliente no aparece en los flows — usar `/threads/{thread_id}/messages` para esperar resultados, y `/flows` solo para trazar.

El body del POST también devuelve `run_id`. Es el candidato para correlacionar con `/flows` (pendiente de verificación — ver SPEC-007).

---

## 3. Flujo de mensajes del cliente (lo que implementa `RemoteAgentClient`)

```
CLIENTE                              WATSON ORCHESTRATE
  │                                        │
  │  POST /chat/completions                │
  │  { messages: [{ role: "user",          │
  │      content: [{ response_type:        │
  │        "text", text: <form JSON> }]    │
  │    }], stream: "false" }               │
  │ ──────────────────────────────────►   │
  │                                        │  ← dispara "FI Flujo Agentico"
  │  200 OK                                │
  │  { thread_id: "abc123",                │
  │    run_id:    "9f942fe0-...",          │
  │    choices[0].message.content:         │
  │    "A new flow has started..." }       │
  │ ◄──────────────────────────────────   │
  │                                        │
  │  [polling cada 10 s]                   │  ┌─ FI Flujo Agentico ejecutando
  │                                        │  │   sub-agentes internos (~30-45 s)
  │  GET /threads/abc123/messages          │  │
  │ ──────────────────────────────────►   │  │
  │  [{ role: "assistant",                 │  │
  │     content: "A new flow..." }]        │  │  ← solo control message: seguir
  │ ◄──────────────────────────────────   │  │    esperando
  │                                        │  │
  │  [esperar 10 s, reintentar]            │  │
  │                                        │  └─ flow completado, msgs depositados
  │  GET /threads/abc123/messages          │
  │ ──────────────────────────────────►   │
  │  [{ role: "user",    ... },            │  msg 1: form enviado por el cliente
  │   { role: "assistant",                 │  msg 2: "A new flow has started..."
  │     "A new flow..." },                 │
  │   { role: "assistant",                 │  msg 3: ★ CLASIFICACIÓN ★
  │     "riesgo: VERDE\n..." },            │
  │   { role: "assistant",                 │  msg 4: confirmación técnica
  │     "El flujo se ejecutó..." }]        │
  │ ◄──────────────────────────────────   │
  │                                        │
  ▼                                        ▼

  wait_for_completion() retorna True
  (encontró msg assistant sin "A new flow has started")

  get_thread_messages() devuelve la lista completa
  extract_classification() lee msg 3 → "Verde"
```

**Criterio de completitud**: cualquier mensaje `role=assistant` cuyo texto no contenga `"A new flow has started"` indica que el flow terminó. Ver `wait_for_completion()` en `src/adapters/remote_agent_client.py`.

---

## 4. Formato del mensaje de clasificación

El agente deposita en el thread un mensaje `role=assistant` con este formato:

```
riesgo: VERDE

FastGate Preguntas:
1. <pregunta>
<"false" si el factor de riesgo no aplica>

2. <pregunta>
<"false">

...
```

La clasificación está siempre en la **primera línea**, con el patrón `riesgo: (VERDE|AMARILLO|ROJO|NEGRO)`.

Caso especial — **RECHAZADO**: el agente rechaza el caso con un mensaje que contiene la palabra `RECHAZADO` pero **no** usa el prefijo `riesgo:`. Se detecta por `ClassificationEvaluator.extract()` (regex de paleta completa sobre la respuesta cruda), no por `extract_classification()` (que busca el prefijo). Ver SPEC-003b.

---

## 5. Formato del campo `content` en mensajes del thread

El campo `content` en `/threads/{id}/messages` **no es siempre un string**. Puede venir como lista:

```json
"content": [{"response_type": "text", "text": "riesgo: VERDE\n\nFastGate Preguntas: ..."}]
```

La función `_extract_text(content)` en `src/adapters/remote_agent_client.py` normaliza ambos formatos a string plano. Todo código que lea mensajes del thread debe usarla.

---

## 6. Traza interna de sub-agentes (`/flows`)

`/flows` **no sirve para esperar que el agente termine** (usar `/threads` para eso — sección 3). Su utilidad es describir qué ocurrió internamente entre los sub-agentes.

### Estados del flow externo (`flow_async_chat`)

```
POST recibido
      │
      ▼
┌─────────────┐
│ in_progress │   cargar_iniciativa_v2 corriendo
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ interrupted │   flow_nested corriendo (FI Agente validador de Intents)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  completed  │   email enviado, mensajes depositados en el thread
└─────────────┘
```

`interrupted` **no es un fallo** — es el estado normal mientras el flow anidado ejecuta. ⚠️ El estado del flow externo puede leerse `interrupted` si se consulta `/flows` **antes** de que cierre su cola de tareas finales (`actualizar_iniciativa`, `send_mail`, `__flow_end__`); esas tareas corren **después** de depositar la clasificación en el thread (ver SPEC-007 FR-012).

### Pasos del flow externo (`tasks`) y sub-evaluaciones

Los pasos que traza `get_trace()` son los `tasks` del flow externo, en el orden de `sequence.steps`. Pasos observados (run real 2026-05-27):

1. `cargar_iniciativa_v2`
2. `FI - Agente validador de Intents`
3. `Branch 1`
4. `FI Fast Gate Google`
5. `actualizar_iniciativa`
6. `Generacion de mails`
7. `Generacion de To+Subject+Body`
8. `send_mail`
9. `__flow_end__`

Las **sub-evaluaciones** (integridad, impacto, factibilidad) **no son tasks separados**: viven dentro del `output` del task `FI - Agente validador de Intents`, en `data.output_validador_intent.{agente_evaluador_integridad, agente_evaluador_impacto, agente_factibilidad_tecnica}`. La clasificación FastGate vive en el `output` del task `FI Fast Gate Google` (`data.output_fast_gate`).

### Shape real de un flow (verificado 2026-05-27)

Mapeo concreto que usa `RemoteAgentClient.get_trace()` (SPEC-007 FR-006):

| Dato | Clave real en el flow |
|------|-----------------------|
| Estado general del flow | `state` (ej. `"completed"`) — **no** `status` |
| Pasos ejecutados | `tasks` (lista de dicts) |
| Orden de ejecución | `sequence.steps` (lista de grupos de nombres, ej. `[["cargar_iniciativa_v2"], ["FI - Agente validador de Intents"], …]`) |
| ID del flow | `instance_id` |
| Sub-flows anidados | `children` (recursivo, mismo shape) |

Y dentro de cada item de `tasks`:

| Dato | Clave real en la task |
|------|-----------------------|
| Nombre del paso | `name` |
| Estado del paso | `state` (ej. `"completed"`) — **no** `status` |
| ID del paso | `task_instance_id` |
| Input / Output | `input` / `output` (dicts; `input` suele venir `{}`) |
| Duración | `trace_context.duration_ms` (entero, ms) — los `created_at`/`updated_at` son del **registro**, no del span de ejecución |

`tasks` viene **desordenado**; el orden de ejecución se reconstruye con `sequence.steps`.

### Filtro para obtener el flow externo

```python
trigger == "flow_async_chat"
AND agent_id == AGENT_ID
# se toma el más reciente por `created_at` (top-level, ISO).
# correlación exacta por run_id pendiente de verificar (ver SPEC-007 FR-008)
```

---

## 7. Dónde vive cada dato

| Dato | Cómo obtenerlo |
|------|----------------|
| `thread_id` de conversación | `data["thread_id"]` en el body del POST inicial |
| `run_id` de ejecución | `data["run_id"]` en el body del POST inicial |
| Esperar que el agente termine | `GET /threads/{thread_id}/messages` → polling hasta msg `role=assistant` sin "A new flow" |
| Clasificación (`riesgo: VERDE`) | Mismo endpoint — primer mensaje `role=assistant` con patrón `riesgo:` |
| Detección de RECHAZADO | Mismo endpoint — `ClassificationEvaluator.extract()` sobre el contenido crudo |
| Traza interna (pasos, estado, duraciones) | `GET /flows` → flow más reciente por `created_at` → `tasks` ordenados por `sequence.steps` (SPEC-007) |
| Detalle de sub-evaluaciones | `GET /flows` → task `FI - Agente validador de Intents` → `output.data.output_validador_intent` |

---

## 8. Comportamientos que NO tiene el agente

- No devuelve la clasificación inline en el POST (siempre devuelve el control message).
- No soporta GET de mensajes con `agent_id` en el path — `/threads/{id}/messages` opera a nivel de instancia.
- No responde a un segundo mensaje en el thread con el resultado del flow anterior — lo interpreta como nuevo intent y lanza un flow nuevo.
- El `thread_id` del cliente **no es igual** al `agent_thread_id` del flow — no usar para correlacionar con `/flows`.
