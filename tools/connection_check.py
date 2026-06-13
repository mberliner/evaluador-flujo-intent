"""Smoke de conexion: prueba auth + envio minimo al agente bajo test.

Uso:
    python tools/connection_check.py [--list-agents] [--prompt "texto"]

Exit code 0 si todo OK, != 0 si algo falla. Imprime el contenido de la
respuesta del agente o el error legible.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Permite ejecutar el script directamente (python tools/connection_check.py)
# o como modulo (python -m tools.connection_check) sin diferencia.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import requests  # noqa: E402

from src.adapters.platform_config import MissingConfigError, PlatformConfig  # noqa: E402
from src.adapters.remote_agent_client import RemoteAgentClient  # noqa: E402
from src.adapters.token_provider import TokenError, TokenProvider  # noqa: E402


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke de conexion al agente bajo test.")
    parser.add_argument(
        "--prompt",
        default="ping de smoke",
        help="Prompt a enviar al agente (default: 'ping de smoke').",
    )
    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="Lista los agentes disponibles y verifica que AGENT_ID figura.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Con --list-agents, imprime el JSON crudo (todos los campos).",
    )
    parser.add_argument(
        "--brief",
        action="store_true",
        help="Con --list-agents, imprime solo name e id (vista simple).",
    )
    parser.add_argument(
        "--only-list",
        action="store_true",
        help="Solo lista agentes; no envia prompt de smoke.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout en segundos para el envio (default: 60).",
    )
    return parser.parse_args(argv)


def _find_id_in_obj(obj: object, target: str, path: str = "") -> list[str]:
    """Busca recursivamente `target` como valor en cualquier campo. Devuelve paths."""
    matches: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}.{k}" if path else k
            if isinstance(v, str) and v == target:
                matches.append(new_path)
            else:
                matches.extend(_find_id_in_obj(v, target, new_path))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            matches.extend(_find_id_in_obj(v, target, f"{path}[{i}]"))
    return matches


def _list_and_verify_agents(
    config: PlatformConfig, token: str, *, raw: bool = False, brief: bool = False
) -> int:
    import json as _json

    headers = {"Authorization": f"Bearer {token}"}
    print(f"[..] GET {config.agents_url}")
    response = requests.get(config.agents_url, headers=headers, timeout=40)
    if response.status_code != 200:
        print(
            f"[ERROR] Listado de agentes fallo: {response.status_code} - {response.text[:400]}",
            file=sys.stderr,
        )
        request_id = response.headers.get("x-request-id") or response.headers.get(
            "X-Global-Transaction-ID"
        )
        if request_id:
            print(f"[info] request id devuelto por el server: {request_id}", file=sys.stderr)
        return 2

    agents = response.json()
    if not isinstance(agents, list):
        print(f"[ERROR] Respuesta inesperada en listado: {type(agents).__name__}", file=sys.stderr)
        return 2

    ids = [a.get("id") for a in agents if isinstance(a, dict)]
    print(f"[ok] {len(agents)} agente(s) disponibles.")

    if raw:
        print("[raw] JSON crudo:")
        print(_json.dumps(agents, indent=2, ensure_ascii=False))
    elif brief:
        for agent in agents:
            if isinstance(agent, dict):
                display = agent.get("display_name") or "-"
                print(
                    f"   - display_name={display!r}  name={agent.get('name', '?')}  "
                    f"id={agent.get('id', '?')}"
                )
    else:
        for agent in agents:
            if isinstance(agent, dict):
                extra_keys = [k for k in agent if k not in {"name", "id", "display_name"}]
                display = agent.get("display_name") or "-"
                print(
                    f"   - display_name={display!r}  name={agent.get('name', '?')}  "
                    f"id={agent.get('id', '?')}  otros_campos={extra_keys}"
                )

    # Busca el agent_id configurado en cualquier campo (no solo 'id').
    paths = _find_id_in_obj(agents, config.agent_id)
    if paths:
        print(f"[info] AGENT_ID '{config.agent_id}' aparece en: {paths}")
    else:
        print(f"[info] AGENT_ID '{config.agent_id}' NO aparece en ningun campo de la lista.")

    if config.agent_id not in ids:
        print(
            f"[ERROR] AGENT_ID configurado '{config.agent_id}' no figura como 'id' "
            "principal entre los agentes disponibles.",
            file=sys.stderr,
        )
        return 3

    print(f"[ok] AGENT_ID '{config.agent_id}' presente en la lista.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    try:
        config = PlatformConfig.from_env()
    except MissingConfigError as err:
        print(f"[ERROR] Config: {err}", file=sys.stderr)
        return 10

    print(f"[ok] Config cargada (agent_id={config.agent_id})")

    credentials = TokenProvider(config)
    try:
        token = credentials.get()
    except TokenError as err:
        print(f"[ERROR] Token: {err}", file=sys.stderr)
        return 20

    print(f"[ok] Token obtenido (longitud={len(token)})")

    if args.list_agents:
        code = _list_and_verify_agents(config, token, raw=args.raw, brief=args.brief)
        if code != 0:
            return code

    if args.only_list:
        return 0

    client = RemoteAgentClient(config, credentials, timeout_seconds=args.timeout)
    print(f"[..] Enviando prompt: {args.prompt!r}")
    response = client.send(args.prompt)

    if response.content.startswith(("Error API:", "Error conexion:", "Respuesta sin formato")):
        print(f"[ERROR] Envio fallo: {response.content}", file=sys.stderr)
        return 30

    print(f"[ok] Respuesta recibida (conversation_id={response.conversation_id}):")
    print("---")
    print(response.content)
    print("---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
