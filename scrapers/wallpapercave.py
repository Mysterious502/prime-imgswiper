from .base import BaseScraper
from ..utils import rate_limiter, random_headers
import asyncio
from playwright.async_api import async_playwright


class WallpaperCaveScraper(BaseScraper):
    """
    Selector was correct (got 1 result) but not enough scrolling to trigger
    lazy-load of more thumbnails. Increased scroll iterations + wait time.
    """

    BASE_URL = "https://wallpapercave.com/search"

    async def search(self, query: str, max_results: int = 5) -> list[str]:
        await rate_limiter.wait("wallpapercave.com")
        search_url = f"{self.BASE_URL}?q={query.replace(' ', '+')}"
        urls = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=random_headers()["User-Agent"],
                    viewport={"width": 1280, "height": 800},
                )
                page = await context.new_page()
                await page.goto(search_url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_selector("img[src*='wallpapercave.com']", timeout=15000)

                # More aggressive scrolling — site lazy-loads thumbnails
                # progressively as you scroll, one scroll wasn't enough.
                for _ in range(6):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await asyncio.sleep(1.2)

                img_elements = await page.query_selector_all("img[src*='wallpapercave.com']")
                for img in img_elements:
                    src = await img.get_attribute("data-src") or await img.get_attribute("src")
                    if src and src.startswith("http") and "logo" not in src.lower():
                        if src not in urls:
                            urls.append(src)
                    if len(urls) >= max_results:
                        break
                await browser.close()
        except Exception as e:
            print(f"[WallpaperCave] Error: {e}")

        return urls[:max_results]