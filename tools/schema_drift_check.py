"""Verifica drift de contrato entre un agente y el schema versionado del proyecto.

Compara, de forma ESTATICA (lee la configuracion del agente, no lo ejecuta), el
bloque de formato de salida embebido en las `instructions` del agente contra un
archivo de schema local (por defecto `schemas/FI_Orquestador_Input.schema.json`).

Util para detectar que el contrato de un agente (ej. el traductor de intents, que
declara su formato de salida en el prompt) divergio del schema que la suite versiona.

Uso:
    python tools/schema_drift_check.py [--agent-name FRAG] [--schema RUTA] [--dump]

Exit codes:
    0  identidad exacta (sin drift)
    1  hay diferencias (drift detectado)
    2  error operativo (config, agente no encontrado, bloque no extraible)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# Permite ejecutar el script directamente o como modulo.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import json as _serializer  # API estandar de Python (ver SPEC-000-naming, allowlist)  # noqa: E402

import requests  # noqa: E402

from src.adapters.platform_config import MissingConfigError, PlatformConfig  # noqa: E402
from src.adapters.token_provider import TokenError, TokenProvider  # noqa: E402

_DEFAULT_AGENT_FRAGMENT = "traductor"
_DEFAULT_SCHEMA = "schemas/FI_Orquestador_Input.schema.json"
_FORMAT_MARKER = "Formato del JSON"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detecta drift entre el formato declarado por un agente y un schema local."
    )
    parser.add_argument(
        "--agent-name",
        default=_DEFAULT_AGENT_FRAGMENT,
        help=(
            "Fragmento (case-insensitive) del nombre del agente cuyo formato declarado se "
            f"compara. Default: '{_DEFAULT_AGENT_FRAGMENT}'."
        ),
    )
    parser.add_argument(
        "--schema",
        default=_DEFAULT_SCHEMA,
        help=f"Ruta al schema local a comparar. Default: '{_DEFAULT_SCHEMA}'.",
    )
    parser.add_argument(
        "--marker",
        default=_FORMAT_MARKER,
        help=(
            "Texto que antecede al bloque de formato en las instrucciones del agente. "
            f"Default: '{_FORMAT_MARKER}'."
        ),
    )
    parser.add_argument(
        "--dump",
        action="store_true",
        help="Vuelca el bloque extraido del agente a runs/ para inspeccion.",
    )
    return parser.parse_args(argv)


def fetch_agent_instructions(cfg: PlatformConfig, token: str, name_fragment: str) -> str:
    """Devuelve las `instructions` del primer agente cuyo nombre contiene el fragmento."""
    response = requests.get(
        cfg.agents_url, headers={"Authorization": f"Bearer {token}"}, timeout=40
    )
    response.raise_for_status()
    needle = name_fragment.lower()
    for agent in response.json():
        if isinstance(agent, dict) and needle in str(agent.get("name", "")).lower():
            return str(agent.get("instructions", ""))
    raise LookupError(f"No se encontro un agente cuyo nombre contenga '{name_fragment}'.")


def extract_format_block(text: str, marker: str) -> dict[str, Any]:
    """Extrae el objeto balanceado que sigue al marcador de formato (cuenta llaves)."""
    marker_at = text.find(marker)
    search_from = marker_at if marker_at != -1 else 0
    start = text.find("{", search_from)
    if start == -1:
        raise ValueError("No hay bloque '{...}' tras el marcador de formato.")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return _serializer.loads(text[start : i + 1])
    raise ValueError("El bloque de formato no cierra (llaves desbalanceadas).")


def _normalize(obj: Any) -> Any:
    """Normaliza recursivamente para comparar ignorando orden de claves."""
    if isinstance(obj, dict):
        return {k: _normalize(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [_normalize(v) for v in obj]
    return obj


def collect_diffs(path: str, agent: Any, schema: Any, out: list[str]) -> None:
    """Acumula diferencias entre el bloque del agente y el schema local."""
    if isinstance(agent, dict) and isinstance(schema, dict):
        for key in sorted(set(agent) | set(schema)):
            if key not in agent:
                out.append(f"{path}.{key}: FALTA en agente (esta en schema)")
            elif key not in schema:
                out.append(f"{path}.{key}: SOBRA en agente (no esta en schema)")
            else:
                collect_diffs(f"{path}.{key}", agent[key], schema[key], out)
    elif agent != schema:
        out.append(f"{path}: agente={agent!r}  vs  schema={schema!r}")


def _form_keys(block: dict[str, Any]) -> set[str]:
    form = block.get("form", {})
    props = form.get("properties", {}) if isinstance(form, dict) else {}
    return set(props.keys()) if isinstance(props, dict) else set()


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    try:
        cfg = PlatformConfig.from_env()
    except MissingConfigError as err:
        print(f"[ERROR] Config: {err}", file=sys.stderr)
        return 2

    try:
        token = TokenProvider(cfg).get()
    except TokenError as err:
        print(f"[ERROR] Token: {err}", file=sys.stderr)
        return 2

    try:
        instructions = fetch_agent_instructions(cfg, token, args.agent_name)
    except (requests.RequestException, LookupError) as err:
        print(f"[ERROR] Instrucciones del agente: {err}", file=sys.stderr)
        return 2

    try:
        agent_block = extract_format_block(instructions, args.marker)
    except (ValueError, _serializer.JSONDecodeError) as err:
        print(f"[ERROR] No se pudo extraer el bloque de formato del agente: {err}", file=sys.stderr)
        return 2

    schema_path = Path(args.schema)
    if not schema_path.is_absolute():
        schema_path = _PROJECT_ROOT / schema_path
    try:
        schema_block = _serializer.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, _serializer.JSONDecodeError) as err:
        print(f"[ERROR] No se pudo leer el schema '{schema_path}': {err}", file=sys.stderr)
        return 2

    print(f"[ok] Agente '{args.agent_name}' vs schema '{args.schema}'")

    if args.dump:
        dump = _PROJECT_ROOT / "runs" / "agent-format-block.json"
        dump.parent.mkdir(parents=True, exist_ok=True)
        dump.write_text(
            _serializer.dumps(agent_block, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[ok] Bloque del agente volcado en: {dump}")

    agent_keys = _form_keys(agent_block)
    schema_keys = _form_keys(schema_block)
    print(f"[..] Claves form — agente: {len(agent_keys)} | schema: {len(schema_keys)}")
    missing = sorted(schema_keys - agent_keys)
    extra = sorted(agent_keys - schema_keys)
    if missing:
        print(f"     Faltan en agente: {missing}")
    if extra:
        print(f"     Sobran en agente: {extra}")

    diffs: list[str] = []
    collect_diffs("form", _normalize(agent_block), _normalize(schema_block), diffs)

    if not diffs:
        print("[ok] IDENTIDAD EXACTA — sin drift de contrato.")
        return 0

    print(f"[DRIFT] {len(diffs)} diferencia(s) entre el agente y el schema:", file=sys.stderr)
    for diff in diffs:
        print(f"   - {diff}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
