import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    app_name: str = os.getenv("APP_NAME", "Py Smart Home")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    data_dir: Path = Path(os.getenv("DATA_DIR", "/data"))

    @property
    def db_path(self) -> Path:
        return self.data_dir / "smart_home.sqlite3"


config = Config()
