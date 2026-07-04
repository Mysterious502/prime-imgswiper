from .base import BaseScraper
from ..utils import rate_limiter, random_headers
from playwright.async_api import async_playwright


class VecteezyScraper(BaseScraper):
    """
    Purana selector `img[src*='vecteezy.com']` bohot loose tha — category
    icons, logos, aur UI chrome bhi isi domain se serve hote hain, isliye
    pehla match galat nikal raha tha. Fix: sirf CDN photo-asset path
    (`static.vecteezy.com/system/resources/`) match karo, aur result grid
    load hone ka wait timeout badhao.
    """

    BASE_URL = "https://www.vecteezy.com/free-photos"

    async def search(self, query: str, max_results: int = 5) -> list[str]:
        await rate_limiter.wait("vecteezy.com")
        params = f"?qterm={query.replace(' ', '+')}"
        search_url = self.BASE_URL + params
        urls = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=random_headers()["User-Agent"],
                    viewport={"width": 1280, "height": 800},
                )
                page = await context.new_page()
                await page.goto(search_url, timeout=45000, wait_until="domcontentloaded")

                await page.wait_for_selector(
                    "img[src*='static.vecteezy.com/system/resources']", timeout=20000
                )

                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await page.wait_for_timeout(1200)

                img_tags = await page.query_selector_all(
                    "img[src*='static.vecteezy.com/system/resources']"
                )
                for img in img_tags:
                    src = await img.get_attribute("src")
                    if src and src not in urls:
                        urls.append(src)
                    if len(urls) >= max_results:
                        break
                await browser.close()
        except Exception as e:
            print(f"[Vecteezy] Error: {e}")
        return urls[:max_results]