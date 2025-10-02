import os
import json
from click.testing import CliRunner
from pathlib import Path

from anidl.utils import append_history, load_history
from anidl import cli


def test_history_append_and_load(monkeypatch, tmp_path):
    # Isolate HOME to tmp_path
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    entry = {"title": "Test DL", "date": "2025-09-17"}
    append_history(entry)
    items = load_history()
    assert items and items[-1]["title"] == "Test DL"


def test_cli_history(monkeypatch):
    runner = CliRunner()
    # point HOME to a temp dir that already has a history file
    tmp = Path.cwd() / "test_hist_tmp"
    tmp.mkdir(exist_ok=True)
    monkeypatch.setenv("HOME", str(tmp))
    monkeypatch.setenv("USERPROFILE", str(tmp))
    # create a history file
    p = tmp / ".anidl"
    p.mkdir(exist_ok=True)
    hist = [{"title": "A", "date": "d1"}, {"title": "B", "date": "d2"}]
    (p / "history.json").write_text(json.dumps(hist))

    res = runner.invoke(cli.cli, ["history"]) 
    assert res.exit_code == 0
    assert "1. A" in res.output or "A - d1" in res.output
