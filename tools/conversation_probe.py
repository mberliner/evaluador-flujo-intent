"""REPL interactivo contra el agente bajo test.

Envía mensajes, espera que el flow async complete y muestra la respuesta
real del agente (no el placeholder "A new flow has started...").

El flujo por turno es:
  1. POST /chat/completions  → thread_id + placeholder
  2. GET  /flows             → polling hasta state=completed
  3. GET  /threads/{id}/messages → mensaje con "riesgo: ..."

Cada turno queda registrado en la transcripción. Se puede volcar a JSON
al salir o con /save.

Uso:
    python tools/conversation_probe.py [--timeout 300]

Comandos (escribirlos solos en la primera línea):
    /reset      Descarta el thread y arranca uno nuevo.
    /save       Vuelca la transcripción a runs/probe-<ts>.json.
    /show       Muestra resumen de los turnos actuales.
    /quit       Sale (guarda automáticamente si hubo turnos).
    /help       Muestra esta ayuda.

Mensajes: multilinea por defecto. Terminar con '.' solo en una línea o EOF.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json as _json
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

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

_POLL_INTERVAL = 10
_FLOW_STARTED_PREFIX = "A new flow has started"


# ---------------------------------------------------------------------------
# Modelos de transcripción
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class _Turn:
    index: int
    sent_at: str
    prompt: str
    immediate: str
    final_response: str | None
    thread_id_in: str | None
    thread_id_out: str | None
    flow_state: str | None


@dataclass(slots=True)
class _Transcript:
    agent_id: str
    started_at: str
    turns: list[_Turn] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "started_at": self.started_at,
            "turns": [asdict(t) for t in self.turns],
        }


# ---------------------------------------------------------------------------
# Helpers de red
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds")


def _threads_url(config: PlatformConfig) -> str:
    return config.chat_url.rstrip("/") + "/threads"


def _post_chat(
    config: PlatformConfig,
    token: str,
    text: str,
    thread_id: str | None,
    timeout: int,
) -> tuple[str, str | None]:
    """POST a chat/completions. Devuelve (content, thread_id)."""
    payload: dict = {
        "messages": [{"role": "user", "content": [{"response_type": "text", "text": text}]}],
        "stream": "false",
    }
    if thread_id:
        payload["thread_id"] = thread_id

    url = f"{config.chat_url}{config.agent_id}/chat/completions"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"Error API {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    return str(content), data.get("thread_id")


def _poll_thread(config: PlatformConfig, token: str, thread_id: str, timeout: int) -> bool:
    """Polling en /threads/{thread_id}/messages hasta que aparece la respuesta final.

    Retorna True cuando hay un mensaje assistant que no es el control message del flow.
    """
    url = f"{_threads_url(config)}/{thread_id}/messages"
    deadline = time.time() + timeout

    while time.time() < deadline:
        headers = {"Authorization": f"Bearer {token}"}
        try:
            resp = requests.get(url, headers=headers, timeout=30)
        except requests.RequestException as err:
            print(f"[warn] GET /threads → {err}")
            time.sleep(_POLL_INTERVAL)
            continue

        if resp.status_code != 200:
            print(f"[warn] GET /threads → {resp.status_code}")
            time.sleep(_POLL_INTERVAL)
            continue

        messages = resp.json()
        if not isinstance(messages, list):
            messages = messages.get("messages", [])

        for msg in messages:
            if msg.get("role") != "assistant":
                continue
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
            if _FLOW_STARTED_PREFIX not in str(content):
                print(f"[..] {_now_iso()} — respuesta final recibida")
                return True

        print(f"[..] {_now_iso()} — esperando respuesta del agente...")
        time.sleep(_POLL_INTERVAL)

    return False


def _get_final_response(config: PlatformConfig, token: str, thread_id: str) -> str | None:
    """Lee el thread y devuelve el primer mensaje del agente con la clasificación."""
    url = f"{_threads_url(config)}/{thread_id}/messages"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code != 200:
        return None
    messages = resp.json()
    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
        if _FLOW_STARTED_PREFIX in str(content):
            continue
        return str(content)
    return None


# ---------------------------------------------------------------------------
# REPL
# ---------------------------------------------------------------------------


def _read_message(first_line: str) -> str:
    if first_line.strip() == ".":
        return ""
    lines = [first_line]
    while True:
        try:
            cont = input("..   ")
        except EOFError:
            print()
            break
        if cont.strip() == ".":
            break
        lines.append(cont)
    return "\n".join(lines)


def _save(transcript: _Transcript, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = _json.dumps(transcript.to_dict(), ensure_ascii=False, indent=2)
    path.write_text(content, encoding="utf-8")
    print(f"[ok] Transcripción guardada en {path}")


def _show(transcript: _Transcript, thread_id: str | None) -> None:
    print(f"\n=== Transcripción ({len(transcript.turns)} turno(s)) ===")
    print(f"thread actual: {thread_id or '(ninguno)'}")
    for t in transcript.turns:
        resp = (t.final_response or t.immediate)[:100].replace("\n", " ")
        print(f"  #{t.index}  prompt: {t.prompt[:60]!r}")
        print(f"          resp:   {resp!r}")
        print(f"          flow:   {t.flow_state or '?'}")
    print("=" * 40)


def _help() -> None:
    print(
        "Comandos (solos en la primera línea):\n"
        "  /reset   Nuevo thread.\n"
        "  /save    Guarda la transcripción.\n"
        "  /show    Resumen de turnos.\n"
        "  /quit    Salir.\n"
        "  /help    Esta ayuda.\n"
        "\n"
        "Mensajes multilinea: terminar con '.' solo en una línea o EOF.\n"
        "El probe espera automáticamente la respuesta real del agente."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="REPL contra el agente bajo test (modo async).")
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout de polling por turno en segundos (default: 300).",
    )
    parser.add_argument(
        "--send-timeout",
        type=int,
        default=60,
        help="Timeout del POST inicial (default: 60).",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    try:
        config = PlatformConfig.from_env()
    except MissingConfigError as err:
        print(f"[ERROR] Config: {err}", file=sys.stderr)
        return 10

    credentials = TokenProvider(config)
    try:
        credentials.get()
    except TokenError as err:
        print(f"[ERROR] Token: {err}", file=sys.stderr)
        return 20

    transcript = _Transcript(agent_id=config.agent_id, started_at=_now_iso())
    default_save = f"runs/probe-{_dt.datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
    thread_id: str | None = None

    print(f"[ok] Conectado (agent_id={config.agent_id})")
    print("Tipea /help para comandos. /quit para salir.")
    print("Mensajes multilinea: terminar con '.' en una línea sola.\n")

    while True:
        try:
            first = input(">>   ").rstrip("\n")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not first.strip():
            continue

        if first.startswith("/"):
            cmd, _, _ = first.partition(" ")
            if cmd == "/quit":
                break
            elif cmd == "/help":
                _help()
            elif cmd == "/reset":
                thread_id = None
                print("[ok] Thread reseteado.")
            elif cmd == "/show":
                _show(transcript, thread_id)
            elif cmd == "/save":
                _save(transcript, Path(default_save))
            else:
                print(f"[ERROR] Comando desconocido: {cmd}", file=sys.stderr)
            continue

        prompt = _read_message(first)
        if not prompt:
            continue

        token = credentials.get()
        sent_at = _now_iso()

        # 1. POST al agente
        print("[..] Enviando...")
        try:
            immediate, new_thread_id = _post_chat(
                config, token, prompt, thread_id, args.send_timeout
            )
        except Exception as err:
            print(f"[ERROR] {err}", file=sys.stderr)
            continue

        thread_id = new_thread_id or thread_id
        print(f"[ok] thread_id: {thread_id}")
        print(f"[..] Respuesta inmediata: {immediate[:80]!r}")

        # 2. Si es un flow async, esperar y leer el thread
        flow_state: str | None = None
        final_response: str | None = None

        if _FLOW_STARTED_PREFIX in immediate and thread_id:
            print(
                f"[..] Flow detectado — polling thread messages "
                f"(timeout={args.timeout}s, intervalo={_POLL_INTERVAL}s)..."
            )
            completed = _poll_thread(config, token, thread_id, args.timeout)
            if completed:
                flow_state = "completed"
                final_response = _get_final_response(config, token, thread_id)
            else:
                flow_state = "timeout"
                print("[warn] Timeout agotado sin recibir respuesta final.")

        turn = _Turn(
            index=len(transcript.turns) + 1,
            sent_at=sent_at,
            prompt=prompt,
            immediate=immediate,
            final_response=final_response,
            thread_id_in=thread_id,
            thread_id_out=new_thread_id,
            flow_state=flow_state,
        )
        transcript.turns.append(turn)

        print(f"\n--- turno #{turn.index} ---")
        if final_response:
            print(final_response)
        else:
            print(immediate)
        print("-" * 40)

    if transcript.turns:
        _save(transcript, Path(default_save))
    return 0


if __name__ == "__main__":
    sys.exit(main())
