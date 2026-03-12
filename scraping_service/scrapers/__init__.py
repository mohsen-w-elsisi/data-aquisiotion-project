"""
defined the classes used to scrape vendors
"""

from .scraper import Scraper
from .listing import Listing

from .ebay import EbayScraper
from .jumia import JumiaScraper
from .noon import NoonScraper


__all__ = ["EbayScraper", "JumiaScraper", "NoonScraper", "Scraper", "Listing"]
