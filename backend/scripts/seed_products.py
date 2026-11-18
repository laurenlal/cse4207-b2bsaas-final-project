"""Load ingestion/catalog.json into the Products table. Run from backend/:
    python -m scripts.seed_products
Safe to re-run after editing catalog.json: it never resets trackingStartedAt.
"""
import json
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from shared import database  # noqa: E402  (after load_dotenv so AWS_REGION is set)

CATALOG = Path(__file__).resolve().parents[1] / "ingestion" / "catalog.json"
CONDITIONS = ("new", "refurbished", "used")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def load_catalog(path=CATALOG):
    """Products from catalog.json with listingId added to every listing (same format as the mock)."""
    products = json.loads(Path(path).read_text())["products"]
    for product in products:
        for listing in product["listings"]:
            if listing["condition"] not in CONDITIONS:
                raise ValueError(f"{product['productId']}: bad condition {listing['condition']!r}")
            listing["listingId"] = f"{product['productId']}:{slug(listing['retailer'])}:{listing['condition']}"
    return products


def main():
    for product in load_catalog():
        database.upsert_product(product)
        print("seeded", product["productId"], f"({len(product['listings'])} listings)")


if __name__ == "__main__":
    main()
