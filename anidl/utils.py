from typing import List
from pathlib import Path


def parse_selection(input_str: str, max_idx: int) -> List[int]:
    """Parse strings like '1,2,5-7' into list of ints (1-based)."""
    if not input_str:
        return []
    # normalize separators
    normalized = input_str.replace(";", ",").replace(" ", ",")
    parts = [p.strip() for p in normalized.split(",") if p.strip()]
    out = set()
    for p in parts:
        if "-" in p:
            a, b = p.split("-", 1)
            try:
                a_i = int(a)
                b_i = int(b)
            except ValueError:
                continue
            for i in range(max(1, a_i), min(max_idx, b_i) + 1):
                out.add(i)
        else:
            try:
                v = int(p)
            except ValueError:
                continue
            if 1 <= v <= max_idx:
                out.add(v)
    return sorted(out)


def ensure_dir(p: Path):
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)


def _history_path() -> Path:
    d = Path.home() / ".anidl"
    d.mkdir(parents=True, exist_ok=True)
    return d / "history.json"


def append_history(entry: dict):
    p = _history_path()
    import json
    items = []
    if p.exists():
        try:
            items = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            items = []
    items.append(entry)
    p.write_text(json.dumps(items, default=str, indent=2), encoding="utf-8")


def load_history() -> List[dict]:
    p = _history_path()
    import json
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []


def setup_logging(verbose: bool = False):
    import logging
    log_dir = Path.home() / ".anidl"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "anidl.log"
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.FileHandler(log_file, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(formatter)
    root = logging.getLogger()
    # Avoid adding multiple handlers in repeated calls
    if not any(isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', None) == str(log_file) for h in root.handlers):
        root.addHandler(handler)
    root.setLevel(level)
