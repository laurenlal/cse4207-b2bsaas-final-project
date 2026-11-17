from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from ingestion.serpapi_client import search_products
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