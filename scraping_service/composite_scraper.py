from typing import Callable
from scrapers import Listing, Scraper, EbayScraper, JumiaScraper
from constants import SERB_API_KEY


class CompositeScraper:
    _scraper_initers: list[Callable[[], Scraper]] = [
        lambda: EbayScraper(SERB_API_KEY),
        JumiaScraper,
    ]

    def __init__(self) -> None:
        self._scrapers: list[Scraper] = [
            scraper_initer() for scraper_initer in self._scraper_initers
        ]

    def scrape(self, product_name: str) -> list[Listing]:
        listings: list[Listing] = []
        for scraper in self._scrapers:
            scraper_output = scraper.scrape(product_name)
            listings.extend(scraper_output)
        return listings
