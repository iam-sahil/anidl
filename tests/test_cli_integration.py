from click.testing import CliRunner
from anidl import cli
import re


SIMPLE_RSS = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Test Anime - Episode 01</title>
      <description>Size: 200 MB - Seeders: 20</description>
      <author>subsplease</author>
      <link>magnet:?xt=urn:btih:FAKE</link>
      <pubDate>Wed, 17 Sep 2025 12:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>
"""


def _normalize_output(text: str) -> str:
    # remove ANSI escape sequences and collapse whitespace for stable assertions
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    # remove common box-drawing and table characters produced by rich
    text = re.sub(r"[\u2500-\u257F\|┌┐└┘├┤┬┴┼─│]+", " ", text)
    # remove other punctuation that may stick to headers
    text = re.sub(r"[\,\:\-\(\)]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def test_cli_search_dry_run(monkeypatch):
    runner = CliRunner()

    async def fake_fetch(urls, timeout=10, concurrency=8):
        return [{"url": "http://test", "raw": SIMPLE_RSS}]

    # patch the function reference used by cli (cli imported fetch_all_feeds directly)
    monkeypatch.setattr(cli, "fetch_all_feeds", fake_fetch)

    result = runner.invoke(cli.cli, ["search", "test", "--dry-run"])
    assert result.exit_code == 0

    normalized = _normalize_output(result.output)
    # Assert essential table headers are present (some columns may be elided by width)
    essential = {"#", "Size", "Uploader"}
    assert essential.issubset(set(normalized.split()))

    # ensure uploader appears
    assert "subsplease" in normalized
