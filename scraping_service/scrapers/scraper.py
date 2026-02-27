from abc import ABC, abstractmethod
from .listing import Listing


class Scraper(ABC):
    """
    defines the standard interface for a scraper. children implement this
    interface for specfic vendors
    """

    @abstractmethod
    def scrape(self, product_name: str) -> list[Listing]:
        """
        scrapes the specified vendor and returns a list of relavant results
        """


class ScrapeException(Exception):
    """
    defines the standard exception for scrapers. children can raise this
    exception when they encounter an error during scraping
    """

    def __init__(self, vendor: str, message: str) -> None:
        super().__init__(f"Error scraping {vendor}: {message}")
        self.vendor = vendor
        self.message = message
