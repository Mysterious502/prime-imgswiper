from abc import ABC, abstractmethod
import httpx

class BaseScraper(ABC):
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[str]:
        """Returns list of image URLs."""
        pass