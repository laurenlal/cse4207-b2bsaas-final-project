import os
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

_resource = None


def _db():
    global _resource
    if _resource is None:
        _resource = boto3.resource(
            "dynamodb",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            endpoint_url=os.getenv("DYNAMODB_ENDPOINT_URL") or None,
        )
    return _resource


def products_table():
    return _db().Table(os.getenv("PRODUCTS_TABLE", "bestbuy-products"))


def history_table():
    return _db().Table(os.getenv("PRICE_HISTORY_TABLE", "bestbuy-price-history"))


def _plain(v):
    """Decimal -> int/float so FastAPI can return it as JSON."""
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    if isinstance(v, list):
        return [_plain(x) for x in v]
    if isinstance(v, dict):
        return {k: _plain(x) for k, x in v.items()}
    return v


def _dynamo(v):
    """float -> Decimal (DynamoDB rejects floats); drop None values."""
    if isinstance(v, float):
        return Decimal(str(v))
    if isinstance(v, list):
        return [_dynamo(x) for x in v]
    if isinstance(v, dict):
        return {k: _dynamo(x) for k, x in v.items() if x is not None}
    return v


def get_products():
    table = products_table()
    resp = table.scan()
    items = resp["Items"]
    while "LastEvaluatedKey" in resp:
        resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
        items += resp["Items"]
    return sorted((_plain(i) for i in items), key=lambda p: p["productId"])


def get_product(product_id):
    item = products_table().get_item(Key={"productId": product_id}).get("Item")
    return _plain(item) if item else None


def upsert_product(product):
    """Write catalog fields without resetting trackingStartedAt."""
    fields = {k: v for k, v in product.items() if k not in ("productId", "trackingStartedAt", "image")}
    expr = ", ".join(f"#{k} = :{k}" for k in fields)
    names = {f"#{k}": k for k in fields}
    values = {f":{k}": _dynamo(v) for k, v in fields.items()}
    if product.get("image"):
        expr += ", #image = if_not_exists(#image, :image)"
        names["#image"] = "image"
        values[":image"] = product["image"]
    products_table().update_item(
        Key={"productId": product["productId"]},
        UpdateExpression="SET " + expr,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )


def mark_tracked(product_id, started_at, image=None):
    """First successful run sets trackingStartedAt; later runs leave it alone."""
    expr = "SET trackingStartedAt = if_not_exists(trackingStartedAt, :t)"
    values = {":t": started_at}
    names = {}
    if image:
        expr += ", #image = if_not_exists(#image, :img)"
        values[":img"] = image
        names["#image"] = "image"
    kwargs = {"ExpressionAttributeNames": names} if names else {}
    products_table().update_item(
        Key={"productId": product_id},
        UpdateExpression=expr,
        ExpressionAttributeValues=values,
        **kwargs,
    )


def put_observation(listing_id, product_id, timestamp, price, url=None, title=None, source=None):
    history_table().put_item(Item=_dynamo({
        "listingId": listing_id, "timestamp": timestamp, "productId": product_id,
        "price": float(price), "url": url, "title": title, "source": source,
    }))


def get_observations(listing_id, since_iso):
    table = history_table()
    cond = Key("listingId").eq(listing_id) & Key("timestamp").gte(since_iso)
    resp = table.query(KeyConditionExpression=cond)
    items = resp["Items"]
    while "LastEvaluatedKey" in resp:
        resp = table.query(KeyConditionExpression=cond, ExclusiveStartKey=resp["LastEvaluatedKey"])
        items += resp["Items"]
    return [_plain(i) for i in items]


def get_history(listing_ids, since_iso):
    return {lid: get_observations(lid, since_iso) for lid in listing_ids}