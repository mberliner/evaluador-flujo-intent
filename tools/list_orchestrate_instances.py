"""Lista las instancias de watsonx Orchestrate visibles para la API key actual.

Consulta el IBM Cloud Resource Controller y filtra por servicios cuyo CRN
referencie 'watson-orchestrate' o 'watsonx-orchestrate'. Util para confirmar
en que instancia (y region) vive el agente que se quiere testear.

Uso:
    python tools/list_orchestrate_instances.py [--all]

  --all  imprime TODAS las instancias visibles (sin filtrar por Orchestrate),
         util para diagnosticar si la API key tiene permisos de Resource
         Controller. Si esta lista tambien viene vacia, la key no es de
         cuenta IAM sino una key de servicio de Orchestrate.

Exit 0 si pudo listar; != 0 ante fallo de auth o red.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import requests  # noqa: E402

from src.adapters.platform_config import MissingConfigError, PlatformConfig  # noqa: E402
from src.adapters.token_provider import TokenError, TokenProvider  # noqa: E402

RESOURCE_CONTROLLER_URL = "https://resource-controller.cloud.ibm.com/v2/resource_instances"
ORCHESTRATE_CRN_HINTS = ("watson-orchestrate", "watsonx-orchestrate")


def _fetch_all_instances(token: str) -> list[dict]:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    results: list[dict] = []
    url: str | None = RESOURCE_CONTROLLER_URL
    params: dict[str, str] | None = {"limit": "100"}

    while url:
        response = requests.get(url, headers=headers, params=params, timeout=40)
        if response.status_code != 200:
            raise RuntimeError(
                f"Resource Controller fallo: {response.status_code} - {response.text[:400]}"
            )
        data = response.json()
        results.extend(data.get("resources", []))
        next_url = data.get("next_url")
        if next_url:
            url = f"https://resource-controller.cloud.ibm.com{next_url}"
            params = None
        else:
            url = None
    return results


def _is_orchestrate(instance: dict) -> bool:
    crn = instance.get("crn", "")
    return any(hint in crn for hint in ORCHESTRATE_CRN_HINTS)


def _region_from_crn(crn: str) -> str:
    parts = crn.split(":")
    return parts[5] if len(parts) > 5 else "?"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--all",
        action="store_true",
        help="No filtrar por Orchestrate; mostrar TODAS las instancias visibles.",
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
        instances = _fetch_all_instances(token)
    except (requests.RequestException, RuntimeError) as err:
        print(f"[ERROR] {err}", file=sys.stderr)
        return 30

    print(f"[info] Resource Controller devolvio {len(instances)} instancia(s) en total.")

    orchestrate = instances if args.all else [i for i in instances if _is_orchestrate(i)]

    if not orchestrate:
        if instances:
            print(
                "[warn] No hay instancias de Orchestrate, pero la key SI ve otras "
                "instancias en la cuenta. Probable cuenta distinta o el CRN usa "
                "otro service-name. Reintenta con --all para ver todo."
            )
        else:
            print(
                "[warn] La API key no ve NINGUNA instancia. Probablemente sea una "
                "API key de servicio de Orchestrate (no de cuenta IAM). Para listar "
                "instancias necesitas una API key creada en "
                "https://cloud.ibm.com/iam/apikeys."
            )
        return 0

    label = "instancia(s)" if args.all else "instancia(s) de Orchestrate"
    print(f"[ok] {len(orchestrate)} {label} visibles:\n")
    configured_id = config.agent_id  # solo para referencia
    for inst in orchestrate:
        guid = inst.get("guid", "?")
        name = inst.get("name", "?")
        crn = inst.get("crn", "?")
        state = inst.get("state", "?")
        region = _region_from_crn(crn)
        print(f"- {name}")
        print(f"    region : {region}")
        print(f"    guid   : {guid}")
        print(f"    state  : {state}")
        print(f"    crn    : {crn}")
        print()

    print(f"[info] AGENT_ID configurado en .env: {configured_id}")
    print(
        "[info] El instance-id que figura en ES_URL_CHAT/ES_AGENTS_URL debe coincidir "
        "con el 'guid' de la instancia donde creaste el agente."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
