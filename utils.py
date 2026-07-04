import asyncio
import random
from fake_useragent import UserAgent

ua = UserAgent()


async def retry_with_backoff(func, retries=3, base_delay=2.0):
    """
    Runs an async no-arg callable, retrying with exponential backoff on
    failure/empty result. Used for sources that intermittently
    rate-limit/block during frequent testing (Pexels, Openverse) — a
    short wait + retry often succeeds where an immediate retry wouldn't.
    """
    last_exc = None
    for attempt in range(retries):
        try:
            result = await func()
            if result:  # non-empty result counts as success
                return result
        except Exception as e:
            last_exc = e
        if attempt < retries - 1:
            await asyncio.sleep(base_delay * (2 ** attempt))
    if last_exc:
        print(f"[retry_with_backoff] All {retries} attempts failed: {last_exc}")
    return []


class DomainRateLimiter:
    """Har domain ke liye minimum delay enforce karta hai."""
    def __init__(self, default_delay=2.0):
        self.delay = default_delay
        self.last_call = {}

    async def wait(self, domain):
        loop = asyncio.get_event_loop()
        now = loop.time()
        if domain in self.last_call:
            elapsed = now - self.last_call[domain]
            if elapsed < self.delay:
                await asyncio.sleep(self.delay - elapsed)
        self.last_call[domain] = loop.time()

rate_limiter = DomainRateLimiter()

def random_headers():
    return {
        "User-Agent": ua.random,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }