from time import sleep
from typing import Optional, Callable, TypeVar, Any
from re import search

from selenium import webdriver
from selenium.common import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from .listing import Listing, PriceType
from .scraper import Scraper
from .web_driver_management import WebDriverTask, WebDriverOrchestrater


class NoonScraper(Scraper):
    def __init__(self) -> None:
        super().__init__()
        self._product_name = ""
        self._listing_urls: list[str] = []

    def scrape(self, product_name: str):
        self._product_name = product_name
        self._get_listing_urls()
        self._scrape_urls()

    def _get_listing_urls(self):
        driver = webdriver.Chrome()
        self._listing_urls = _NoonSearcher(driver) \
            .get_listing_urls(self._product_name)[:15]
        driver.close()

    def _scrape_urls(self):
        tasks = [
            WebDriverTask(url, lambda drv: _ListingLinkScraper(drv).scrape())
            for url in self._listing_urls]
        WebDriverOrchestrater(tasks, self._listings).start()


class _NoonSearcher:
    _BASE_URL = "https://www.noon.com/egypt-en"
    _PRODUCT_ANCHOR_SELECTOR = '[data-qa="plp-product-box"] a'

    def __init__(self, driver: WebDriver):
        self._product_name: str = ""
        self._driver = driver
        self._listing_urls: list[str] = []

    def get_listing_urls(self, product_name: str):
        self._product_name = product_name
        self._driver.get(self._BASE_URL)
        self._navigate_to_results_page()
        sleep(3)
        self._scrape_listing_urls()
        return self._listing_urls

    def _navigate_to_results_page(self):
        search_input = self._driver.find_element(By.ID, "search-input")
        search_input.send_keys(self._product_name)
        search_input.send_keys(Keys.RETURN)

    def _scrape_listing_urls(self):
        product_anchors = self._driver.find_elements(
            By.CSS_SELECTOR, self._PRODUCT_ANCHOR_SELECTOR
        )
        self._listing_urls = [
            anchor.get_attribute("href") for anchor in product_anchors
        ]


T = TypeVar("T")


def _skip_if_element_not_found(func: Callable[[Any], T]):
    def wrapper(self: Any) -> T:
        try:
            return func(self)
        except StaleElementReferenceException:
            return None
        except NoSuchElementException:
            return None

    return wrapper


class _ListingLinkScraper:
    def __init__(self, driver: WebDriver):
        self._listing: Listing
        self._driver = driver

    def scrape(self) -> Listing:
        self._construct_listing()
        return self._listing

    def _construct_listing(self):
        self._listing = Listing(
            name=self.title,
            image=self.image,
            url=self._driver.current_url,
            price_type=PriceType.DISCRETE,
            price=self.price,
            price_range=None,
            vendor="Noon",
            subvendor=self.subvendor,
            rating=self.rating,
            review_count=self.review_count,
        )

    @property
    @_skip_if_element_not_found
    def title(self) -> Optional[str]:
        title_element = self._driver.find_element(By.TAG_NAME, "h1")
        return title_element.text

    @property
    @_skip_if_element_not_found
    def price(self):
        price_container: WebElement = self._driver.find_element(
            By.CSS_SELECTOR, '[data-qa="div-price-now"]'
        )
        price_text = price_container.find_elements(By.XPATH, ".//*")[1].text
        return float(price_text)

    @property
    @_skip_if_element_not_found
    def rating(self):
        rating_element = self._driver.find_element(
            By.CLASS_NAME, "RatingPreviewStarV2-module-scss-module__0_8vQW__text"
        )
        return float(rating_element.text)

    @property
    @_skip_if_element_not_found
    def review_count(self):
        review_count_element = self._driver.find_element(
            By.CLASS_NAME,
            "NoonRatingsBasedOnTitle-module-scss-module__aAM0SW__basedOnInfoCtrLoader",
        )
        review_count_text = search(r"[\d,]+", review_count_element.text)
        review_count_text = review_count_text.group(0).replace(",", "").strip()
        return int(review_count_text)

    @property
    @_skip_if_element_not_found
    def image(self):
        image_element = self._driver.find_element(
            By.CLASS_NAME, "GalleryV2-module-scss-module__hlK6zG__imageMagnify"
        )
        return image_element.get_attribute("src")

    @property
    @_skip_if_element_not_found
    def subvendor(self):
        subvendor_element = self._driver.find_element(
            By.CLASS_NAME, "PartnerRatingsV2-module-scss-module__1CV-Aa__soldBy"
        )
        return subvendor_element.text
