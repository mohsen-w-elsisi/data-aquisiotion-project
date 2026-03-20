from os import environ

from dotenv import load_dotenv
from flask import Flask, request
from composite_scraper import CompositeScraper
import cache

server = Flask(__name__)


@server.route("/api")
def hello():
    return "hello", 200


@server.route("/api/search")
def search():
    try:
        product_name = request.args["product_name"]
    except KeyError:
        return "Must include product_name parameter", 400
    return _search(product_name), 200


def _search(product_name: str) -> dict:
    should_use_cache = bool(int(environ["ENABLE_CACHE"]))
    cached_search_results = cache.get_cached(product_name)
    if cached_search_results is not None:
        return cached_search_results
    else:
        listings = CompositeScraper().scrape(product_name)
        listings_json = [listing.to_json() for listing in listings]
        cache.set_cached(product_name, listings_json)
        return listings_json


if __name__ == "__main__":
    print(load_dotenv())
    server.run()
