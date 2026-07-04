from .base import BaseScraper
from ..utils import rate_limiter, random_headers
import asyncio
from playwright.async_api import async_playwright


class WallpapersComScraper(BaseScraper):
    """
    FIX: default wait_for_selector waits for an element to become fully
    "visible" (in viewport, non-zero opacity, etc). With 91 matching
    thumbnails on a lazy-loaded grid, none may hit "visible" state fast
    enough, causing intermittent timeouts even though images already
    exist in the DOM. Using state="attached" instead — just checks the
    element exists in the DOM, which is all we actually need since we
    only read the src/data-src attribute, not click or see it.
    """

    BASE_URL = "https://wallpapers.com/search"

    async def search(self, query: str, max_results: int = 5) -> list[str]:
        await rate_limiter.wait("wallpapers.com")
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

                try:
                    await page.wait_for_selector(
                        "img[src*='wallpapers.com']", timeout=20000, state="attached"
                    )
                except Exception:
                    pass  # continue anyway, collect whatever loaded

                for _ in range(4):
                    try:
                        await page.evaluate("window.scrollBy(0, window.innerHeight)")
                        await asyncio.sleep(1.2)
                    except Exception:
                        break

                img_elements = await page.query_selector_all("img[src*='wallpapers.com']")
                for img in img_elements:
                    src = await img.get_attribute("data-src") or await img.get_attribute("src")
                    if src and src.startswith("http") and "logo" not in src.lower() and src not in urls:
                        urls.append(src)
                    if len(urls) >= max_results:
                        break
                await browser.close()
        except Exception as e:
            print(f"[WallpapersCom] Error: {e}")

        return urls[:max_results]