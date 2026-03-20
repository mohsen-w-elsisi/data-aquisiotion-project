from threading import Thread
from re import compile as compileRe
from typing import Optional
from requests import get as http_get
from bs4 import BeautifulSoup
from bs4.element import Tag as HtmlTag
from .listing import PriceType
from .scraper import Scraper
from .listing import Listing


class JumiaScraper(Scraper):
    def __init__(self) -> None:
        super().__init__()
        self._urls: list[str] = []

    def scrape(self, product_name: str):
        self._urls = _JumiaSearcher().get_listing_urls(product_name)
        self._extract_info_from_urls()

    def _extract_info_from_urls(self):
        threads = [Thread(target=self._scrape_url, args=(url,)) for url in self._urls]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    def _scrape_url(self, url: str):
        listing = _UrlToListingConverter().convert(url)
        self._listings.push(listing)


class _JumiaSearcher:
    _URL_BASE = "https://www.jumia.com.eg"
    _LISTING_CARD_SELECTOR = "[data-catalog=true] article"
    _LISTING_LINK_SELECTOR = "a.core"

    def __init__(self) -> None:
        self._product_name: str = None
        self._page: BeautifulSoup = None
        self._listing_links: list[str] = None

    def get_listing_urls(self, product_name: str) -> list[str]:
        self._product_name = product_name
        self._load_page()
        self._find_listing_links()
        return self._listing_links

    def _load_page(self):
        res = http_get(self._search_url)
        self._page = BeautifulSoup(res.content, "html.parser")

    @property
    def _search_url(self):
        url_friendly_topic_name = self._product_name.replace(" ", "+")
        return f"{self._URL_BASE}/catalog/?q={url_friendly_topic_name}"

    def _find_listing_links(self):
        listing_cards = self._page.select(self._LISTING_CARD_SELECTOR)
        listing_anchors = [
            listing_card.select_one("a.core") for listing_card in listing_cards
        ]
        listing_link_paths = [anchor["href"] for anchor in listing_anchors]
        self._listing_links = [f"{self._URL_BASE}{path}" for path in listing_link_paths]


class _UrlToListingConverter:
    _REQUEST_TIMEOUT = 2

    def __init__(self):
        self._url: str
        self._page: BeautifulSoup
        self._listing_data: _listingPageDataExtractor
        self._listing: Listing

    def convert(self, listing_url: str) -> Listing:
        print(f"converting {listing_url}")
        self._url = listing_url
        self._load_page()
        self._listing_data = _listingPageDataExtractor(self._page)
        self._construct_listing()
        return self._listing

    def _load_page(self):
        res = http_get(self._url, timeout=self._REQUEST_TIMEOUT)
        self._page = BeautifulSoup(res.content, "html.parser")

    def _construct_listing(self):
        self._listing = Listing(
            name=self._listing_data.name,
            url=self._url,
            image=self._listing_data.image,
            price_type=PriceType.DISCRETE,
            price=self._listing_data.price,
            price_range=None,
            vendor="Jumia",
            subvendor=None,
            rating=self._listing_data.rating,
            review_count=self._listing_data.review_count,
        )


class _listingPageDataExtractor:
    _price_regex = compileRe(r"EGP [\d,\.]+")
    _rating_regex = compileRe(r"[\d.]+")
    _review_count_regex = compileRe(r"[\d|,]+")

    def __init__(self, page: BeautifulSoup):
        self._page = page

    @property
    def name(self):
        return self._page.select_one("h1").text

    @property
    def image(self):
        return self._page.select_one("div#imgs img")["data-src"]

    @property
    def price(self) -> Optional[float]:
        match = self._price_regex.search(self._page.text)
        if match is not None:
            price_str = match.group().replace("EGP ", "").replace(",", "")
            return float(price_str)
        return None

    @property
    def rating(self) -> Optional[float]:
        stars_element = self._page.select_one(".stars")
        if type(stars_element) != HtmlTag:
            return None
        if not stars_element.text.endswith("out of 5"):
            return None
        rating_num_text = self._rating_regex.search(stars_element.text).group(0)
        return float(rating_num_text) if rating_num_text != "0" else None

    @property
    def review_count(self) -> Optional[int]:
        anchors = self._page.select("a")
        try:
            reviews_anchor = [
                anchor
                for anchor in anchors
                if anchor["href"].startswith("/catalog/productratingsreviews")
            ][0]
        except IndexError:
            return 0 if "No ratings available" in self._page.text else None
        review_num_str = (
            self._review_count_regex.search(reviews_anchor.text)
            .group()
            .replace(",", "")
        )
        return int(review_num_str)
