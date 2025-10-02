import sys
from click.testing import CliRunner
from anidl import cli
from anidl.utils import parse_selection


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--help"]) 
    assert result.exit_code == 0
    assert "anidl - search and download anime torrents" in result.output


def test_parse_selection():
    assert parse_selection("1,2,5-7", 10) == [1, 2, 5, 6, 7]
    assert parse_selection("3-5,2", 5) == [2, 3, 4, 5]
    assert parse_selection("", 5) == []
