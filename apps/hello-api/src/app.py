"""hello-api — минимальный JSON API для стенда (только stdlib).

GET /         информация о версии и поде
GET /version  {"version": "..."} — проверяется Kargo-верификацией
GET /health   200, если сборка "здоровая"; 500, если собрана с APP_BROKEN=true
              (по нему canary-анализ Argo Rollouts решает, катить ли дальше)
GET /ready    readiness-проба, всегда 200
"""

import json
import logging
import os
import signal
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP_NAME = "hello-api"
VERSION = os.getenv("APP_VERSION", "0.0.0")
COLOR = os.getenv("APP_COLOR", "blue")
BROKEN = os.getenv("APP_BROKEN", "false").lower() == "true"
PORT = int(os.getenv("PORT", "8080"))
NAMESPACE = os.getenv("POD_NAMESPACE", "local")
HOSTNAME = socket.gethostname()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(APP_NAME)


class Handler(BaseHTTPRequestHandler):
    server_version = f"{APP_NAME}/{VERSION}"

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (имя задаёт BaseHTTPRequestHandler)
        path = self.path.split("?", 1)[0]
        if path == "/":
            self._json(200, {
                "app": APP_NAME,
                "version": VERSION,
                "color": COLOR,
                "pod": HOSTNAME,
                "namespace": NAMESPACE,
                "broken": BROKEN,
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
        # пробы не засоряют лог
        if "/ready" in self.path:
            return
        log.info("%s %s", self.address_string(), fmt % args)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    # shutdown() блокируется до выхода serve_forever(), поэтому вызываем его из отдельного потока
    signal.signal(signal.SIGTERM, lambda *_: threading.Thread(target=server.shutdown).start())
    log.info("%s %s listening on :%d (broken=%s, color=%s)", APP_NAME, VERSION, PORT, BROKEN, COLOR)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        log.info("stopped")


if __name__ == "__main__":
    main()
