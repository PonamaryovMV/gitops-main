"""Демо-компонент сервиса ФП qa/at (только stdlib).

Один и тот же образ публикуется под именами <АС>-<ФП>-<сервис>-<компонент>,
а имя и версия зашиваются при сборке. Страница показывает, что именно запущено.

GET /         HTML: сервис, компонент, версия, окружение, под
GET /version  {"version": "..."}
GET /health   {"status": "ok"}
"""

import json
import logging
import os
import signal
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SERVICE = os.getenv("APP_SERVICE", "unknown")
COMPONENT = os.getenv("APP_COMPONENT", "unknown")
VERSION = os.getenv("APP_VERSION", "none")
ENVIRONMENT = os.getenv("APP_ENVIRONMENT", "local")
PORT = int(os.getenv("PORT", "8080"))
POD = socket.gethostname()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
log = logging.getLogger(SERVICE)

# цвет карточки зависит от номера релиза: release-2-102 → второй цвет
PALETTE = ["#1f5bd8", "#1d7f4e", "#b4570b", "#7a3fc0", "#0e7c86", "#b8323f"]


def color() -> str:
    parts = VERSION.split("-")
    try:
        return PALETTE[int(parts[1]) % len(PALETTE)]
    except (IndexError, ValueError):
        return "#5a6876"


PAGE = """<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{service}-{component}</title>
<style>body{{margin:0;font-family:system-ui,sans-serif;background:#f3f5f8;color:#17212c;display:grid;place-items:center;min-height:100vh}}
.card{{background:#fff;border-radius:12px;padding:28px 32px;border-top:8px solid {color};min-width:300px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
h1{{margin:0 0 4px;font-size:22px}}.v{{font-family:monospace;font-size:28px;color:{color};margin:8px 0 16px}}
td{{padding:3px 12px 3px 0}}td:first-child{{color:#5a6876}}</style></head>
<body><div class="card"><h1>{service}</h1><div>компонент <b>{component}</b></div>
<div class="v">{version}</div><table><tr><td>окружение</td><td>{env}</td></tr><tr><td>под</td><td>{pod}</td></tr></table></div></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, ctype):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path == "/":
            html = PAGE.format(service=SERVICE, component=COMPONENT, version=VERSION, env=ENVIRONMENT, pod=POD, color=color())
            self._send(200, html.encode(), "text/html; charset=utf-8")
        elif path == "/version":
            self._send(200, json.dumps({"service": SERVICE, "component": COMPONENT, "version": VERSION}).encode(), "application/json")
        elif path == "/health":
            self._send(200, b'{"status": "ok"}', "application/json")
        else:
            self._send(404, b'{"error": "not found"}', "application/json")

    def log_message(self, fmt, *args):
        if "/health" not in self.path:
            log.info("%s %s", self.address_string(), fmt % args)


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    signal.signal(signal.SIGTERM, lambda *_: threading.Thread(target=server.shutdown).start())
    log.info("%s-%s %s listening on :%d", SERVICE, COMPONENT, VERSION, PORT)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
