#!/usr/bin/env python3
"""Kokoro TTS server: loads the model once, synthesizes over local HTTP.

Runs inside the voicebridge Kokoro venv (see `vb tts on`). Endpoints:
  GET  /health          -> ok
  POST /synth  {"text": ..., "voice": "af_heart", "speed": 1.0} -> WAV bytes

Local-only (127.0.0.1). Model: ~/.voicebridge/models/kokoro-v1.0.onnx
"""

import io
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import soundfile as sf
from kokoro_onnx import Kokoro

HOME = os.path.expanduser("~")
MODEL = os.path.join(HOME, ".voicebridge", "models", "kokoro-v1.0.onnx")
VOICES = os.path.join(HOME, ".voicebridge", "models", "voices-v1.0.bin")
PORT = int(os.environ.get("VB_TTS_PORT", "8798"))

kokoro = Kokoro(MODEL, VOICES)


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _out(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._out(200, b"ok", "text/plain")
        elif self.path == "/voices":
            self._out(200, json.dumps(sorted(kokoro.get_voices())).encode(),
                      "application/json")
        else:
            self._out(404, b"nope", "text/plain")

    def do_POST(self):
        if self.path != "/synth":
            self._out(404, b"nope", "text/plain")
            return
        try:
            n = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(n))
            text = (req.get("text") or "").strip()
            voice = req.get("voice") or "af_heart"
            speed = float(req.get("speed") or 1.0)
            if not text:
                raise ValueError("empty text")
            samples, sr = kokoro.create(text, voice=voice, speed=speed)
            buf = io.BytesIO()
            sf.write(buf, samples, sr, format="WAV")
            self._out(200, buf.getvalue(), "audio/wav")
        except Exception as e:
            self._out(500, str(e).encode(), "text/plain")


print(f"kokoro server on 127.0.0.1:{PORT}", flush=True)
ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
