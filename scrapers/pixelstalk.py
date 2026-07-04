from .base import BaseScraper
from ..utils import rate_limiter, random_headers
import asyncio
from playwright.async_api import async_playwright


class PixelstalkScraper(BaseScraper):
    """
    NO API KEY — Playwright-based scrape of pixelstalk.net search.
    EXPERIMENTAL, test karke batana.
    """

    BASE_URL = "https://pixelstalk.net/"

    async def search(self, query: str, max_results: int = 5) -> list[str]:
        await rate_limiter.wait("pixelstalk.net")
        search_url = f"{self.BASE_URL}?s={query.replace(' ', '+')}"
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
                    await page.wait_for_selector("img[src*='pixelstalk.net']", timeout=20000)
                except Exception:
                    pass

                for _ in range(4):
                    try:
                        await page.evaluate("window.scrollBy(0, window.innerHeight)")
                        await asyncio.sleep(1.2)
                    except Exception:
                        break

                img_elements = await page.query_selector_all("img[src*='pixelstalk.net']")
                for img in img_elements:
                    src = await img.get_attribute("data-src") or await img.get_attribute("src")
                    if src and src.startswith("http") and "logo" not in src.lower() and src not in urls:
                        urls.append(src)
                    if len(urls) >= max_results:
                        break
                await browser.close()

                if not urls:
                    print("[Pixelstalk] 0 results — page structure may differ from expected.")
        except Exception as e:
            print(f"[Pixelstalk] Error: {e}")

        return urls[:max_results]