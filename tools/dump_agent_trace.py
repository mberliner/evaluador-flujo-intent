"""Vuelca el JSON crudo de GET /flows para inspeccionar el shape real.

Sirve para mapear correctamente la traza (SPEC-007): muestra que claves y que
valores de estado devuelve realmente el proveedor, sin transformarlos. Usalo
despues de enviar un caso real desde el dashboard.

Uso:
    python tools/dump_agent_trace.py            # imprime el flow mas reciente del agente
    python tools/dump_agent_trace.py --all      # imprime TODOS los flows que devuelve /flows
    python tools/dump_agent_trace.py --keys      # solo lista las claves de cada nivel (compacto)

Exit 0 si pudo consultar; != 0 ante fallo de auth o red.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import requests  # noqa: E402

from src.adapters.platform_config import MissingConfigError, PlatformConfig  # noqa: E402
from src.adapters.token_provider import TokenError, TokenProvider  # noqa: E402

_OUTER_FLOW_TRIGGER = "flow_async_chat"


def _fetch_flows(config: PlatformConfig, token: str) -> list[dict[str, Any]]:
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(config.flows_url, headers=headers, params={"limit": "50"}, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"/flows fallo: {response.status_code} - {response.text[:400]}")
    data: Any = response.json()
    if isinstance(data, list):
        return [f for f in data if isinstance(f, dict)]
    if isinstance(data, dict):
        flows = data.get("flows", [])
        return [f for f in flows if isinstance(f, dict)] if isinstance(flows, list) else []
    return []


def _print_keys(value: Any, prefix: str = "", depth: int = 0) -> None:
    """Imprime las claves de cada nivel del objeto, acotando recursion."""
    pad = "  " * depth
    if isinstance(value, dict):
        for key, sub in value.items():
            kind = type(sub).__name__
            print(f"{pad}{prefix}{key}  ({kind})")
            if depth < 4 and isinstance(sub, dict | list):
                _print_keys(sub, "", depth + 1)
    elif isinstance(value, list):
        print(f"{pad}[lista de {len(value)} item(s)]")
        if value and depth < 4:
            _print_keys(value[0], "", depth + 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--all", action="store_true", help="Imprime todos los flows, sin filtrar.")
    parser.add_argument(
        "--keys", action="store_true", help="Solo lista las claves por nivel (compacto)."
    )
    args = parser.parse_args()

    try:
        config = PlatformConfig.from_env()
    except MissingConfigError as err:
        print(f"[ERROR] Config: {err}", file=sys.stderr)
        return 10

    try:
        token = TokenProvider(config).get()
    except TokenError as err:
        print(f"[ERROR] Token: {err}", file=sys.stderr)
        return 20

    try:
        flows = _fetch_flows(config, token)
    except (requests.RequestException, RuntimeError) as err:
        print(f"[ERROR] {err}", file=sys.stderr)
        return 30

    print(f"[info] /flows devolvio {len(flows)} flow(s).", file=sys.stderr)

    if not args.all:
        candidates = [
            f
            for f in flows
            if f.get("trigger") == _OUTER_FLOW_TRIGGER and f.get("agent_id") == config.agent_id
        ]
        pool = candidates or flows
        flows = [pool[-1]] if pool else []
        print(
            f"[info] Filtrado a {len(flows)} flow (mas reciente del agente). "
            "Usa --all para ver todos.",
            file=sys.stderr,
        )

    if args.keys:
        for i, flow in enumerate(flows):
            print(f"\n=== flow #{i} (trigger={flow.get('trigger')}) ===")
            _print_keys(flow)
    else:
        print(json.dumps(flows, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
