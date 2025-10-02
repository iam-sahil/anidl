from typing import List, Dict
from datetime import datetime, timedelta
import time
import feedparser
from difflib import SequenceMatcher


TRUSTED_UPLOADERS = {"subsplease": 0.9, "erai-raws": 0.8, "varyg1001": 0.7}


def _parse_size_from_summary(summary: str) -> str:
    # naive extraction: look for "Size: 123 MB" or similar
    import re

    if not summary:
        return ""
    m = re.search(r"Size:\s*([0-9\.]+\s*[GMK]B)", summary, re.IGNORECASE)
    if m:
        return m.group(1)
    return ""


def _parse_seeders_from_summary(summary: str) -> int:
    import re

    if not summary:
        return 0
    m = re.search(r"Seeders?:\s*(\d+)", summary, re.IGNORECASE)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return 0
    return 0


def health_score(seeders: int, published: datetime, uploader: str) -> float:
    days_old = max(1.0, (datetime.utcnow() - published).days)
    uploader_trust = TRUSTED_UPLOADERS.get(uploader.lower(), 0.5)
    score = seeders * 0.7 + (1.0 / days_old) * 0.2 + uploader_trust * 0.1
    return score


def _is_similar(a: str, b: str, threshold: float = 0.8) -> bool:
    return SequenceMatcher(None, a, b).ratio() >= threshold


def parse_feeds(raw_feeds: List[dict], max_results: int = 50, resolve_magnets: bool = False) -> List[Dict]:
    """Parse raw feed fetch results into structured items.

    raw_feeds: list of dicts containing 'url' and 'raw' (feed XML/text)
    Returns list of items with keys: title, size, uploader, date (datetime), seeders, torrent_url, health
    """
    items = []
    seen_titles = []

    for feed in raw_feeds:
        raw = feed.get("raw") or ""
        url = feed.get("url")
        if not raw:
            continue
        try:
            parsed = feedparser.parse(raw)
        except Exception:
            # If raw is actually a URL (when fetch_all_feeds wasn't used), try parsing URL directly
            parsed = feedparser.parse(url or "")

        for entry in getattr(parsed, "entries", []):
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            uploader = entry.get("author", entry.get("uploader", "")) or ""
            # many RSS feeds use "submitter" or "author" to indicate uploader/uploader account
            submitter = entry.get("submitter", entry.get("author", uploader)) or uploader or "Anonymous"

            # published date
            published = None
            if entry.get("published_parsed"):
                published = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            else:
                published = datetime.utcnow()

            size = _parse_size_from_summary(summary) or entry.get("size") or ""
            seeders = _parse_seeders_from_summary(summary) or int(entry.get("seeders", 0) or 0)

            # determine torrent/magnet link
            torrent_url = ""
            if entry.get("links"):
                for l in entry.links:
                    href = l.get("href")
                    if href and (href.endswith(".torrent") or href.startswith("magnet:")):
                        torrent_url = href
                        break

            item = {
                "title": title,
                "size": size,
                "uploader": uploader,
                "submitter": submitter,
                "date": published,
                "seeders": seeders,
                "torrent_url": torrent_url,
                "source": url,
            }
            # dedupe by similar title
            duplicate = False
            for t in seen_titles:
                if _is_similar(t, title):
                    duplicate = True
                    break
            if duplicate:
                continue
            seen_titles.append(title)

            item["health"] = health_score(seeders, published, uploader or "")
            items.append(item)

    # sort by date desc
    items.sort(key=lambda x: x.get("date", datetime.min), reverse=True)
    # Optionally resolve magnet metadata (best-effort) to fill missing size/title
    if resolve_magnets:
        try:
            # lazy import to avoid top-level dependency / circular import
            from .downloader import resolve_magnet as _resolve_magnet

            for it in items:
                if it.get("torrent_url", "").startswith("magnet:"):
                    # only attempt when size or title missing
                    if not it.get("size") or not it.get("title"):
                        try:
                            meta = _resolve_magnet(it.get("torrent_url"), timeout=5)
                            if meta:
                                if not it.get("title") and meta.get("title"):
                                    it["title"] = meta.get("title")
                                if not it.get("size") and meta.get("size"):
                                    # convert bytes to a human-friendly string if numeric
                                    s = meta.get("size")
                                    try:
                                        # aria2 returns bytes; convert to MB/GB
                                        s_n = int(s)
                                        if s_n > 1024 * 1024 * 1024:
                                            it["size"] = f"{s_n / (1024**3):.2f} GB"
                                        else:
                                            it["size"] = f"{s_n / (1024**2):.0f} MB"
                                    except Exception:
                                        it["size"] = str(s)
                        except Exception:
                            # best-effort: ignore failures
                            pass
        except Exception:
            # unable to import resolver or run metadata fetch - ignore
            pass

    return items[:max_results]

