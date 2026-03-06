"""
defined the classes used to scrape vendors
"""

from .scraper import Scraper
from .listing import Listing

from .ebay import EbayScraper
from .jumia import JumiaScraper


__all__ = ["EbayScraper", "JumiaScraper", "Scraper", "Listing"]
