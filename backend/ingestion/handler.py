"""Daily ingestion Lambda: EventBridge Scheduler -> this function -> SerpApi -> DynamoDB.

For every product in the Products table, run one Google Shopping search, pick the matching
result for each tracked listing, and write one price observation per listing.
Never uses shared/cache.py, so every run records a fresh price.
"""

import json
import os
from collections import defaultdict
from datetime import datetime, timezone

import boto3

from ingestion.matching import best_match
from ingestion.serpapi_client import fetch_shopping_results
from shared import database

_api_key = None


def _get_api_key():
    """Local runs use SERPAPI_API_KEY from .env; in AWS the key comes from SSM Parameter Store."""
    global _api_key
    if _api_key is None:
        _api_key = os.getenv("SERPAPI_API_KEY") or boto3.client("ssm").get_parameter(
            Name=os.environ["SERPAPI_KEY_PARAMETER"], WithDecryption=True
        )["Parameter"]["Value"]
    return _api_key


def lambda_handler(event, context):
    api_key = _get_api_key()
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()  # one timestamp per run
    summary = {"runAt": now, "searches": 0, "recorded": 0, "missed": [], "errors": []}

    for product in database.get_products():
        # Usually one search per product: a Google Shopping search covers every retailer.
        groups = defaultdict(list)
        for listing in product.get("listings", []):
            groups[listing.get("searchQuery") or product["searchQuery"]].append(listing)

        image = None
        recorded_any = False
        for query, listings in groups.items():
            try:
                results = fetch_shopping_results(query, api_key)
                summary["searches"] += 1
            except Exception as exc:
                summary["errors"].append(f"{product['productId']}: {type(exc).__name__}: {exc}")
                continue

            for listing in listings:
                match = best_match(results, product, listing)
                if match is None:
                    summary["missed"].append(listing["listingId"])
                    continue
                database.put_observation(
                    listing["listingId"], product["productId"], now, match["extracted_price"],
                    match.get("product_link"), match.get("title"), match.get("source"),
                )
                summary["recorded"] += 1
                recorded_any = True
                image = image or match.get("thumbnail")

        if recorded_any:
            database.mark_tracked(product["productId"], now, image)

    print(json.dumps(summary))  # appears in CloudWatch Logs
    if summary["searches"] == 0 and summary["errors"]:
        raise RuntimeError("Every SerpApi search failed")
    return summary
