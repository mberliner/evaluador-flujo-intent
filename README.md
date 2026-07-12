# agent-test-suite

Suite de pruebas para un **agente de clasificación de iniciativas de IA**. Enviará casos al agente, extraerá la clasificación que devuelve y la comparará contra el resultado esperado para medir su accuracy y detectar regresiones.

El agente clasifica cada iniciativa en uno de cuatro niveles de riesgo — **Verde / Amarillo / Rojo / Negro** — o la marca como **Rechazado** si no la admite.

> **Estado:** proyecto recién bootstrapeado (Iter 0 cerrada). La estructura, el tooling de calidad y las specs base están listos; la primera capacidad funcional se implementa en la próxima iteración.

---

## Inicio rápido

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env       # completar credenciales (ver abajo)
```

> **Entorno virtual (opcional):** si preferís aislar dependencias, creá el venv primero con `python -m venv .venv && source .venv/bin/activate` (o `.venv\Scripts\activate` en Windows) y luego seguí los pasos de arriba.

---

## Credenciales (`.env`)

| Variable | Qué poner |
|---|---|
| `ES_URL_CHAT` | URL base del endpoint de chat — reemplazar `<instance-id>` con el ID real de la instancia |
| `ES_URL_TOKEN` | URL de obtención de token (generalmente no cambia) |
| `ES_TOKEN` | API key de entorno de agente a probar |
| `AGENT_ID` | ID del agente a probar (formato UUID) |

---

## Para qué sirve

- **Detectar regresiones** — correr la suite antes y después de cambiar el prompt y comparar resultados.
- **Comparar versiones del agente** — cambiar `AGENT_ID` y medir cuál clasifica mejor.
- **Encontrar debilidades** — identificar qué tipos de iniciativa confunde el agente.

El detalle del producto (modos de uso previstos y métricas) es SSOT de [docs/PRODUCT.md](docs/PRODUCT.md).

---

## Documentación

| Tema | Documento |
|---|---|
| Propósito y métricas | [docs/PRODUCT.md](docs/PRODUCT.md) |
| Arquitectura y decisiones de diseño | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Setup de desarrollo y comandos | [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) |
| Workflow y commits | [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) |
| Estado por capacidad (specs vivas) | [specs/SPECS_REGISTRY.md](specs/SPECS_REGISTRY.md) |
| Navegación completa del proyecto | [00-INDEX.md](00-INDEX.md) |
