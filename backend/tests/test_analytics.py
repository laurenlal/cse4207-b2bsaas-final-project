from datetime import datetime, timedelta, timezone

import pytest

from api import dev_server
from shared import analytics

NOW = datetime(2026, 12, 1, 12, tzinfo=timezone.utc)


def obs(hours_ago, price, url=None):
    row = {"timestamp": (NOW - timedelta(hours=hours_ago)).isoformat(), "price": price}
    if url:
        row["url"] = url
    return row


LISTING = {"listingId": "p:walmart:new", "retailer": "Walmart", "condition": "new",
           "url": "https://catalog.example/p"}


def test_summarize_odd_and_even():
    assert analytics.summarize([3.0, 1.0, 2.0]) == {"low": 1.0, "median": 2.0, "high": 3.0}
    assert analytics.summarize([1.0, 2.0, 3.0, 4.0]) == {"low": 1.0, "median": 2.5, "high": 4.0}


@pytest.mark.parametrize("current,previous,drop,is_drop", [
    (95.0, 100.0, 5.0, True),     # exactly 5% counts
    (95.01, 100.0, 5.0, False),   # just under 5% does not (rounds to 5.0 for display)
    (88.0, 100.0, 12.0, True),
    (110.0, 100.0, -10.0, False), # price went up
])
def test_price_change(current, previous, drop, is_drop):
    change, flag = analytics.price_change(current, previous)
    assert change == {"previousPrice": previous, "dropPercent": drop}
    assert flag is is_drop


def test_offer_with_single_observation_has_no_drop():
    offer = analytics.build_offer(LISTING, [obs(1, 50.0)])
    assert offer["change"] == {"previousPrice": None, "dropPercent": 0.0}
    assert offer["isDrop"] is False
    assert offer["stats"] == {"low": 50.0, "median": 50.0, "high": 50.0}


def test_offer_sorts_by_time_and_uses_newest_url():
    rows = [obs(1, 88.0, "https://new"), obs(25, 100.0, "https://old"), obs(13, 100.0)]
    offer = analytics.build_offer(LISTING, rows)
    assert offer["price"] == 88.0
    assert offer["change"]["previousPrice"] == 100.0
    assert offer["isDrop"] is True
    assert offer["url"] == "https://new"


def test_offer_falls_back_to_catalog_url():
    assert analytics.build_offer(LISTING, [obs(1, 10.0)])["url"] == "https://catalog.example/p"


def test_offer_without_observations_is_none():
    assert analytics.build_offer(LISTING, []) is None


@pytest.mark.parametrize("started_hours_ago,expected", [
    (None, 1), (0.5, 1), (24, 1), (25, 2), (24 * 7, 7), (24 * 45, 30),
])
def test_tracking_days(started_hours_ago, expected):
    started = None if started_hours_ago is None else (NOW - timedelta(hours=started_hours_ago)).isoformat()
    assert analytics.tracking_days(started, NOW) == expected


def _product(listings, started_days_ago=10):
    return {"productId": "p", "productName": "P", "image": None,
            "trackingStartedAt": (NOW - timedelta(days=started_days_ago)).isoformat(),
            "listings": listings}


def test_item_stats_use_new_offers_only():
    new = {**LISTING}
    refurb = {"listingId": "p:bm:refurbished", "retailer": "Back Market", "condition": "refurbished"}
    item = analytics.build_item(_product([new, refurb]), {
        new["listingId"]: [obs(13, 100.0), obs(1, 90.0)],
        refurb["listingId"]: [obs(13, 40.0), obs(1, 30.0)],
    }, NOW)
    assert item["stats"]["low"] == 90.0
    assert item["stats"]["currentLowest"] == {"listingId": "p:walmart:new", "retailer": "Walmart", "price": 90.0}
    assert [o["listingId"] for o in item["offers"]] == ["p:walmart:new", "p:bm:refurbished"]
    assert item["trackingDays"] == 10


def test_item_with_only_used_offers_falls_back_to_them():
    used = {"listingId": "p:ebay:used", "retailer": "eBay", "condition": "used"}
    item = analytics.build_item(_product([used]), {used["listingId"]: [obs(1, 20.0)]}, NOW)
    assert item["stats"]["currentLowest"]["retailer"] == "eBay"


def test_stale_offer_is_hidden():
    fresh = {**LISTING}
    stale = {"listingId": "p:target:new", "retailer": "Target", "condition": "new"}
    item = analytics.build_item(_product([fresh, stale]), {
        fresh["listingId"]: [obs(2, 100.0)],
        stale["listingId"]: [obs(analytics.STALE_AFTER_HOURS + 1, 50.0)],
    }, NOW)
    assert [o["retailer"] for o in item["offers"]] == ["Walmart"]


def test_item_without_data_is_none():
    assert analytics.build_item(_product([LISTING]), {}, NOW) is None


def test_summary_shape():
    l2 = {"listingId": "p:target:new", "retailer": "Target", "condition": "new"}
    item = analytics.build_item(_product([LISTING, l2]), {
        LISTING["listingId"]: [obs(13, 100.0), obs(1, 88.0)],
        l2["listingId"]: [obs(13, 100.0), obs(1, 93.0)],
    }, NOW)
    assert analytics.build_summary(item) == {
        "productId": "p", "productName": "P", "image": None,
        "lowestPrice": 88.0, "lowestRetailer": "Walmart", "offerCount": 2,
        "hasPriceDrop": True, "bestDropPercent": 12.0,
    }


@pytest.mark.parametrize("product", dev_server.CATALOG, ids=lambda p: p["productId"])
def test_matches_mock_server_exactly(product):
    """Feed the mock's own price histories through analytics.py: the output must equal
    what dev_server returns, which is what the frontend is built against."""
    listings, history = [], {}
    for retailer, condition in product["offers"]:
        lid = dev_server._listing_id(product["productId"], retailer, condition)
        listings.append({"listingId": lid, "retailer": retailer, "condition": condition,
                         "url": f"https://example.com/mock/{dev_server._slug(retailer)}/{product['productId']}"})
        history[lid] = dev_server._history(product, retailer, condition)

    now = datetime.now(timezone.utc)
    real = analytics.build_item({
        "productId": product["productId"], "productName": product["productName"],
        "image": dev_server._image(product),
        "trackingStartedAt": (now - timedelta(days=dev_server.TRACKING_DAYS)).isoformat(),
        "listings": listings,
    }, history, now)

    assert real == dev_server._item(product)
