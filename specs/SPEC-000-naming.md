# SPEC-000-naming — Nomenclatura agnóstica a tecnología

**Estado:** active
**Iter:** 0
**Tipo:** Regla transversal (aplica a todas las specs siguientes)

## Propósito

Garantizar que el código del proyecto sea **portable y resiliente al cambio de proveedor, framework o formato**. Los nombres del dominio describen *qué* hace el sistema, no *con qué* lo hace.

## Regla

Ningún identificador (módulo, paquete, clase, función, método, variable, atributo, archivo de código, archivo de documentación interna, símbolo público) puede contener referencias a:

- **Proveedor / plataforma**: `watson`, `orchestrate`, `ibm`, `azure`, `aws`, `openai`, `anthropic`, `bedrock`.
- **Framework de UI**: `streamlit`, `flask`, `fastapi`, `django`, `gradio`.
- **Formato de almacenamiento o serialización**: `json`, `csv`, `xml`, `yaml`, `parquet` (salvo en utilidades de bajo nivel que sí los manejan, donde el formato es la razón de ser del módulo — y aun así se prefiere el nombre semántico, ver "Excepciones").
- **Protocolo o herramienta de auth**: `oauth`, `iam`, `jwt`, `apikey`.

## Forma correcta

| En lugar de... | Usar... | Razón |
|---|---|---|
| `WatsonAgentClient` | `RemoteAgentClient` o `HttpAgentClient` | El proveedor es un detalle del adapter |
| `IamAuthManager` | `TokenProvider` o `CredentialProvider` | El protocolo es un detalle interno |
| `StreamlitApp` | `Dashboard` o `app` (dentro de `dashboard/`) | El framework UI es intercambiable |
| `JsonRepository` | `FileTestCaseRepository` | El formato es un detalle del repositorio |
| `csv_to_json.py` | `dataset_builder.py` | El builder transforma fuentes; los formatos cambian |
| `OauthTokenManager` | `TokenProvider` | Lo relevante es proveer un token |

## Excepciones explícitas

1. **Configuración externa** (`.env`, variables de entorno) **sí** puede usar nombres específicos del proveedor (`ES_URL_CHAT`, `ES_URL_TOKEN`, `AGENT_ID`) porque son contrato con el operador. El código interno las consume vía un `PlatformConfig` agnóstico.
2. **Documentación de adapters concretos** puede mencionar al proveedor en el cuerpo (`docs/ARCHITECTURE.md` puede decir "el `RemoteAgentClient` actual usa Watson Orchestrate") pero **no** en los nombres de archivos de código.
3. **README** y docs de producto pueden mencionar libremente el proveedor, ya que son orientadas al humano.
4. **Métodos que implementan contratos de APIs externas** pueden conservar el nombre del contrato. Caso concreto: el método `.json()` de `requests.Response` es parte de la API pública de la librería `requests`; los stubs de tests que lo reemplazan deben llamarse igual o el código bajo test no los reconoce. Mantener una lista mínima de **identificadores explícitamente permitidos** en `tools/check_naming.py` (constante `ALLOWED_IDENTIFIERS`) sincronizada con esta sección.

### Identificadores permitidos (sincronizar con `tools/check_naming.py`)

| Identificador | Motivo |
|---|---|
| `json` | Contrato de `requests.Response.json()` reutilizado por stubs de test. |

## Verificación

- **Code review**: cada PR revisa nombres introducidos contra la lista prohibida.
- **Linter automático** (a construir en Iter 0 o Iter 1): script `tools/check_naming.py` que recorre `src/` con AST y falla si encuentra identificadores con substrings prohibidos (case-insensitive). Bloquea pre-commit.
- **Lista de tokens prohibidos** (canónica, mantener aquí y sincronizar con `tools/check_naming.py:PROHIBITED_TOKENS`):
  - Proveedor/plataforma: `watson`, `orchestrate`, `ibm`, `azure`, `aws`, `openai`, `anthropic`, `bedrock`
  - Framework UI: `streamlit`, `flask`, `fastapi`, `django`, `gradio`
  - Formato: `csv`, `json`, `xml`, `yaml`, `parquet`
  - Auth: `oauth`, `iam`, `jwt`, `apikey`

## Criterios de aceptación

- [x] El linter de naming existe (`tools/check_naming.py`) y pasa en verde sobre `src/`, `tests/` y `tools/`.
- [ ] El linter corre en pre-commit (pendiente: requiere `git init`).
- [x] El registro de tokens prohibidos vive en este archivo y se referencia desde el linter (`SPEC-000-naming.md` línea 3 de `check_naming.py`).
- [x] `docs/ARCHITECTURE.md` describe cómo `RemoteAgentClient` aísla al proveedor (sección `src/adapters/`).
- [x] Excepciones documentadas registradas en este archivo bajo "Excepciones explícitas" (`json`, `_serializer`, métodos de `requests`).

## Historial

- **Iter 0** — Spec creada. Motivación: el usuario explicitó que los nombres deben ser agnósticos a tecnologías o herramientas, y esto debe ser parte de la spec.
