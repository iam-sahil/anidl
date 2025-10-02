import toml
from pathlib import Path


def _config_path(user: str | None = None) -> Path:
    if user:
        d = Path.home() / f".anidl-{user}"
    else:
        d = Path.home() / ".anidl"
    d.mkdir(parents=True, exist_ok=True)
    return d / "config.toml"


def load_config(user: str | None = None) -> dict:
    p = _config_path(user)
    if not p.exists():
        default = {"defaults": {"download_dir": "./downloads", "resolution": "", "notify": True}}
        save_config(default, user=user)
        return default
    try:
        return toml.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"defaults": {"download_dir": "./downloads", "resolution": "", "notify": True}}


def save_config(cfg: dict, user: str | None = None):
    p = _config_path(user)
    p.write_text(toml.dumps(cfg), encoding="utf-8")
