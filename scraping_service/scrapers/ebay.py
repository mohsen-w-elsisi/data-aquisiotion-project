from serpapi import Client
from .scraper import Scraper, ScrapeException
from .listing import Listing, PriceType


class EbayScraper(Scraper):
    def __init__(self, api_key) -> None:
        super().__init__()
        self.client = Client(api_key=api_key)

        self._product_name: str = None
        self._api_response: dict = None
        self._parsed_results: list[Listing] = None

    def scrape(self, product_name: str):
        self._product_name = product_name
        self._search_using_api()
        self._parse_api_response()
        for listing in self._parsed_results:
            self._listings.push(listing)

    def _search_using_api(self):
        self._api_response = self.client.search(
            {
                "engine": "ebay",
                "_nkw": self._product_name,
            }
        )

    def _parse_api_response(self):
        listings: list[dict] = self._api_response.get("organic_results", [])
        parsed_results = []
        for listing in listings:
            try:
                parsed_results.append(_ListingParser(listing).parse())
            except _ListingParserException:
                continue
        self._parsed_results = parsed_results


class _ListingParser:
    def __init__(self, listing: dict) -> None:
        self.listing = listing

    def parse(self) -> Listing:
        price_type, price, price_range = self._parse_price()
        return Listing(
            name=self.listing["title"],
            url=self.listing["link"],
            image=self.listing["thumbnail"],
            price_type=price_type,
            price=price,
            price_range=price_range,
            vendor="Ebay",
            subvendor=self.listing["seller"]["username"],
            rating=None, # not provided by surpapi
            review_count=None, # not provided by surpapi
        )

    def _parse_price(
        self,
    ) -> tuple[PriceType, float | None, tuple[float, float] | None]:
        unparsed_price: dict = self.listing.get("price", None)
        if unparsed_price is None:
            raise _ListingParserException(
                self.listing, f"Listing is missing price field: {self.listing}"
            )
        if "extracted" in unparsed_price:
            return PriceType.DISCRETE, unparsed_price["extracted"], None
        if "from" in unparsed_price and "to" in unparsed_price:
            return (
                PriceType.RANGE,
                None,
                (
                    unparsed_price["from"]["extracted"],
                    unparsed_price["to"]["extracted"],
                ),
            )
        raise ScrapeException(
            "Ebay", f"unexpected price format returned from surpapi: {unparsed_price}"
        )


class _ListingParserException(Exception):
    def __init__(self, listing, message: str) -> None:
        super().__init__(f"Error parsing listing: {message}\n Listing: {listing}")
