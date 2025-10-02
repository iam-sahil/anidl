from anidl import parser
from datetime import datetime, timedelta


def _make_feed_entry(title: str, summary: str, author: str, published: datetime):
    # Create a minimal RSS entry structure that feedparser.parse can accept
    return {
        "title": title,
        "summary": summary,
        "author": author,
        "published_parsed": published.timetuple(),
        "links": [{"href": "magnet:?xt=urn:btih:FAKE"}],
    }


def test_parse_size_and_seeders_and_health():
    now = datetime.utcnow()
    summary = "Some release - Size: 123 MB - Seeders: 15"
    entry = _make_feed_entry("Test Title", summary, "subsplease", now)
    raw_feed = {"url": "http://example.com/feed", "raw": ""}

    # We will bypass feedparser by constructing a fake parsed structure
    parsed = {"entries": [entry]}

    # monkeypatching feedparser.parse by directly calling internal logic is cumbersome here,
    # so call parse_feeds with a feed that has the raw equal to an empty string; parse_feeds will skip
    # that, so instead directly test helper functions
    size = parser._parse_size_from_summary(summary)
    seeders = parser._parse_seeders_from_summary(summary)
    assert size.lower().endswith("mb")
    assert seeders == 15

    # health score should be > 0 and respect uploader trust (subsplease is trusted)
    score = parser.health_score(seeders, now - timedelta(days=1), "subsplease")
    assert score > 0


def test_dedupe_titles():
    now = datetime.utcnow()
    raw1 = {"url": "u1", "raw": ""}
    raw2 = {"url": "u2", "raw": ""}
    # Use similar titles to trigger dedupe function directly via _is_similar
    assert parser._is_similar("My Anime Episode 01", "My Anime Ep 01")
