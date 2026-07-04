import httpx
from urllib.parse import urlsplit
from .utils import random_headers

MAGIC_BYTES = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG\r\n\x1a\n": "png",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
    b"RIFF": "webp",
}

MAX_IMAGE_SIZE = 25 * 1024 * 1024
MIN_IMAGE_SIZE = 100

# Some CDNs use hotlink-protection: they only serve images if the request's
# Referer header matches their own site. A browser sends this automatically
# when you're browsing the page; a raw background request doesn't, so we
# set it explicitly per-domain here.
REFERER_MAP = {
    "i.imgur.com": "https://imgur.com/",
    "staticflickr.com": "https://www.flickr.com/",
}


def _referer_for(url: str) -> str | None:
    host = urlsplit(url).netloc
    for domain, referer in REFERER_MAP.items():
        if domain in host:
            return referer
    return None


async def is_safe_image_url(url: str, client: httpx.AsyncClient, timeout: float = 8.0) -> bool:
    try:
        headers = random_headers()
        referer = _referer_for(url)
        if referer:
            headers["Referer"] = referer

        async with client.stream("GET", url, headers=headers, timeout=timeout, follow_redirects=True) as resp:
            if resp.status_code != 200:
                return False

            content_type = resp.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                return False

            content_length = resp.headers.get("content-length")
            if content_length is not None:
                size = int(content_length)
                if size < MIN_IMAGE_SIZE or size > MAX_IMAGE_SIZE:
                    return False

            chunk = b""
            async for part in resp.aiter_bytes():
                chunk += part
                if len(chunk) >= 16:
                    break

            if not chunk:
                return False

            if chunk.startswith(b"RIFF") and b"WEBP" in chunk[:16]:
                return True

            for magic, _fmt in MAGIC_BYTES.items():
                if magic != b"RIFF" and chunk.startswith(magic):
                    return True

            return False

    except Exception:
        return False


async def filter_safe_images(urls: list[str], client: httpx.AsyncClient, concurrency: int = 8) -> list[str]:
    import asyncio

    semaphore = asyncio.Semaphore(concurrency)

    async def check(url: str):
        async with semaphore:
            return url, await is_safe_image_url(url, client)

    results = await asyncio.gather(*(check(u) for u in urls))
    return [url for url, ok in results if ok]