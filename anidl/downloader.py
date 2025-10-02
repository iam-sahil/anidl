from pathlib import Path
from typing import Optional, Dict
import subprocess
import shutil
import time
import threading

try:
    import aria2p
except Exception:
    aria2p = None

try:
    from plyer import notification
except Exception:
    notification = None

try:
    from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn, TransferSpeedColumn
except Exception:
    Progress = None


def _aria2_api():
    """Return an aria2p.API instance or None if aria2p is not available or connection fails."""
    if aria2p is None:
        return None
    try:
        session = aria2p.Client()
        api = aria2p.API(session)
        # quick check
        _ = api.get_version()
        return api
    except Exception:
        try:
            # older aria2p
            session = aria2p.Session()
            api = aria2p.API(session)
            return api
        except Exception:
            return None


def add_torrent_or_magnet(uri: str, download_dir: Path, pause: bool = False, max_connections: int = 16, verify: bool = True) -> str:
    """Add a torrent file URL or magnet to aria2 (via aria2p) or fallback to subprocess aria2c.

    Returns a gid string (if aria2p) or a generated id for subprocess.
    """
    api = _aria2_api()
    if api:
        try:
            opts = {"dir": str(download_dir)}
            if pause:
                opts["pause"] = "true"
            # include max connections and integrity check options if provided
            try:
                opts["max-connection-per-server"] = str(int(max_connections))
            except Exception:
                pass
            if verify:
                opts["check-integrity"] = "true"
            else:
                opts["check-integrity"] = "false"
            # aria2p API may accept add_uris
            g = api.add(uri if isinstance(uri, list) else [uri], options=opts)
            # g may be a Download object or list; return a string gid
            try:
                return g.gid
            except Exception:
                # maybe a list
                return getattr(g[0], "gid", "")
        except Exception:
            pass

    # Fallback: call aria2c CLI to start download
    aria2c = shutil.which("aria2c")
    if aria2c:
        args = [aria2c, str(uri), f"--dir={str(download_dir)}"]
        if pause:
            args.append("--pause")
        proc = subprocess.Popen(args)
        return f"subproc-{proc.pid}"

    raise RuntimeError("aria2p unavailable and aria2c not found on PATH")


def resolve_magnet(uri: str, download_dir: Optional[Path] = None, timeout: int = 10) -> Optional[Dict]:
    """Try to add magnet in paused state to fetch metadata, then return basic metadata.

    This requires aria2 RPC to be running. If aria2p is not available, return None.
    """
    api = _aria2_api()
    if not api:
        return None
    try:
        # add the magnet paused so metadata can be fetched
        opts = {"pause": "true"}
        gid = api.add([uri], options=opts).gid
        # poll for metadata (limited time)
        waited = 0
        while waited < timeout:
            dl = api.get_download(gid)
            if getattr(dl, "is_metadata_received", False):
                meta = {"title": getattr(dl, "name", None), "size": getattr(dl, "total_length", None)}
                # remove or stop the download to avoid leaving paused entries
                try:
                    api.remove(gid)
                except Exception:
                    pass
                return meta
            time.sleep(1)
            waited += 1
        # timeout
        try:
            api.remove(gid)
        except Exception:
            pass
        return None
    except Exception:
        return None


def notify(title: str, message: str):
    if notification is None:
        return
    try:
        notification.notify(title=title, message=message, timeout=5)
    except Exception:
        return


def download_with_progress(gids: list, download_dir: Path):
    """Monitor downloads via aria2p and show progress using rich.Progress.

    This function is best-effort: if rich or aria2p are not available it will return immediately.
    """
    api = _aria2_api()
    if api is None or Progress is None:
        return

    # This function runs a simple loop that polls downloads until they finish
    with Progress(
        "{task.description}",
        TextColumn("{task.fields[title]}", justify="left"),
        BarColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    ) as progress:
        tasks = {}
        running = True
        while running:
            running = False
            for gid in gids:
                try:
                    dl = api.get_download(gid)
                except Exception:
                    continue
                running = True
                total = getattr(dl, "total_length", 0) or None
                completed = getattr(dl, "completed_length", 0) or 0
                speed = getattr(dl, "download_speed", 0) or 0
                title = getattr(dl, "name", gid)
                if gid not in tasks:
                    task_id = progress.add_task("download", total=total, title=title)
                    tasks[gid] = task_id
                else:
                    task_id = tasks[gid]
                progress.update(task_id, completed=completed)
            time.sleep(0.5)

