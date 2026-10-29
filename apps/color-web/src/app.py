"""color-web — веб-страница для наглядного canary (только stdlib).

Страница раз в секунду опрашивает /api/info: видно, какой под (stable или canary)
ответил, его цвет и версию, а также версию hello-api в том же неймспейсе.

GET /          HTML-страница
GET /api/info  JSON: эта версия + ответ hello-api
GET /version   {"version": "..."} — проверяется Kargo-верификацией
GET /health    200 / 500 (если собрано с APP_BROKEN=true)
GET /ready     readiness-проба
"""

import json
import logging
import os
import signal
import socket
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP_NAME = "color-web"
VERSION = os.getenv("APP_VERSION", "0.0.0")
COLOR = os.getenv("APP_COLOR", "blue")
BROKEN = os.getenv("APP_BROKEN", "false").lower() == "true"
PORT = int(os.getenv("PORT", "8080"))
NAMESPACE = os.getenv("POD_NAMESPACE", "local")
HELLO_API_URL = os.getenv("HELLO_API_URL", "http://hello-api")
HOSTNAME = socket.gethostname()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(APP_NAME)

PAGE = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>color-web</title>
<style>
  :root { color-scheme: light dark; font-family: system-ui, sans-serif; }
  body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: #111; color: #eee; }
  main { width: min(720px, 100vw - 32px); }
  h1 { font-size: 1.1rem; font-weight: 600; opacity: .8; }
  #grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 4px; margin: 16px 0; }
  .cell { aspect-ratio: 1; border-radius: 4px; background: #333; transition: background .3s; }
  table { width: 100%; border-collapse: collapse; font-size: .9rem; }
  td { padding: 4px 0; border-bottom: 1px solid #2a2a2a; }
  td:first-child { opacity: .6; width: 40%; }
  .err { color: #ff6b6b; }
</style>
</head>
<body>
<main>
  <h1>color-web · __NAMESPACE__</h1>
  <div id="grid"></div>
  <table>
    <tr><td>color-web</td><td id="self">…</td></tr>
    <tr><td>под</td><td id="pod">…</td></tr>
    <tr><td>hello-api</td><td id="api">…</td></tr>
  </table>
</main>
<script>
  const grid = document.getElementById("grid");
  for (let i = 0; i < 50; i++) grid.insertAdjacentHTML("beforeend", '<div class="cell"></div>');
  const cells = [...grid.children];
  let i = 0;
  async function tick() {
    try {
      const r = await fetch("/api/info", { cache: "no-store" });
      const d = await r.json();
      cells[i++ % cells.length].style.background = d.color;
      document.getElementById("self").textContent = d.version + " (" + d.color + ")";
      document.getElementById("pod").textContent = d.pod;
      const api = document.getElementById("api");
      api.textContent = d.backend.version ? d.backend.version : d.backend.error;
      api.className = d.backend.error ? "err" : "";
    } catch (e) {
      cells[i++ % cells.length].style.background = "#000";
    }
  }
  setInterval(tick, 1000);
  tick();
</script>
</body>
</html>
"""


def backend_info() -> dict:
    try:
        with urllib.request.urlopen(f"{HELLO_API_URL}/version", timeout=2) as resp:
            return json.load(resp)
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return {"error": f"hello-api недоступен: {exc}"}


class Handler(BaseHTTPRequestHandler):
    server_version = f"{APP_NAME}/{VERSION}"

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: dict) -> None:
        self._send(status, json.dumps(payload).encode(), "application/json")

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path == "/":
            self._send(200, PAGE.replace("__NAMESPACE__", NAMESPACE).encode(), "text/html; charset=utf-8")
        elif path == "/api/info":
            self._json(200, {
                "app": APP_NAME,
                "version": VERSION,
                "color": COLOR,
                "pod": HOSTNAME,
                "namespace": NAMESPACE,
                "backend": backend_info(),
            })
        elif path == "/version":
            self._json(200, {"version": VERSION})
        elif path == "/health":
            if BROKEN:
                self._json(500, {"status": "broken", "version": VERSION})
            else:
                self._json(200, {"status": "ok", "version": VERSION})
        elif path == "/ready":
            self._json(200, {"status": "ready"})
        else:
            self._json(404, {"error": "not found", "path": path})

    def log_message(self, fmt: str, *args) -> None:
        if self.path.startswith(("/ready", "/api/info")):
            return
        log.info("%s %s", self.address_string(), fmt % args)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    signal.signal(signal.SIGTERM, lambda *_: threading.Thread(target=server.shutdown).start())
    log.info("%s %s listening on :%d (broken=%s, color=%s, hello-api=%s)",
             APP_NAME, VERSION, PORT, BROKEN, COLOR, HELLO_API_URL)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        log.info("stopped")


if __name__ == "__main__":
    main()
