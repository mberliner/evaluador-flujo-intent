# agent-test-suite

Suite de pruebas para un **agente de clasificación de iniciativas de IA**. Envía casos al agente, extrae la clasificación que devuelve y la compara contra el resultado esperado para medir su accuracy y detectar regresiones.

El agente clasifica cada iniciativa en uno de cuatro niveles de riesgo — **Verde / Amarillo / Rojo / Negro** — o la marca como **Rechazado** si no la admite.

---

## Inicio rápido

```bash
pip install -r requirements.txt
cp .env.example .env       # completar credenciales (ver abajo)
streamlit run src/dashboard/app.py
```

Abre el navegador en `http://localhost:8501`.

> **Entorno virtual (opcional):** si preferís aislar dependencias, creá el venv primero con `python -m venv .venv && source .venv/bin/activate` (o `.venv\Scripts\activate` en Windows) y luego seguí los pasos de arriba.

---

## Credenciales (`.env`)

| Variable | Qué poner |
|---|---|
| `ES_URL_CHAT` | URL base del endpoint de chat — reemplazar `<instance-id>` con el ID real de la instancia |
| `ES_URL_TOKEN` | URL de obtención de token (generalmente no cambia) |
| `ES_AGENTS_URL` | URL para listar agentes — mismo `<instance-id>` que arriba |
| `ES_TOKEN` | API key de entorno de agente a probar |
| `AGENT_ID` | ID del agente a probar (formato UUID) |
| `ACCURACY_THRESHOLD` | Umbral de accuracy para el runner headless (opcional, default `0.0`) |

---

## Para qué sirve

- **Detectar regresiones** — correr la suite antes y después de cambiar el prompt y comparar resultados.
- **Comparar versiones del agente** — cambiar `AGENT_ID` y medir cuál clasifica mejor.
- **Encontrar debilidades** — ver en una matriz de confusión qué tipos de iniciativa confunde el agente.

---

## Dos modos de uso

### Modo simple — un caso por vez

Completá el formulario con los datos de la iniciativa y hacé clic en **Enviar al agente**. La interfaz muestra el veredicto (acertó / falló / indeterminado), la respuesta cruda del agente y la traza de ejecución interna.

También podés cargar el caso desde un archivo JSON en vez de tipear el formulario.

### Modo batch — muchos casos a la vez

Cargá un CSV con todos los casos de prueba. La interfaz ejecuta cada uno, muestra el progreso en vivo y al terminar presenta accuracy global, detalle por caso y la matriz de confusión 5×6 (5 clases esperadas × esas 5 + `Sin clasificación`). Cada corrida queda guardada en `runs/` para comparar contra corridas anteriores.

Para correr el batch sin interfaz:

```bash
python -m src.runner --in data/mis_casos.csv --out runs/
```

El CSV acepta separador `;` o `,`. Las filas inválidas se reportan y se omiten sin abortar la corrida.

---

## Documentación

| Tema | Documento |
|---|---|
| Propósito y métricas | [docs/PRODUCT.md](docs/PRODUCT.md) |
| Arquitectura y decisiones de diseño | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Conexión y flujo de mensajes con el agente | [docs/AGENT-INVOCATION.md](docs/AGENT-INVOCATION.md) |
| Setup de desarrollo y comandos | [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) |
| Workflow y commits | [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) |
| Estado por capacidad (specs vivas) | [specs/SPECS_REGISTRY.md](specs/SPECS_REGISTRY.md) |
| Navegación completa del proyecto | [00-INDEX.md](00-INDEX.md) |
