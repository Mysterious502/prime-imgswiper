from .base import BaseScraper
from ..utils import rate_limiter, random_headers
import asyncio
from playwright.async_api import async_playwright

class UnsplashScraper(BaseScraper):
    async def search(self, query: str, max_results: int = 5) -> list[str]:
        await rate_limiter.wait("unsplash.com")
        search_url = f"https://unsplash.com/s/photos/{query.replace(' ', '-')}"
        urls = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=random_headers()["User-Agent"],
                    viewport={"width": 1280, "height": 800}
                )
                page = await context.new_page()
                # networkidle was hanging — Unsplash keeps background
                # requests going (same issue we hit with Pixabay/Pinterest).
                # domcontentloaded + explicit wait is more reliable.
                await page.goto(search_url, timeout=30000, wait_until="domcontentloaded")

                try:
                    await page.wait_for_selector('figure img[srcset]', timeout=20000)
                except Exception:
                    pass  # continue anyway, collect whatever loaded

                for _ in range(2):
                    try:
                        await page.evaluate("window.scrollBy(0, window.innerHeight)")
                        await asyncio.sleep(1)
                    except Exception:
                        break

                img_elements = await page.query_selector_all('figure img[srcset]')
                for img in img_elements:
                    try:
                        srcset = await img.get_attribute("srcset")
                    except Exception:
                        continue
                    if srcset:
                        parts = srcset.strip().split(",")
                        if parts:
                            best = parts[-1].strip().split(" ")[0]
                            if best.startswith("https://images.unsplash.com/") and "profile" not in best:
                                if "w=32" not in best and "w=64" not in best:
                                    urls.append(best)
                    if len(urls) >= max_results:
                        break
                await browser.close()
        except Exception as e:
            print(f"[Unsplash] Error: {e}")
        return urls[:max_results]