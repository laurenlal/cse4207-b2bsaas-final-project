import os
import requests
from dotenv import load_dotenv

load_dotenv()


def search_products(query):
    api_key = os.getenv("SERPAPI_API_KEY")

    if not api_key:
        raise ValueError("SERPAPI_API_KEY is not configured")

    response = requests.get(
        "https://serpapi.com/search.json",
        params={
            "engine": "google_shopping",
            "q": query,
            "gl": "us",
            "hl": "en",
            "api_key": api_key,
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise RuntimeError(data["error"])

    products = []

    for item in data.get("shopping_results", []):
        price = item.get("extracted_price")

        if price is None:
            continue

        products.append({
            "productId": item.get("product_id"),
            "productName": item.get("title"),
            "retailer": item.get("source"),
            "price": price,
            "image": item.get("thumbnail"),
            "url": item.get("product_link"),
        })

    return products