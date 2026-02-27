from serpapi import Client
from .scraper import Scraper


class EbayScraper(Scraper):
    def __init__(self, api_key) -> None:
        super().__init__()
        self.client = Client(api_key=api_key)

    def scrape(self, product: str) -> list[str]:
        return self.client.search({
            "engine": "ebay",
            "_nkw": product,
        })
