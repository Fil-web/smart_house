from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_DEVICES = [
    {
        "id": "hall_light",
        "name": "Свет в прихожей",
        "type": "light",
        "room": "Прихожая",
        "state": {"power": False, "brightness": 70},
    },
    {
        "id": "kitchen_light",
        "name": "Свет на кухне",
        "type": "light",
        "room": "Кухня",
        "state": {"power": False, "brightness": 80},
    },
    {
        "id": "bedroom_temp",
        "name": "Температура спальни",
        "type": "sensor",
        "room": "Спальня",
        "state": {"temperature": 22.4, "humidity": 41},
    },
]

DEFAULT_SCENES = [
    {
        "id": "evening",
        "name": "Вечер",
        "actions": [
            {"device_id": "hall_light", "state": {"power": True, "brightness": 45}},
            {"device_id": "kitchen_light", "state": {"power": True, "brightness": 55}},
        ],
    },
    {
        "id": "sleep",
        "name": "Сон",
        "actions": [
            {"device_id": "hall_light", "state": {"power": False}},
            {"device_id": "kitchen_light", "state": {"power": False}},
        ],
    },
]


class Store:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    room TEXT NOT NULL,
                    state TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scenes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    actions TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    kind TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            self._seed(conn)

    def _seed(self, conn: sqlite3.Connection) -> None:
        count = conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO devices (id, name, type, room, state) VALUES (?, ?, ?, ?, ?)",
                [
                    (
                        device["id"],
                        device["name"],
                        device["type"],
                        device["room"],
                        json.dumps(device["state"]),
                    )
                    for device in DEFAULT_DEVICES
                ],
            )
        scene_count = conn.execute("SELECT COUNT(*) FROM scenes").fetchone()[0]
        if scene_count == 0:
            conn.executemany(
                "INSERT INTO scenes (id, name, actions) VALUES (?, ?, ?)",
                [
                    (scene["id"], scene["name"], json.dumps(scene["actions"]))
                    for scene in DEFAULT_SCENES
                ],
            )

    def list_devices(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM devices ORDER BY room, name").fetchall()
        return [self._device_from_row(row) for row in rows]

    def get_device(self, device_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()
        return self._device_from_row(row) if row else None

    def update_device_state(self, device_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        device = self.get_device(device_id)
        if device is None:
            return None
        state = device["state"] | patch
        with self.connect() as conn:
            conn.execute(
                "UPDATE devices SET state = ? WHERE id = ?",
                (json.dumps(state), device_id),
            )
            self.log_event(conn, "device.updated", {"device_id": device_id, "state": patch})
        device["state"] = state
        return device

    def list_scenes(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM scenes ORDER BY name").fetchall()
        return [self._scene_from_row(row) for row in rows]

    def run_scene(self, scene_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM scenes WHERE id = ?", (scene_id,)).fetchone()
            if row is None:
                return None
            scene = self._scene_from_row(row)
            for action in scene["actions"]:
                device = self.get_device(action["device_id"])
                if device is None:
                    continue
                state = device["state"] | action["state"]
                conn.execute(
                    "UPDATE devices SET state = ? WHERE id = ?",
                    (json.dumps(state), action["device_id"]),
                )
            self.log_event(conn, "scene.ran", {"scene_id": scene_id})
        return scene

    def recent_events(self, limit: int = 25) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "kind": row["kind"],
                "payload": json.loads(row["payload"]),
            }
            for row in rows
        ]

    def log_event(self, conn: sqlite3.Connection, kind: str, payload: dict[str, Any]) -> None:
        conn.execute(
            "INSERT INTO events (kind, payload) VALUES (?, ?)",
            (kind, json.dumps(payload)),
        )

    def _device_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "type": row["type"],
            "room": row["room"],
            "state": json.loads(row["state"]),
        }

    def _scene_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "actions": json.loads(row["actions"]),
        }
