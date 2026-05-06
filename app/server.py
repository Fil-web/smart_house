from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from app.config import config
from app.storage import Store


ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"
store = Store(config.db_path)


class SmartHomeHandler(BaseHTTPRequestHandler):
    server_version = "PySmartHome/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_json({"ok": True, "app": config.app_name})
            return
        if parsed.path == "/api/devices":
            self.send_json({"devices": store.list_devices()})
            return
        if parsed.path == "/api/scenes":
            self.send_json({"scenes": store.list_scenes()})
            return
        if parsed.path == "/api/events":
            query = parse_qs(parsed.query)
            limit = int(query.get("limit", ["25"])[0])
            self.send_json({"events": store.recent_events(limit)})
            return
        self.serve_static(parsed.path)

    def do_PATCH(self) -> None:
        parsed = urlparse(self.path)
        parts = parsed.path.strip("/").split("/")
        if len(parts) == 3 and parts[:2] == ["api", "devices"]:
            payload = self.read_json()
            device = store.update_device_state(parts[2], payload.get("state", payload))
            if device is None:
                self.send_json({"error": "device not found"}, HTTPStatus.NOT_FOUND)
                return
            self.send_json({"device": device})
            return
        self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        parts = parsed.path.strip("/").split("/")
        if len(parts) == 4 and parts[:2] == ["api", "scenes"] and parts[3] == "run":
            scene = store.run_scene(parts[2])
            if scene is None:
                self.send_json({"error": "scene not found"}, HTTPStatus.NOT_FOUND)
                return
            self.send_json({"scene": scene, "devices": store.list_devices()})
            return
        self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def serve_static(self, path: str) -> None:
        if path in ("", "/"):
            path = "/index.html"
        target = (WEB_DIR / path.lstrip("/")).resolve()
        if not str(target).startswith(str(WEB_DIR.resolve())) or not target.exists():
            self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        content_type = "text/html; charset=utf-8"
        if target.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        elif target.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"
        data = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args: object) -> None:
        print("%s - %s" % (self.address_string(), fmt % args))


def main() -> None:
    server = ThreadingHTTPServer((config.host, config.port), SmartHomeHandler)
    print(f"{config.app_name} listening on http://{config.host}:{config.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
