from abc import ABC, abstractmethod
from .listing import Listing
from .read_once_list import ReadOnceList


class Scraper(ABC):
    """
    defines the standard interface for a scraper. children implement this
    interface for specific vendors
    """

    def __init__(self) -> None:
        self._listings: ReadOnceList[Listing] | None = None

    def push_to(self, push_to_list: ReadOnceList[Listing]) -> None:
        self._listings = push_to_list


    @abstractmethod
    def scrape(self, product_name: str):
        """
        scrapes the specified vendor and returns a list of relavant results
        """

    def terminate(self):
        pass


class ScrapeException(Exception):
    """
    defines the standard exception for scrapers. children can raise this
    exception when they encounter an error during scraping
    """

    def __init__(self, vendor: str, message: str) -> None:
        super().__init__(f"Error scraping {vendor}: {message}")
        self.vendor = vendor
        self.message = message
