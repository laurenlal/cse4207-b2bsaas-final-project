"""End to end against an in-memory DynamoDB (moto): seed -> ingestion Lambda -> /wishlist API.
No AWS account or SerpApi searches needed."""

import os
from datetime import datetime, timedelta, timezone

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

os.environ.update(AWS_REGION="us-east-1", AWS_ACCESS_KEY_ID="test", AWS_SECRET_ACCESS_KEY="test",
                  PRODUCTS_TABLE="bestbuy-products", PRICE_HISTORY_TABLE="bestbuy-price-history",
                  SERPAPI_API_KEY="test-key")

FAKE_RESULTS = [
    {"title": "Sony WH-1000XM5 Wireless Headphones", "source": "Best Buy", "extracted_price": 329.99,
     "product_link": "https://example.com/bb", "thumbnail": "https://example.com/img.jpg"},
    {"title": "Sony WH-1000XM5 Wireless Headphones", "source": "Walmart", "extracted_price": 299.00,
     "product_link": "https://example.com/wm"},
    {"title": "Sony WH-1000XM5 (Refurbished)", "source": "Back Market", "extracted_price": 228.00,
     "product_link": "https://example.com/backmarket"},
    {"title": "Hard Case for Sony WH-1000XM5", "source": "Target", "extracted_price": 19.99},
]


@pytest.fixture
def aws():
    with mock_aws():
        from shared import database
        database._resource = None  # make boto3 connect to the mock
        ddb = boto3.client("dynamodb", region_name="us-east-1")
        ddb.create_table(TableName="bestbuy-products", BillingMode="PAY_PER_REQUEST",
                         AttributeDefinitions=[{"AttributeName": "productId", "AttributeType": "S"}],
                         KeySchema=[{"AttributeName": "productId", "KeyType": "HASH"}])
        ddb.create_table(TableName="bestbuy-price-history", BillingMode="PAY_PER_REQUEST",
                         AttributeDefinitions=[{"AttributeName": "listingId", "AttributeType": "S"},
                                               {"AttributeName": "timestamp", "AttributeType": "S"}],
                         KeySchema=[{"AttributeName": "listingId", "KeyType": "HASH"},
                                    {"AttributeName": "timestamp", "KeyType": "RANGE"}])
        yield database
        database._resource = None


def test_seed_ingest_and_serve(aws, monkeypatch):
    from api.main import app
    from ingestion import handler
    from scripts.seed_products import load_catalog

    database = aws
    for product in load_catalog():
        database.upsert_product(product)
    assert len(database.get_products()) == 4

    calls = []
    monkeypatch.setattr(handler, "fetch_shopping_results",
                        lambda q, key: calls.append(q) or (FAKE_RESULTS if "WH-1000XM5" in q else []))
    summary = handler.lambda_handler({}, None)

    assert summary["searches"] == 4  # one per product, not one per listing
    assert summary["recorded"] == 3
    assert "sony-wh1000xm5:target:new" in summary["missed"]  # only a case at Target

    # Add an older observation so there's a price change to report.
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).replace(microsecond=0).isoformat()
    database.put_observation("sony-wh1000xm5:walmart:new", "sony-wh1000xm5", yesterday, 340.0)

    client = TestClient(app)
    wishlist = client.get("/wishlist").json()
    assert wishlist["count"] == 1  # products without data are skipped
    assert wishlist["items"][0] == {
        "productId": "sony-wh1000xm5", "productName": "Sony WH-1000XM5 Wireless Headphones",
        "image": "https://example.com/img.jpg", "lowestPrice": 299.0, "lowestRetailer": "Walmart",
        "offerCount": 3, "hasPriceDrop": True, "bestDropPercent": 12.1,
    }

    item = client.get("/wishlist/sony-wh1000xm5").json()
    assert item["trackingDays"] == 1
    assert item["stats"]["currentLowest"] == {"listingId": "sony-wh1000xm5:walmart:new",
                                              "retailer": "Walmart", "price": 299.0}
    assert item["stats"]["low"] == 299.0  # refurbished $228 doesn't count
    walmart = next(o for o in item["offers"] if o["retailer"] == "Walmart")
    assert walmart["change"] == {"previousPrice": 340.0, "dropPercent": 12.1}
    assert walmart["url"] == "https://example.com/wm"

    assert client.get("/wishlist/airpods-pro-2").status_code == 404   # no data yet
    assert client.get("/wishlist/nope").status_code == 404

    # Re-seeding must not reset when tracking began.
    started = database.get_product("sony-wh1000xm5")["trackingStartedAt"]
    for product in load_catalog():
        database.upsert_product(product)
    assert database.get_product("sony-wh1000xm5")["trackingStartedAt"] == started
