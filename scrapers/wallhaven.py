from .base import BaseScraper
from ..utils import rate_limiter, random_headers


class WallhavenScraper(BaseScraper):
    """
    Wallhaven ka apna free public API hai (no key required for basic search,
    SFW results). Isse HTML scrape karne ki zaroorat khatam ho jati hai —
    'a.preview img' selector timeout isi wajah se aa raha tha (Wallhaven
    results ko client-side JS render karta hai jo Playwright ke default
    networkidle wait se pehle complete nahi hota).
    """

    BASE_URL = "https://wallhaven.cc/api/v1/search"

    async def search(self, query: str, max_results: int = 5) -> list[str]:
        await rate_limiter.wait("wallhaven.cc")
        params = {"q": query, "sorting": "relevance"}
        headers = random_headers()
        urls = []

        try:
            resp = await self.client.get(self.BASE_URL, params=params, headers=headers, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[Wallhaven] Error: {e}")
            return []

        for item in data.get("data", []):
            path = item.get("path")  # full-resolution image, not a thumbnail
            if path:
                urls.append(path)
            if len(urls) >= max_results:
                break

        return urls[:max_results]