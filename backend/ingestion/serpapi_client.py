import os
import requests
from dotenv import load_dotenv

load_dotenv()


def fetch_shopping_results(query, api_key=None):
    """One Google Shopping search (costs 1 SerpApi search). Never cached."""
    api_key = api_key or os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise ValueError("SERPAPI_API_KEY is not configured")

    response = requests.get(
        "https://serpapi.com/search.json",
        params={"engine": "google_shopping", "q": query, "gl": "us", "hl": "en", "api_key": api_key},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return [r for r in data.get("shopping_results", []) if r.get("extracted_price") is not None]


def search_products(query):
    """Simplified listings for the local /products endpoint (unchanged output)."""
    return [
        {
            "productId": r.get("product_id"),
            "productName": r.get("title"),
            "retailer": r.get("source"),
            "price": r.get("extracted_price"),
            "image": r.get("thumbnail"),
            "url": r.get("product_link"),
        }
        for r in fetch_shopping_results(query)
    ]