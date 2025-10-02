import shutil
from pathlib import Path
import subprocess


def test_add_torrent_or_magnet_subprocess(monkeypatch, tmp_path):
    # Simulate aria2p not available and aria2c present
    import anidl.downloader as dl

    monkeypatch.setattr(dl, "aria2p", None)
    # Create a fake aria2c executable path
    fake = tmp_path / "aria2c"
    fake.write_text("")
    monkeypatch.setenv("PATH", str(tmp_path))

    # Ensure shutil.which finds the fake
    monkeypatch.setattr(shutil, "which", lambda name: str(fake))

    # Mock subprocess.Popen so we don't try to execute the fake file
    class FakeProc:
        def __init__(self):
            self.pid = 42424

    monkeypatch.setattr(subprocess, "Popen", lambda args: FakeProc())

    pid_like = dl.add_torrent_or_magnet("magnet:?xt=urn:btih:FAKE", tmp_path)
    assert pid_like == "subproc-42424"


def test_resolve_magnet_no_aria2(monkeypatch):
    import anidl.downloader as dl
    monkeypatch.setattr(dl, "aria2p", None)
    assert dl.resolve_magnet("magnet:?xt=urn:btih:FAKE") is None
