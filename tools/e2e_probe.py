"""Prueba end-to-end de un caso del intake contra el agente real.

Flujo:
  1. Lee intake_clasificacion.json y elige un caso (default: TC-V-01).
  2. Envia el form completo como JSON al agente via chat/completions.
  3. Captura el conversation_id de la respuesta inmediata.
  4. Hace polling en /flows filtrando por agent_id + agent_thread_id
     hasta que state != "running" o se agota el timeout.
  5. Imprime el output del run y guarda el dump en runs/e2e-<ts>.json.

Uso:
    python tools/e2e_probe.py [--case TC-V-01] [--timeout 300]
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json as _json
import sys
import time
from pathlib import Path

# Fuerza UTF-8 en stdout para que los acentos no revienten en Windows.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import requests  # noqa: E402

from src.adapters.platform_config import MissingConfigError, PlatformConfig  # noqa: E402
from src.adapters.token_provider import TokenError, TokenProvider  # noqa: E402

_INTAKE_FILE = _PROJECT_ROOT.parent / "intake_clasificacion.json"
_POLL_INTERVAL = 10  # segundos entre polls
_RUNS_DIR = _PROJECT_ROOT / "runs"


def _now_iso() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds")


def _load_case(case_id: str) -> dict:
    if not _INTAKE_FILE.exists():
        raise FileNotFoundError(f"No se encontro {_INTAKE_FILE}")
    cases = _json.loads(_INTAKE_FILE.read_text(encoding="utf-8"))
    for c in cases:
        if c.get("id") == case_id:
            return c
    ids = [c.get("id") for c in cases]
    raise ValueError(f"Caso '{case_id}' no encontrado. Disponibles: {ids}")


def _chat_post(
    config: PlatformConfig,
    token: str,
    text: str,
    timeout: int,
    conversation_id: str | None = None,
) -> tuple[str, str | None, dict]:
    """POST a chat/completions. Devuelve (content, conversation_id, raw_data)."""
    payload: dict = {
        "messages": [
            {
                "role": "user",
                "content": [{"response_type": "text", "text": text}],
            }
        ],
        "stream": "false",
    }
    if conversation_id:
        payload["thread_id"] = conversation_id

    url = f"{config.chat_url}{config.agent_id}/chat/completions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    print(f"[..] POST {url}" + (f"  (thread={conversation_id})" if conversation_id else ""))
    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"Chat completions fallo: {resp.status_code} — {resp.text[:400]}")
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    conv_id = data.get("thread_id") if isinstance(data, dict) else None
    return str(content), conv_id, data


def _send_form(
    config: PlatformConfig, token: str, form: dict, timeout: int
) -> tuple[str, str | None]:
    """Envia el form al agente. Devuelve (content_inmediato, conversation_id)."""
    content, conv_id, _ = _chat_post(config, token, _json.dumps(form, ensure_ascii=False), timeout)
    return content, conv_id


def _flows_url(config: PlatformConfig) -> str:
    # chat_url ya tiene trailing slash: https://.../v1/orchestrate/
    base = config.chat_url.rstrip("/")
    # Sube un nivel si termina en el agent path, o usa directamente.
    # El endpoint es /v1/orchestrate/flows, que es el mismo base + /flows.
    return f"{base}/flows"


def _poll_flow(
    config: PlatformConfig,
    token: str,
    conversation_id: str,
    timeout_seconds: int,
) -> dict | None:
    """Hace polling en /flows hasta encontrar el run con agent_thread_id == conversation_id."""
    url = _flows_url(config)
    headers = {"Authorization": f"Bearer {token}"}
    deadline = time.time() + timeout_seconds

    print(f"[..] Polling {url}")
    print(f"     buscando agent_thread_id == {conversation_id!r}")
    print(f"     timeout: {timeout_seconds}s, intervalo: {_POLL_INTERVAL}s")

    while time.time() < deadline:
        resp = requests.get(url, headers=headers, timeout=40, params={"limit": 50})
        if resp.status_code != 200:
            print(f"[warn] GET /flows devolvio {resp.status_code}: {resp.text[:200]}")
            time.sleep(_POLL_INTERVAL)
            continue

        data = resp.json()
        runs = data if isinstance(data, list) else data.get("flows", data.get("runs", []))

        matched = None
        for run in runs:
            meta = run.get("metadata") or {}
            thread_id = meta.get("agent_thread_id") or meta.get("wxo_thread_id")
            # Solo el flow raiz disparado por el chat (no flows anidados).
            if (
                thread_id == conversation_id
                and run.get("agent_id") == config.agent_id
                and run.get("trigger") == "flow_async_chat"
            ):
                matched = run
                break

        if matched is None:
            print(
                f"[..] {_now_iso()} — run no encontrado aun en /flows "
                f"({len(runs)} runs visibles), reintentando..."
            )
            time.sleep(_POLL_INTERVAL)
            continue

        state = matched.get("state", "?")
        print(f"[..] {_now_iso()} — run encontrado, state={state!r}")
        # "interrupted" = flow raiz esperando al flow anidado; sigue corriendo.
        if state not in ("running", "in_progress", "interrupted"):
            return matched

        time.sleep(_POLL_INTERVAL)

    print(f"[warn] Timeout de {timeout_seconds}s agotado sin que el run terminara.")
    return None


def _save(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] Dump guardado en {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prueba e2e de un caso del intake.")
    parser.add_argument("--case", default="TC-V-01", help="ID del caso (default: TC-V-01)")
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout de polling en segundos (default: 300)",
    )
    parser.add_argument(
        "--send-timeout",
        type=int,
        default=60,
        help="Timeout para el POST inicial (default: 60)",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    try:
        config = PlatformConfig.from_env()
    except MissingConfigError as err:
        print(f"[ERROR] Config: {err}", file=sys.stderr)
        return 10

    credentials = TokenProvider(config)
    try:
        token = credentials.get()
    except TokenError as err:
        print(f"[ERROR] Token: {err}", file=sys.stderr)
        return 20

    print(f"[ok] Token obtenido. agent_id={config.agent_id}")

    try:
        case = _load_case(args.case)
    except (FileNotFoundError, ValueError) as err:
        print(f"[ERROR] {err}", file=sys.stderr)
        return 30

    print(f"[ok] Caso cargado: {case['id']} — {case['form'].get('nombre_iniciativa', '?')}")

    ts = _dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    dump: dict = {
        "case_id": case["id"],
        "started_at": _now_iso(),
        "agent_id": config.agent_id,
        "form_sent": case["form"],
    }

    # 1. Enviar el form al agente.
    try:
        immediate_content, conv_id = _send_form(config, token, case["form"], args.send_timeout)
    except Exception as err:
        print(f"[ERROR] Envio fallo: {err}", file=sys.stderr)
        return 40

    dump["immediate_response"] = immediate_content
    dump["conversation_id"] = conv_id

    print(f"[ok] Respuesta inmediata: {immediate_content!r}")
    print(f"[ok] conversation_id: {conv_id!r}")

    if not conv_id:
        print(
            "[ERROR] No se obtuvo conversation_id — no es posible hacer polling.",
            file=sys.stderr,
        )
        _save(dump, _RUNS_DIR / f"e2e-{ts}.json")
        return 50

    # 2. Polling en /flows.
    run = _poll_flow(config, token, conv_id, args.timeout)
    dump["flow_run"] = run

    if run is None:
        print("[ERROR] No se obtuvo resultado dentro del timeout.", file=sys.stderr)
        _save(dump, _RUNS_DIR / f"e2e-{ts}.json")
        return 60

    state = run.get("state", "?")
    output = run.get("output")
    error = run.get("error")
    summary = run.get("execution_summary")

    print("\n" + "=" * 50)
    print("FLOW COMPLETADO (estado interno)")
    print(f"  state            : {state}")
    print(f"  execution_summary: {summary}")
    if error:
        print(f"  error            : {error}")
    if output:
        print("  output (raw flows):")
        print(_json.dumps(output, ensure_ascii=False, indent=4))
    print("=" * 50)

    # 3. Turno final: volver al chat con el mismo thread para obtener la respuesta
    #    del agente (lo que el usuario vería en pantalla).
    if state == "completed":
        print(f"\n[..] Turno 2: consultando respuesta final al thread {conv_id!r}...")
        try:
            final_content, final_conv_id, final_raw = _chat_post(
                config, token, "dame el resultado", args.send_timeout, conversation_id=conv_id
            )
            dump["final_chat_response"] = {
                "text_sent": "dame el resultado",
                "content": final_content,
                "conversation_id": final_conv_id,
                "raw": final_raw,
            }
            print("\n" + "=" * 50)
            print("RESPUESTA FINAL DEL AGENTE (chat)")
            print(final_content)
            print("=" * 50)
        except Exception as err:
            print(f"[warn] No se pudo obtener respuesta final del chat: {err}")

    _save(dump, _RUNS_DIR / f"e2e-{ts}.json")

    if state == "completed":
        print("[ok] Run completado exitosamente.")
        return 0
    else:
        print(f"[ERROR] Run termino en state={state!r} — ver dump para detalles.")
        return 70


if __name__ == "__main__":
    sys.exit(main())
