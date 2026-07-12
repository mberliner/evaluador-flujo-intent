# IDEAS — Registro de ideas y mejoras futuras

Este documento es el SSOT (Single Source of Truth) para almacenar ideas, propuestas y mejoras arquitectónicas, técnicas o funcionales que **aún no han sido formalizadas ni priorizadas**. Lo ya formalizado vive en [`specs/SPECS_REGISTRY.md`](../specs/SPECS_REGISTRY.md) (qué se especificó) y su priorización por iteración en el "Roadmap de iteraciones" del registro.

Cuando una idea se promueve a spec (aunque sea `draft`), su alcance, criterios y decisiones pasan a ser SSOT de la spec: acá queda solo como **puntero dentro de su categoría**, sin re-describir el alcance (eso evita duplicar SSOT y que esta lista diverja). Las entradas marcadas **(ya con spec)** son ese puntero; las demás son ideas crudas todavía sin spec.

## 1. Mejoras Funcionales (Impacto en usuario y producto)

- **Gestión Visual e Histórico en Dashboard:** Añadir vistas en la interfaz para comparar visualmente el *accuracy* a lo largo del tiempo o entre diferentes modelos de agentes (A/B testing), sin requerir análisis manual de los archivos de resultados.
- **Agendamiento Desatendido:** Integrar capacidades para que la suite de pruebas corra de manera agendada o como parte continua de CI/CD para monitorear el "health" del agente.
- **Selección del agente bajo prueba (perfiles)** — **(ya con spec)** → [SPEC-011-agent-under-test](../specs/SPEC-011-agent-under-test.md) (draft).
- **Evaluador de traducción de intents** — **(ya con spec)** → [SPEC-012-translation-evaluator](../specs/SPEC-012-translation-evaluator.md) (draft).

## 2. Mejoras Técnicas (Performance, código y testing)

- **Grabación/reproducción de casetes para CI offline:** Grabar las respuestas del API real (casetes) en los tests marcados como `smoke` para permitir corridas de CI/CD rápidas, offline y deterministas sin modificar los adaptadores. (Herramienta candidata: `vcrpy`, a justificar en `docs/DEVELOPMENT.md` si se adopta.)
- **Resguardo robusto del estado de corridas batch en la UI:** Optimizar el resguardo del progreso (estado de sesión o workers en background) de corridas batch pesadas en la interfaz, previniendo que un *re-render* del framework de UI destruya los datos de una iteración en curso.
- **Ejecución paralela / concurrencia configurable** — **(ya con spec)** → [SPEC-009-parallel-execution](../specs/SPEC-009-parallel-execution.md) (draft).

## 3. Mejoras Arquitecturales (Escalabilidad y diseño)

- **Repositorio estructurado de corridas (`DatabaseRunRepository`):** Evolucionar `FileRunRepository` a una implementación respaldada por una base de datos relacional para poder ejecutar consultas y reportes complejos sin parsear archivos de resultados. (Tecnología candidata a evaluar al especificar; el identificador debe permanecer agnóstico — SPEC-000-naming.)
- **Desacoplamiento cliente-servidor de la interfaz:** Aislar la capa `application` y el runner tras una API (p. ej. REST), dejando al frontend como cliente reactivo (vía websockets o polling). Esto permitiría lanzar batch tests de forma segura y desatendida desde cualquier cliente o webhook.
