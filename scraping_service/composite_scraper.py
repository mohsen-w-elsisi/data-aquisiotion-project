from typing import Callable
from threading import Thread
from scrapers import Listing, Scraper, EbayScraper, JumiaScraper, NoonScraper
from constants import SERB_API_KEY


class CompositeScraper:
    _scraper_initers: list[Callable[[], Scraper]] = [
        lambda: EbayScraper(SERB_API_KEY),
        JumiaScraper,
        NoonScraper
    ]

    def __init__(self) -> None:
        self._scrapers: list[Scraper] = [
            scraper_initer() for scraper_initer in self._scraper_initers
        ]
        self._product_name: str
        self._listings: list[Listing] = []

    def scrape(self, product_name: str) -> list[Listing]:
        self._product_name = product_name
        
        threads = [
            Thread(target=self._scrape_using_scraper, args=(scraper,))
            for scraper in self._scrapers
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        return self._listings

    def _scrape_using_scraper(self, scraper: Scraper):
        listing = scraper.scrape(self._product_name)
        self._listings.extend(listing)
