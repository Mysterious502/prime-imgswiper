import httpx
from .scrapers import (
    UnsplashScraper, PixabayScraper,
    WallhavenScraper, VecteezyScraper,
    WallpaperCaveScraper, WallpapersComScraper,
    WallpaperSafariScraper, UHDPaperScraper,
    PixelstalkScraper, StockSnapScraper,
)
from .aggregator import aggregate
from .safety_check import filter_safe_images


class ImgSwiper:
    """
    FINAL: 10 stable, no-API-key sources.
    """

    def __init__(self, client: httpx.AsyncClient = None):
        self._client = client or httpx.AsyncClient()
        self.scrapers = [
            UnsplashScraper(self._client),
            PixabayScraper(self._client),
            WallhavenScraper(self._client),
            VecteezyScraper(self._client),
            WallpaperCaveScraper(self._client),
            WallpapersComScraper(self._client),
            WallpaperSafariScraper(self._client),
            UHDPaperScraper(self._client),
            PixelstalkScraper(self._client),
            StockSnapScraper(self._client),
        ]

    async def swipe(self, query: str, count: int = 5, live_check: bool = False, safety_check: bool = True) -> list[str]:
        raw_urls = await aggregate(self.scrapers, query, count * 2, live_check)
        if safety_check:
            raw_urls = await filter_safe_images(raw_urls, self._client)
        return raw_urls[:count]

    async def close(self):
        await self._client.aclose()