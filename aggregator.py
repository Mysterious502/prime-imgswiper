import asyncio
import random
from urllib.parse import urlsplit
import httpx


def _dedup_key(url: str) -> str:
    """
    Same photo, different crop/size query params (jaise Pexels
    ?h=153&w=171 vs ?h=204&w=228) ko duplicate treat karne ke liye
    path-only key banate hain. Query string ignore.
    """
    parts = urlsplit(url)
    return f"{parts.netloc}{parts.path}"


def deduplicate(urls: list[str]) -> list[str]:
    seen = set()
    unique = []
    for url in urls:
        key = _dedup_key(url)
        if key not in seen:
            seen.add(key)
            unique.append(url)
    return unique


async def aggregate(scrapers, query: str, count: int = 5, live_check: bool = False) -> list[str]:
    tasks = [scraper.search(query, max_results=count) for scraper in scrapers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_urls = []
    for res in results:
        if isinstance(res, list):
            all_urls.extend(res)

    unique = deduplicate(all_urls)

    if live_check:
        async with httpx.AsyncClient() as client:
            valid = []
            for url in unique:
                try:
                    r = await client.head(url, timeout=5.0)
                    if r.status_code == 200:
                        valid.append(url)
                except Exception:
                    pass
            unique = valid

    random.shuffle(unique)
    return unique[:count]