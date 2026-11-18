from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from ingestion.serpapi_client import search_products
from shared import analytics, database
from shared.cache import get_or_fetch

app = FastAPI(title="Best2Buy API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/products")
def get_products(
    q: str = Query(
        default="Sony WH-1000XM5 headphones",
        min_length=2,
        max_length=120,
    )
):
    try:
        # Cached for 2 hours (CACHE_TTL_SECONDS) so page reloads don't spend SerpApi searches.
        products, meta = get_or_fetch("products", q, lambda: search_products(q))

        return {
            "query": q,
            "count": len(products),
            "cached": meta["cached"],
            "fetchedAt": meta["fetchedAt"],
            "products": products,
        }

    except (ValueError, RuntimeError, Exception) as exc:
        # Keep internal API errors and secrets out of frontend responses.
        print(f"Product search failed: {type(exc).__name__}")
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve shopping results",
        ) from None


def _load_item(product, now):
    """Read one product's last 30 days of prices from DynamoDB and compute its stats."""
    since = analytics.window_start(now).isoformat()
    history = database.get_history([l["listingId"] for l in product.get("listings", [])], since)
    return analytics.build_item(product, history, now)


@app.get("/wishlist")
def get_wishlist():
    """Summary of every wishlist item, for the sidebar and home page."""
    try:
        now = datetime.now(timezone.utc)
        items = []
        for product in database.get_products():
            item = _load_item(product, now)
            if item:  # skip products with no price data yet
                items.append(analytics.build_summary(item))
        return {"count": len(items), "items": items}
    except Exception as exc:
        print(f"Wishlist load failed: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=502, detail="Unable to load wishlist") from None


@app.get("/wishlist/{product_id}")
def get_wishlist_item(product_id: str):
    """One item with every retailer offer and its price statistics."""
    try:
        product = database.get_product(product_id)
        item = _load_item(product, datetime.now(timezone.utc)) if product else None
    except Exception as exc:
        print(f"Wishlist item load failed: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=502, detail="Unable to load wishlist item") from None

    if product is None:
        raise HTTPException(status_code=404, detail="Unknown productId")
    if item is None:
        raise HTTPException(status_code=404, detail="No price data yet")
    return item