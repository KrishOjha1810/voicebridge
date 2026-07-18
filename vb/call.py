"""voicebridge call: a real phone call with your live session. No Channels.

The true hands-free mobile mode: dial a phone number, talk, hear replies,
no taps, works while driving. Vapi (voice-AI platform) handles the call,
speech-to-text, and natural neural voices; this relay is the "custom LLM"
it talks to, and it bridges each turn into your live Claude session:

  phone --call--> Vapi --STT--> POST /chat/completions --> this relay
                                                            | inject into
                                                            | focused session
       <--speak-- Vapi <--TTS--  reply text  <-- transcript watch

Channels-free: injection is local (same path as /voice-on), so it works on
org accounts where Claude Channels is blocked.

Needs (one-time, yours): a Vapi account + phone number (paid per minute),
and a tunnel to expose the relay (e.g. `ngrok http 8790`). Point the Vapi
assistant's Custom LLM URL at https://<tunnel>/chat/completions and set a
shared secret. See mobile/vapi/VAPI.md.

Control: vb call on | off | status     Env: VB_CALL_PORT, VB_CALL_SECRET,
VB_CALL_TIMEOUT (seconds per turn), VB_CALL_DRYRUN (test without injecting).
"""

import json
import os
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import core, inject
from .talkd import ACTIVE, _read_json

PID = core.STATE_DIR / "call.pid"
PORT = int(os.environ.get("VB_CALL_PORT", "8790"))
SECRET = os.environ.get("VB_CALL_SECRET", "")
TIMEOUT = float(os.environ.get("VB_CALL_TIMEOUT", "90"))
DRYRUN = bool(os.environ.get("VB_CALL_DRYRUN"))


def _target_transcript() -> str:
    active = _read_json(ACTIVE)
    if active and os.path.exists(active.get("transcript_path", "")):
        return active["transcript_path"]
    return core.newest_transcript()


def _extract_user_text(body: dict) -> str:
    """Last user message; content may be a string or a list of parts."""
    msgs = body.get("messages") or []
    for m in reversed(msgs):
        if m.get("role") != "user":
            continue
        c = m.get("content")
        if isinstance(c, str):
            return c.strip()
        if isinstance(c, list):
            parts = [p.get("text", "") for p in c
                     if isinstance(p, dict) and p.get("type") == "text"]
            return " ".join(parts).strip()
    return ""


def _ask_session(text: str) -> str:
    """Inject a turn into the live session and wait for the reply."""
    if DRYRUN:
        return f"dry run reply to: {text}"
    tp = _target_transcript()
    if not tp:
        return "I can't find an open session on the Mac."
    prev = core.last_assistant_text(tp)
    core.log(f"call you: {text}")
    inject.paste_text(text, send=True)
    t0 = time.time()
    while time.time() - t0 < TIMEOUT:
        time.sleep(1.0)
        cur = core.last_assistant_text(tp)
        if cur and cur != prev:
            # Phone answers should be speech-shaped: no markdown/code.
            return core.clean_for_speech(cur, max_chars=2500)
    return "Still working on that. Ask me again in a moment."


def _openai_json(text: str) -> bytes:
    return json.dumps({
        "id": f"chatcmpl-vb{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "voicebridge-live-session",
        "choices": [{"index": 0, "finish_reason": "stop",
                     "message": {"role": "assistant", "content": text}}],
    }).encode()


def _sse(text: str) -> bytes:
    chunk = {
        "id": f"chatcmpl-vb{int(time.time())}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": "voicebridge-live-session",
        "choices": [{"index": 0, "delta": {"role": "assistant",
                                           "content": text},
                     "finish_reason": None}],
    }
    done = dict(chunk)
    done["choices"] = [{"index": 0, "delta": {}, "finish_reason": "stop"}]
    return (f"data: {json.dumps(chunk)}\n\n"
            f"data: {json.dumps(done)}\n\ndata: [DONE]\n\n").encode()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # keep the daemon quiet
        core.log("call http: " + fmt % args)

    def _reply(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._reply(200, b"ok", "text/plain")
        else:
            self._reply(404, b"not found", "text/plain")

    def do_POST(self):
        if not self.path.rstrip("/").endswith("chat/completions"):
            self._reply(404, b"not found", "text/plain")
            return
        if SECRET:
            got = (self.headers.get("x-vapi-secret", "")
                   or self.headers.get("Authorization", "")
                   .removeprefix("Bearer ").strip())
            if got != SECRET:
                self._reply(401, b"unauthorized", "text/plain")
                return
        try:
            n = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            self._reply(400, b"bad request", "text/plain")
            return
        text = _extract_user_text(body)
        answer = (_ask_session(text) if text
                  else "Sorry, I didn't catch that.")
        if body.get("stream"):
            self._reply(200, _sse(answer), "text/event-stream")
        else:
            self._reply(200, _openai_json(answer), "application/json")


def run_daemon() -> int:
    core.log(f"call: relay listening on 127.0.0.1:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
    return 0


def _alive() -> bool:
    try:
        os.kill(int(PID.read_text().strip()), 0)
        return True
    except Exception:
        return False


def on() -> str:
    if _alive():
        return "call relay already running"
    core.STATE_DIR.mkdir(parents=True, exist_ok=True)
    vb = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "bin", "vb")
    env = dict(os.environ)
    p = subprocess.Popen([sys.executable, vb, "call", "__run__"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True, env=env)
    PID.write_text(str(p.pid))
    return (f"call relay ON (pid {p.pid}, port {PORT}). Tunnel it "
            f"(`ngrok http {PORT}`) and point your Vapi assistant's Custom "
            f"LLM at https://<tunnel>/chat/completions. See mobile/vapi/VAPI.md.")


def off() -> str:
    try:
        os.kill(int(PID.read_text().strip()), 15)
    except Exception:
        pass
    try:
        PID.unlink()
    except FileNotFoundError:
        pass
    return "call relay OFF"


def status() -> str:
    return "\n".join([
        f"relay  : {'running' if _alive() else 'stopped'} (port {PORT})",
        f"secret : {'set' if SECRET else '(none - set VB_CALL_SECRET!)'}",
        f"target : {_target_transcript() or '(no session)'}",
    ])
