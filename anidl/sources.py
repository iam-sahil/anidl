import ssl
import asyncio
import urllib.parse
from typing import List, Dict, Any

import aiohttp


def get_feeds(mode: str, query: str, resolution: str = "") -> List[str]:
    # If resolution is provided, append it with a space so negative terms (e.g. "-480p -360p")
    # become separate terms in the query parameter. Users should quote the value when
    # passing negative terms on the CLI (e.g. --resolution "-480p -360p").
    q = urllib.parse.quote_plus(query + (" " + resolution if resolution else ""))
    if mode == "hentai":
        return [f"https://www.tokyotosho.info/rss.php?filter=4,12,13&terms={q}&reversepolarity=1"]
    if mode == "jav":
        return [f"https://www.tokyotosho.info/rss.php?filter=15&terms={q}&reversepolarity=1"]
    # anime/default
    feeds = [
        f"https://www.tokyotosho.info/rss.php?filter=1&submitter=subsplease&terms={q}&reversepolarity=1",
        f"https://www.tokyotosho.info/rss.php?filter=1&submitter=erai-raws&terms={q}&reversepolarity=1",
        f"https://www.tokyotosho.info/rss.php?filter=1&terms={q}&reversepolarity=1"
    ]
    return feeds


async def _fetch(session: aiohttp.ClientSession, url: str, timeout: int = 10, retries: int = 2) -> Dict[str, Any]:
    last_exc = None
    for attempt in range(retries + 1):
        try:
            async with session.get(url, timeout=timeout) as resp:
                text = await resp.text()
                return {"url": url, "status": resp.status, "raw": text}
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            last_exc = e
            await asyncio.sleep(0.5 * (attempt + 1))
            continue
    return {"url": url, "status": None, "raw": "", "error": str(last_exc)}


async def fetch_all_feeds(urls: List[str], timeout: int = 10, concurrency: int = 8) -> List[dict]:
    """Fetch all RSS feed URLs concurrently and return list of dicts with url, status, raw, error.

    Uses aiohttp with a reasonable default SSL/TLS connector. If SSL verification needs to be
    disabled for a particular environment, the caller can create a session and call _fetch directly.
    """
    # Create SSL context that verifies certificates by default
    ssl_ctx = ssl.create_default_context()

    connector = aiohttp.TCPConnector(ssl=ssl_ctx, limit_per_host=concurrency)

    timeout_obj = aiohttp.ClientTimeout(total=None)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout_obj) as session:
        sem = asyncio.Semaphore(concurrency)

        async def guarded_fetch(u: str):
            async with sem:
                return await _fetch(session, u, timeout=timeout)

        tasks = [guarded_fetch(u) for u in urls]
        results = await asyncio.gather(*tasks)
        return results

