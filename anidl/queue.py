from typing import List
import shutil
import subprocess

try:
    import aria2p
except Exception:
    aria2p = None


def _api():
    if aria2p is None:
        return None
    try:
        session = aria2p.Client()
        return aria2p.API(session)
    except Exception:
        try:
            session = aria2p.Session()
            return aria2p.API(session)
        except Exception:
            return None


def _session_path():
    from pathlib import Path
    return Path.home() / ".anidl" / "aria2.session"


def _save_session(api):
    try:
        sp = _session_path()
        # ensure dir exists
        sp.parent.mkdir(parents=True, exist_ok=True)
        if hasattr(api, "save_session"):
            api.save_session(str(sp))
    except Exception:
        pass


def list_downloads() -> List[dict]:
    api = _api()
    if api:
        try:
            downloads = api.get_downloads()
            out = []
            for d in downloads:
                out.append({"gid": d.gid, "name": getattr(d, "name", None), "status": d.status})
            try:
                _save_session(api)
            except Exception:
                pass
            return out
        except Exception:
            return []
    # fallback: no aria2 available
    return []


def pause(gid: str) -> bool:
    api = _api()
    if api:
        try:
            api.pause(gid)
            try:
                _save_session(api)
            except Exception:
                pass
            return True
        except Exception:
            return False
    return False


def resume(gid: str) -> bool:
    api = _api()
    if api:
        try:
            api.unpause(gid)
            try:
                _save_session(api)
            except Exception:
                pass
            return True
        except Exception:
            return False
    return False


def remove(gid: str) -> bool:
    api = _api()
    if api:
        try:
            api.remove(gid)
            try:
                _save_session(api)
            except Exception:
                pass
            return True
        except Exception:
            return False
    return False
