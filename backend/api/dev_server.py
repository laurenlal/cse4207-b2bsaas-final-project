"""Mock Application Programming Interface (API) for frontend development.
Makes ZERO SerpApi calls and needs no API key.

Run from backend/:
    python -m uvicorn api.dev_server:app --reload --port 8001

/health and /products mirror the real API in api/main.py.
/wishlist and /wishlist/{productId} are PROPOSED endpoints for the dashboard. They don't
exist in the real API yet; the real versions (reading DynamoDB, with statistics computed in
shared/analytics.py) should match these response shapes so the frontend doesn't change.

All data is fake and deterministic: generated from a fixed seed, so prices look the same on
every reload, but timestamps are anchored to "now". Set MOCK_TRACKING_DAYS (1-30) to preview
the "tracking for fewer than 30 days" state the demo will actually be in.
"""

import asyncio
import os
import random
import re
import statistics
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Best2Buy Mock API (dev only)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

LATENCY_MS = int(os.getenv("MOCK_LATENCY_MS", "300"))  # simulate network delay
TRACKING_DAYS = min(max(int(os.getenv("MOCK_TRACKING_DAYS", "30")), 1), 30)
INTERVAL_HOURS = 24  # matches the planned EventBridge schedule
DROP_THRESHOLD = 0.05  # a drop of 5% or more versus the previous observation

# Used products are cheaper than new ones, so scale the base price by condition.
CONDITION_FACTOR = {"new": 1.0, "refurbished": 0.78, "used": 0.66}

# Placeholder products. Swap in the real tracked products once they're chosen.
CATALOG = [
    {"productId": "sony-wh1000xm5", "productName": "Sony WH-1000XM5 Wireless Headphones",
     "basePrice": 348.00, "color": "#16213E",
     "offers": [("Best Buy", "new"), ("Walmart", "new"), ("Target", "new"),
                ("Amazon.com", "new"), ("Back Market", "refurbished"), ("eBay", "used")]},
    {"productId": "airpods-pro-2", "productName": "Apple AirPods Pro (2nd Generation)",
     "basePrice": 249.00, "color": "#3A5BA0",
     "offers": [("Best Buy", "new"), ("Walmart", "new"), ("Target", "new"),
                ("Back Market", "refurbished")]},
    {"productId": "switch-oled", "productName": "Nintendo Switch OLED Model",
     "basePrice": 349.99, "color": "#B3262E",
     "offers": [("Best Buy", "new"), ("Walmart", "new"), ("Target", "new"),
                ("GameStop", "used")]},
    {"productId": "ipad-10", "productName": "Apple iPad 10th Generation 64GB",
     "basePrice": 349.00, "color": "#2B7A78",
     "offers": [("Best Buy", "new"), ("Walmart", "new"), ("Target", "new"),
                ("Amazon.com", "new"), ("Back Market", "refurbished")]},
]

# This listing's latest observation is forced to drop, so the drop UI always has data.
FORCED_DROP = ("sony-wh1000xm5", "Walmart", 0.12)


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _listing_id(product_id, retailer, condition):
    return f"{product_id}:{_slug(retailer)}:{condition}"


def _image(product):
    """Offline-friendly placeholder image (an inline SVG), so mock mode needs no network."""
    initials = "".join(w[0] for w in product["productName"].split()[:2]).upper()
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'>"
        f"<rect width='160' height='160' fill='{product['color']}'/>"
        "<text x='80' y='98' font-size='56' font-family='sans-serif' font-weight='700' "
        f"text-anchor='middle' fill='white'>{initials}</text></svg>"
    )
    return "data:image/svg+xml;utf8," + quote(svg)


def _now_floor():
    """Current time rounded down to the observation interval, so data is stable between reloads."""
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    return now - timedelta(hours=now.hour % INTERVAL_HOURS)


def _history(product, retailer, condition):
    """Deterministic price random walk for one listing, oldest first."""
    rng = random.Random(f"{product['productId']}|{retailer}|{condition}")
    base = product["basePrice"] * CONDITION_FACTOR[condition]
    steps = TRACKING_DAYS * 24 // INTERVAL_HOURS + 1
    end = _now_floor()
    price = base * rng.uniform(0.97, 1.08)
    rows = []

    for i in range(steps):
        if rng.random() < 0.12:  # occasional sale or bounce-back
            price *= rng.choice([0.94, 0.9, 1.04, 1.07])
        price += (base - price) * 0.06  # drift back toward the base price
        price = min(max(price, base * 0.8), base * 1.1)
        ts = end - timedelta(hours=INTERVAL_HOURS * (steps - 1 - i))
        rows.append({"timestamp": ts.isoformat(), "price": round(price, 2)})

    pid, forced_retailer, drop = FORCED_DROP
    if product["productId"] == pid and retailer == forced_retailer and condition == "new":
        rows[-1]["price"] = round(rows[-2]["price"] * (1 - drop), 2)

    return rows


def _stats(prices):
    return {"low": min(prices), "median": round(statistics.median(prices), 2), "high": max(prices)}


def _offer(product, retailer, condition):
    prices = [row["price"] for row in _history(product, retailer, condition)]
    current, previous = prices[-1], prices[-2]
    drop_percent = round((previous - current) / previous * 100, 1)
    return {
        "listingId": _listing_id(product["productId"], retailer, condition),
        "retailer": retailer,
        "condition": condition,
        "price": current,
        "url": f"https://example.com/mock/{_slug(retailer)}/{product['productId']}",
        "stats": _stats(prices),  # this listing's own range over the tracking window
        "change": {"previousPrice": previous, "dropPercent": drop_percent},
        "isDrop": current <= previous * (1 - DROP_THRESHOLD),
    }


def _item(product):
    offers = [_offer(product, r, c) for r, c in product["offers"]]
    # Headline numbers use new listings only; refurbished/used would distort the low.
    new_offers = [o for o in offers if o["condition"] == "new"] or offers
    pooled = [row["price"] for o in new_offers
              for row in _history(product, o["retailer"], o["condition"])]
    best = min(new_offers, key=lambda o: o["price"])
    return {
        "productId": product["productId"],
        "productName": product["productName"],
        "image": _image(product),
        "trackingDays": TRACKING_DAYS,
        "stats": {**_stats(pooled),
                  "currentLowest": {"listingId": best["listingId"],
                                    "retailer": best["retailer"], "price": best["price"]}},
        "offers": offers,
    }


async def _delay():
    if LATENCY_MS > 0:
        await asyncio.sleep(LATENCY_MS / 1000)


@app.get("/health")
def health():
    return {"status": "ok", "mode": "mock"}


@app.get("/wishlist")
async def get_wishlist():
    """PROPOSED: summary of every wishlist item, for the sidebar and home page."""
    await _delay()
    items = []
    for product in CATALOG:
        item = _item(product)
        drops = [o for o in item["offers"] if o["isDrop"]]
        items.append({
            "productId": item["productId"],
            "productName": item["productName"],
            "image": item["image"],
            "lowestPrice": item["stats"]["currentLowest"]["price"],
            "lowestRetailer": item["stats"]["currentLowest"]["retailer"],
            "offerCount": len(item["offers"]),
            "hasPriceDrop": bool(drops),
            "bestDropPercent": max((o["change"]["dropPercent"] for o in drops), default=0),
        })
    return {"count": len(items), "items": items}


@app.get("/wishlist/{product_id}")
async def get_wishlist_item(product_id: str):
    """PROPOSED: one item with every retailer offer and its price statistics."""
    await _delay()
    product = next((p for p in CATALOG if p["productId"] == product_id), None)
    if product is None:
        raise HTTPException(status_code=404, detail="Unknown productId")
    return _item(product)


@app.get("/products")
async def get_products(q: str = Query(default="Sony WH-1000XM5 headphones", min_length=2, max_length=120),
                       simulate: str = Query(default="")):
    """Raw, noisy search-style listings like the real /products (same schema)."""
    await _delay()

    if simulate == "error":  # exercise the frontend's error state
        raise HTTPException(status_code=502, detail="Unable to retrieve shopping results")

    words = set(re.findall(r"[a-z0-9]+", q.lower()))
    matches = [p for p in CATALOG if words & set(re.findall(r"[a-z0-9]+", p["productName"].lower()))]
    matches = matches or CATALOG

    products = []
    for p in matches:
        for retailer, condition in p["offers"]:
            if condition != "new":
                continue
            products.append({
                "productId": _listing_id(p["productId"], retailer, condition),
                "productName": p["productName"],
                "retailer": retailer,
                "price": _offer(p, retailer, condition)["price"],
                "image": _image(p),
                "url": f"https://example.com/mock/{_slug(retailer)}/{p['productId']}",
            })
        # Noise the real Google Shopping results contain (matching will need to filter these).
        products.append({
            "productId": f"{p['productId']}:refurb", "productName": f"{p['productName']} - Refurbished",
            "retailer": "eBay", "price": round(p["basePrice"] * 0.62, 2), "image": None,
            "url": f"https://example.com/mock/ebay/{p['productId']}",
        })
        products.append({
            "productId": f"{p['productId']}:case", "productName": f"Hard Case for {p['productName']}",
            "retailer": "Amazon.com", "price": 19.99, "image": None,
            "url": f"https://example.com/mock/amazon/{p['productId']}-case",
        })

    return {"query": q, "count": len(products), "cached": False,
            "fetchedAt": datetime.now(timezone.utc).isoformat(), "products": products}