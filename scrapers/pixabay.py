from .base import BaseScraper
from ..utils import rate_limiter, random_headers
import asyncio
from playwright.async_api import async_playwright

class PixabayScraper(BaseScraper):
    async def search(self, query: str, max_results: int = 5) -> list[str]:
        await rate_limiter.wait("pixabay.com")
        search_url = f"https://pixabay.com/images/search/{query.replace(' ', '%20')}/"
        urls = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=random_headers()["User-Agent"],
                    viewport={"width": 1280, "height": 800}
                )
                page = await context.new_page()
                # networkidle hangs here — Pixabay keeps background XHR/ads
                # traffic going, so it never goes "idle". domcontentloaded +
                # explicit wait for the actual content is more reliable.
                await page.goto(search_url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_selector("img[srcset]", timeout=15000)
                await page.evaluate("window.scrollBy(0, 500)")
                await asyncio.sleep(1)
                img_elements = await page.query_selector_all("img[srcset]")
                for img in img_elements:
                    srcset = await img.get_attribute("srcset")
                    if srcset:
                        parts = srcset.strip().split(",")
                        if parts:
                            best = parts[-1].strip().split(" ")[0]
                            if best.startswith("https://cdn.pixabay.com/photo/"):
                                urls.append(best)
                    if len(urls) >= max_results:
                        break
                await browser.close()
        except Exception as e:
            print(f"[Pixabay] Error: {e}")
        return urls[:max_results]