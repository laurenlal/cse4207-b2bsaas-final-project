"""Price statistics for the /wishlist endpoints.

Pure functions with no AWS or network access, so they are easy to unit test
(see backend/tests/test_analytics.py). The output shapes match _offer() and _item()
in api/dev_server.py, which the frontend is built against.

An "observation" is one recorded price: {"timestamp": ISO-8601 string, "price": float}.
"""

import math
import statistics
from datetime import datetime, timedelta, timezone

WINDOW_DAYS = 30
DROP_THRESHOLD = 0.05  # a drop of 5% or more versus the previous observation
# Hide an offer whose newest price is older than this (2 missed daily runs + slack).
STALE_AFTER_HOURS = 60


def parse_ts(value):
    """Parse an ISO-8601 timestamp, treating a missing timezone as UTC."""
    ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def window_start(now=None, days=WINDOW_DAYS):
    now = now or datetime.now(timezone.utc)
    return now - timedelta(days=days)


def summarize(prices):
    """Low, median and high of a non-empty list of prices."""
    return {
        "low": min(prices),
        "median": round(statistics.median(prices), 2),
        "high": max(prices),
    }


def price_change(current, previous):
    """Change since the previous observation. previous is None for a listing seen only once."""
    if previous is None or previous <= 0:
        return {"previousPrice": previous, "dropPercent": 0.0}, False
    drop_percent = round((previous - current) / previous * 100, 1)
    is_drop = current <= previous * (1 - DROP_THRESHOLD)
    return {"previousPrice": previous, "dropPercent": drop_percent}, is_drop


def tracking_days(started_at, now=None):
    """Whole days of history, from 1 (first day) up to the 30-day window."""
    if not started_at:
        return 1
    now = now or datetime.now(timezone.utc)
    elapsed = (now - parse_ts(started_at)).total_seconds() / 86400
    return min(max(math.ceil(elapsed), 1), WINDOW_DAYS)


def build_offer(listing, observations):
    """One retailer offer, or None if the listing has no observations in the window.

    listing: {"listingId", "retailer", "condition", "url"}
    observations: this listing's observations in the window, in any order.
    The url of the newest observation wins over the catalog url, because
    the retailer's product link can change between runs.
    """
    if not observations:
        return None
    rows = sorted(observations, key=lambda o: o["timestamp"])
    prices = [float(o["price"]) for o in rows]
    current = prices[-1]
    previous = prices[-2] if len(prices) > 1 else None
    change, is_drop = price_change(current, previous)
    return {
        "listingId": listing["listingId"],
        "retailer": listing["retailer"],
        "condition": listing["condition"],
        "price": current,
        "url": rows[-1].get("url") or listing.get("url"),
        "stats": summarize(prices),
        "change": change,
        "isDrop": is_drop,
    }


def build_item(product, history, now=None):
    """The GET /wishlist/{productId} body, or None if nothing has been recorded yet.

    product: a Products-table item {"productId", "productName", "image",
             "trackingStartedAt", "listings": [...]}
    history: {listingId: [observation, ...]} for the window.
    """
    now = now or datetime.now(timezone.utc)
    stale_before = now - timedelta(hours=STALE_AFTER_HOURS)
    offers = []
    pooled = {}  # listingId -> prices, for the item-level stats
    for listing in product.get("listings", []):
        rows = history.get(listing["listingId"], [])
        # A listing that dropped out of the search results would otherwise keep
        # showing its last price as "current" for the rest of the window.
        if not rows or max(parse_ts(o["timestamp"]) for o in rows) < stale_before:
            continue
        offer = build_offer(listing, rows)
        if offer:
            offers.append(offer)
            pooled[offer["listingId"]] = [float(o["price"]) for o in rows]

    if not offers:
        return None

    # Headline numbers use new listings only; refurbished/used would distort the low.
    new_offers = [o for o in offers if o["condition"] == "new"] or offers
    prices = [p for o in new_offers for p in pooled[o["listingId"]]]
    best = min(new_offers, key=lambda o: o["price"])

    return {
        "productId": product["productId"],
        "productName": product["productName"],
        "image": product.get("image"),
        "trackingDays": tracking_days(product.get("trackingStartedAt"), now),
        "stats": {
            **summarize(prices),
            "currentLowest": {
                "listingId": best["listingId"],
                "retailer": best["retailer"],
                "price": best["price"],
            },
        },
        "offers": offers,
    }


def build_summary(item):
    """One entry of GET /wishlist, from a build_item() result."""
    drops = [o for o in item["offers"] if o["isDrop"]]
    return {
        "productId": item["productId"],
        "productName": item["productName"],
        "image": item["image"],
        "lowestPrice": item["stats"]["currentLowest"]["price"],
        "lowestRetailer": item["stats"]["currentLowest"]["retailer"],
        "offerCount": len(item["offers"]),
        "hasPriceDrop": bool(drops),
        "bestDropPercent": max((o["change"]["dropPercent"] for o in drops), default=0),
    }
