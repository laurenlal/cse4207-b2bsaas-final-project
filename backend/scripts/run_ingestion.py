"""Run the ingestion Lambda once on your laptop, against the real DynamoDB tables.
Uses SERPAPI_API_KEY from the repo-root .env. COSTS ONE SERPAPI SEARCH PER PRODUCT.
Run from backend/:
    python -m scripts.run_ingestion
"""
import json

from dotenv import load_dotenv

load_dotenv()

from ingestion.handler import lambda_handler  # noqa: E402

if __name__ == "__main__":
    print(json.dumps(lambda_handler({}, None), indent=2))
