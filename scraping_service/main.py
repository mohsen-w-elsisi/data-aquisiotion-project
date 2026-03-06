from flask import Flask, request
from composite_scraper import CompositeScraper

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
    listings = CompositeScraper().scrape(product_name)
    listings_json = [listing.to_json() for listing in listings]
    return listings_json, 200


if __name__ == "__main__":
    server.run()
