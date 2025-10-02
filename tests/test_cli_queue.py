from click.testing import CliRunner
from unittest import mock

from anidl import cli


def test_queue_list_no_items(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr("anidl.queue.list_downloads", lambda: [])
    result = runner.invoke(cli.cli, ["queue", "list"]) 
    assert result.exit_code == 0
    assert "No active downloads." in result.output


def test_queue_pause_resume_remove(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr("anidl.queue.pause", lambda gid: True)
    monkeypatch.setattr("anidl.queue.resume", lambda gid: True)
    monkeypatch.setattr("anidl.queue.remove", lambda gid: True)

    r1 = runner.invoke(cli.cli, ["queue", "pause", "GID123"])
    assert r1.exit_code == 0 and "Paused" in r1.output

    r2 = runner.invoke(cli.cli, ["queue", "resume", "GID123"])
    assert r2.exit_code == 0 and "Resumed" in r2.output

    r3 = runner.invoke(cli.cli, ["queue", "remove", "GID123"])
    assert r3.exit_code == 0 and "Removed" in r3.output
