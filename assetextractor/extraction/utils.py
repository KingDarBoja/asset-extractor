import json
import typing as t
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    game_path: Path
    cache_path: Path

    @classmethod
    def from_json(cls, path: Path | str) -> t.Self:
        if isinstance(path, str):
            path = Path(path)
        config_folder = path.resolve().parent

        with path.open("r") as f:
            data = json.load(f)

        for cfg_path in ["game_path", "cache_path"]:
            data[cfg_path] = Path(data[cfg_path])
            if not data[cfg_path].is_absolute():
                data[cfg_path] = config_folder / data[cfg_path]

        return cls(Path(data["game_path"]), Path(data["cache_path"]))
