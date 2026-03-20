from os import environ
from time import sleep
from typing import Callable
from threading import Thread
from scrapers import Listing, Scraper, EbayScraper, JumiaScraper, NoonScraper
from constants import SERB_API_KEY
from scrapers.read_once_list import ReadOnceList


class CompositeScraper:
    _MAX_SCRAPE_TIME: int | None = None
    _SCRAPE_TIME_CHECK_INCREMENT: int | None = None

    _scraper_initers: list[Callable[[], Scraper]] = [
        lambda: EbayScraper(SERB_API_KEY),
        JumiaScraper,
        NoonScraper
    ]

    def __init__(self) -> None:
        if self._MAX_SCRAPE_TIME is None:
            self._MAX_SCRAPE_TIME = int(environ["MAX_SCRAPE_TIME"])
        if self._SCRAPE_TIME_CHECK_INCREMENT is None:
            self._SCRAPE_TIME_CHECK_INCREMENT = int(environ["SCRAPE_TIME_CHECK_INCREMENT"])

        self._scrapers: list[Scraper] = [
            scraper_initer() for scraper_initer in self._scraper_initers
        ]
        self._product_name: str | None = None
        self._listings: ReadOnceList[Listing] = ReadOnceList()
        self._current_time = 0

    def scrape(self, product_name: str) -> list[Listing]:
        self._product_name = product_name

        threads = [
            Thread(target=self._scrape_using_scraper, args=(scraper,))
            for scraper in self._scrapers
        ]

        for thread in threads:
            thread.start()

        while self._current_time < self._MAX_SCRAPE_TIME:
            sleep(self._SCRAPE_TIME_CHECK_INCREMENT / 1000)
            self._current_time += self._SCRAPE_TIME_CHECK_INCREMENT

        return self._listings.read()

    def _scrape_using_scraper(self, scraper: Scraper):
        scraper.push_to(self._listings)
        scraper.scrape(self._product_name)
