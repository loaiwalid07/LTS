"""Config persistence using platformdirs."""

import json
from pathlib import Path
from platformdirs import user_config_dir

APP_NAME = "YTShortsMaker"


def get_config_dir() -> Path:
    return Path(user_config_dir(APP_NAME, ensure_exists=True))


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


def load_config() -> dict:
    """Load config from platform-appropriate user config dir."""
    path = get_config_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_config(cfg: dict) -> None:
    """Save config to platform-appropriate user config dir."""
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
