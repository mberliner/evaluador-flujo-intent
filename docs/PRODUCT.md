# PRODUCT — Qué mide la suite y por qué

SSOT del propósito y las métricas del sistema.

## Problema

Tenemos un agente de clasificación que categoriza iniciativas de IA en cuatro niveles de riesgo (**Verde / Amarillo / Rojo / Negro**), más el resultado **Rechazado** para los casos que no admite. Hoy no existe un mecanismo sistemático para:

1. Detectar regresiones cuando se ajusta el prompt o la configuración del agente.
2. Comparar el comportamiento del agente entre versiones / proveedores.
3. Identificar zonas del dominio donde el agente es débil (qué tipo de iniciativas confunde).

## Solución

Suite de test automatizado que cubre dos modos de uso, entregados de forma iterativa:

### Modo simple (primero)

1. Usuario carga **un caso por pantalla** (formulario en el dashboard).
2. La suite lo envía al agente bajo test (vía el cliente de agente remoto).
3. Extrae la clasificación de la respuesta y la compara con la esperada (también ingresada por pantalla).
4. Muestra pass/fail + respuesta cruda en pantalla.

### Modo batch (posterior)

1. Usuario carga un **archivo de casos** vía una interfaz estable (file uploader o ruta local elegida).
2. La suite ejecuta todos los casos.
3. Reporta accuracy global, matriz de confusión y detalle por caso.
4. Persiste cada run en `runs/` para comparativa histórica.

## Política de datos

Los datasets **no se versionan en el proyecto**: cada ejecución carga los datos vía la interfaz correspondiente al modo elegido. El detalle (referencias externas, qué carga cada modo, `data/.gitkeep`) es SSOT en `docs/ARCHITECTURE.md` §ADR-002.

## Métricas

| Métrica | Definición | Objetivo |
|---|---|---|
| Accuracy global (bruta) | `pass / total` — los Indeterminados (sin clasificación extraíble) cuentan como fallo (denominador = total) | A fijar con baseline real |
| Accuracy efectiva | `pass / (total − indeterminado)` — excluye los Indeterminados del denominador; `null` si el denominador es 0 | A fijar con baseline real |
| Accuracy por clase | Accuracy sobre los casos cuyo expected es esa clase | ≥ accuracy global − 10pp |
| Matriz de confusión | 5×6: filas = 5 clases (Verde, Amarillo, Rojo, Negro, Rechazado); columnas = esas 5 + `Sin clasificación` (predicted vacío) | Reportada cada run |
| Casos sin clasificación extraíble | Respuestas donde el regex no encontró ningún color | < 5% |

## No-objetivos

- **No** evaluamos la calidad de las justificaciones del agente, solo la clasificación final.
- **No** hacemos LLM-as-judge en esta versión: la respuesta válida es única y exacta.
- **No** medimos latencia ni costo en esta versión (puede agregarse en iteraciones futuras).

## Casos de uso

1. **Regresión tras cambio de prompt del agente**: correr suite antes y después, comparar runs.
2. **Comparación de agentes**: cambiar `AGENT_ID`, correr suite, comparar.
3. **Análisis de debilidades**: revisar matriz de confusión para identificar pares (expected, predicted) frecuentes y ajustar el prompt del agente o el dataset.

## Referencia del schema

- Plantilla de los campos del caso (form): el JSON ubicado en el workspace padre como modelo de la interfaz que el agente espera.
- Ejemplo poblado con ground truth: el CSV ubicado en el workspace padre, útil para construir casos de prueba reales.

Su rol (referencia de schema, no fuente operativa) y su no-versionado están detallados en `docs/ARCHITECTURE.md` §ADR-002.
