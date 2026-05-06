from __future__ import annotations

import argparse
import json
import urllib.request


def request(method: str, base_url: str, path: str, payload: dict | None = None) -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(base_url + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Console client for Py Smart Home")
    parser.add_argument("--url", default="http://localhost:8000")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("devices")
    set_parser = sub.add_parser("set")
    set_parser.add_argument("device_id")
    set_parser.add_argument("key")
    set_parser.add_argument("value")

    sub.add_parser("scenes")
    scene_parser = sub.add_parser("run-scene")
    scene_parser.add_argument("scene_id")

    args = parser.parse_args()
    if args.command == "devices":
        result = request("GET", args.url, "/api/devices")
    elif args.command == "set":
        value: object = args.value
        if args.value.lower() in ("true", "false"):
            value = args.value.lower() == "true"
        elif args.value.isdigit():
            value = int(args.value)
        result = request("PATCH", args.url, f"/api/devices/{args.device_id}", {"state": {args.key: value}})
    elif args.command == "scenes":
        result = request("GET", args.url, "/api/scenes")
    else:
        result = request("POST", args.url, f"/api/scenes/{args.scene_id}/run")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
