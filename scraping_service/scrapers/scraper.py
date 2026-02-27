from abc import ABC, abstractmethod


class Scraper(ABC):
    """
    defines the standard interface for a scraper. children implement this
    interface for specfic vendors
    """

    @abstractmethod
    def scrape(self, product: str) -> list[str]:
        """
        scrapes the specified vendor and returns a list of relavant results
        """
