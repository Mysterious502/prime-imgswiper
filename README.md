# Prime ImgSwiper 🖼️

A Python library that aggregates high-quality image and wallpaper URLs from **10 different sources** — no API keys, no logins, no signup required.

Just give it a search query, and it returns a deduplicated, verified list of direct image URLs pulled concurrently from multiple free platforms.

## ✨ Features

- **10 built-in sources**, zero configuration required
- **No API keys** — works out of the box
- **Concurrent scraping** — all sources are queried in parallel via `asyncio`
- **Automatic deduplication** — catches duplicate images even when the same photo is served with different crop/size parameters
- **Built-in safety verification** — every URL is checked for a valid image content-type and correct file signature (magic bytes) before being returned, so you never get broken links or disguised files
- **Simple async API** — one method call to get results

## 📦 Sources

| Source | Type |
|---|---|
| Unsplash | Free stock photos |
| Pixabay | Free stock photos |
| Wallhaven | Wallpapers |
| Vecteezy | Stock photos & vectors |
| Wallpaper Cave | Wallpapers |
| Wallpapers.com | Wallpapers |
| WallpaperSafari | Wallpapers |
| UHDPaper | 4K wallpapers |
| PixelStalk | Wallpapers |
| StockSnap | CC0 free stock photos |

## 🚀 Installation

```bash
git clone https://github.com/yourusername/prime-imgswiper.git
cd prime-imgswiper
pip install -r requirements.txt
playwright install chromium
```

## 🔧 Usage

```python
import asyncio
from prime_imgswiper import ImgSwiper

async def main():
    swiper = ImgSwiper()

    results = await swiper.swipe("beautiful sunset", count=20)

    for url in results:
        print(url)

    await swiper.close()

asyncio.run(main())
```

### `swipe()` parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | — | Search term |
| `count` | `int` | `5` | Number of results to return |
| `live_check` | `bool` | `False` | If `True`, sends a HEAD request to every URL before returning to confirm it's reachable (slower, extra network calls) |
| `safety_check` | `bool` | `True` | Verifies each image's content-type and file signature before returning it |

## 🛡️ How the safety check works

Every URL that comes out of the scrapers is verified before being handed back to you:

1. **Content-Type check** — confirms the server actually reports an image
2. **Magic bytes check** — reads the first few bytes of the actual file and confirms they match a real image format (JPEG/PNG/GIF/WebP), so a mislabeled or disguised file can't slip through
3. **Size sanity check** — rejects anything suspiciously tiny (broken placeholder) or unreasonably huge

This means Discord bots, browser extensions, or any downstream app using this library only ever receive genuine, working image links.

## ⚠️ Notes & Limitations

- This library works by reading each source's public search pages. Sites occasionally change their page structure, which can cause a source to temporarily return fewer results — this is normal for any scraping-based tool and not indicative of a bug.
- Some well-known platforms (Google Images, Pinterest, Reddit) are intentionally **not included**. They use active anti-automation measures (CAPTCHA challenges, mandatory login walls, bot-detection systems) — this library does not attempt to bypass those protections.
- Respect each source's terms of service and rate limits when using this tool at scale.

## 🙌 Credits

Built as a personal project to explore concurrent web scraping, async Python, and building resilient multi-source aggregators.
