# Best2Buy: Command Reference

Commands for setting up, deploying, running and maintaining the Best2Buy backend.
Each block says which folder to run it from.

---

## One-time setup

**Repo root:**
```bash
git clone https://github.com/laurenlal/cse4207-b2bsaas-final-project
cd cse4207-b2bsaas-final-project
git checkout backend-ingestion
```

**`backend/`:**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pip install "botocore[crt]"          # only if you use `aws login`
```

**`frontend/`:**
```bash
npm install
```

**AWS sign-in and SerpApi key** (any folder):
```bash
aws configure                                   # or: aws login
aws sts get-caller-identity                     # check you're signed in
aws ssm put-parameter --name /best2buy/serpapi-api-key --type SecureString --value YOUR_KEY
```

**Repo-root `.env`** (next to `README.md`; never commit this file):
```
AWS_REGION=us-east-1
SERPAPI_API_KEY=your_full_key
```

---

## Deploy the tables, Lambda and schedule

**`infrastructure/`:**
```bash
sam build
sam deploy --guided                             # first time only
sam deploy                                      # every time after
```

For `--guided`, answer: stack name `best2buy`, region `us-east-1`, keep the default
`SerpApiKeyParameterName`, and answer `Y` to everything except **Disable rollback** (`N`).

**`backend/`**, to load or update the products after editing `ingestion/catalog.json`:
```bash
python -m scripts.seed_products
```

---

## Run and check the daily job

The schedule runs it automatically every day at 9 AM Central. To run it by hand:

**Get the function name** (any folder):
```bash
aws cloudformation describe-stacks --stack-name best2buy --query "Stacks[0].Outputs[?OutputKey=='IngestionFunctionName'].OutputValue" --output text
```

**Run it** (costs one SerpApi search per product):
```bash
aws lambda invoke --function-name best2buy-IngestionFunction-D5ByOb6UoCeG out.json && cat out.json
```

A good result has `"recorded"` above 0 and `"errors": []`. Listings under `"missed"` had no matching result that day.

**Check the data:**
```bash
aws dynamodb scan --table-name bestbuy-products --select COUNT
aws dynamodb scan --table-name bestbuy-price-history --select COUNT
```

**Logs** (from `infrastructure/`):
```bash
sam logs -n IngestionFunction --stack-name best2buy
```

---

## Run the app locally

**Terminal 1, `backend/`:**

Real API on port 8000 (reads DynamoDB):
```bash
source .venv/bin/activate
python -m uvicorn api.main:app --reload --port 8000
```

Or the mock API on port 8001 (fake data, uses no searches):
```bash
python -m uvicorn api.dev_server:app --reload --port 8001
```

**Terminal 2, `frontend/`:**
```bash
echo "VITE_API_BASE_URL=http://localhost:8000" > .env      # use 8001 for the mock
npm run dev
```

Then open **http://localhost:5173**, exactly that address (other addresses fail with a CORS error).

**Quick checks** (any folder):
```bash
curl -s localhost:8000/health
curl -s localhost:8000/wishlist
curl -s localhost:8000/wishlist/sony-wh1000xm5
```

---

## Test and debug

**Run the tests** (`backend/`; no AWS or searches needed):
```bash
python -m pytest
```

**Look at what one search returns** (`backend/`; costs one search):
```bash
python -c "from ingestion.serpapi_client import fetch_shopping_results as f; [print(r.get('source'),'|',r['extracted_price'],'|',r.get('second_hand_condition','new?'),'|',r.get('title')) for r in f('YOUR QUERY')]"
```

**Check that `.env` loads** (`backend/`; prints the variable names and the key's length, not the key):
```bash
python -c "from dotenv import dotenv_values, find_dotenv; v=dotenv_values(find_dotenv()); print(list(v), len(v.get('SERPAPI_API_KEY') or ''))"
```

**Find what's using a port:**
```bash
lsof -i :8000
```

---

## Maintenance

**Swap the SerpApi key when the quota runs out:**
```bash
aws ssm put-parameter --name /best2buy/serpapi-api-key --type SecureString --value NEW_KEY --overwrite
```

**Commit and push** (repo root):
```bash
git add backend infrastructure .env.example
git status                                      # .env, out.json, .cache must NOT appear
git commit -m "your message"
git push
```

**Tear everything down** (`infrastructure/`; deletes the tables and all their data):
```bash
sam delete --stack-name best2buy
```

---

## Common problems

| Symptom | Fix |
|---|---|
| `No module named 'boto3'` / `'fastapi'` | Activate the venv, then `python -m pip install -r requirements.txt` |
| `MissingDependencyException ... botocore[crt]` | `python -m pip install "botocore[crt]"` |
| `/products` returns 502 and the log says `ValueError` | `SERPAPI_API_KEY` missing from the repo-root `.env`; fix it and restart uvicorn |
| `/wishlist` returns 502 | Check the uvicorn log; usually expired AWS credentials, so run `aws login` again |
| `sam deploy` says `Missing option '--stack-name'` | Run it from `infrastructure/` |
| Lambda `AccessDenied` on `ssm:GetParameter` | Redeploy with `sam deploy --parameter-overrides SerpApiKeyParameterName=/best2buy/serpapi-api-key` |
| `zsh: no such file or directory` | Remove any `< >` from the command |
| Edited `.env` and nothing changed | Restart uvicorn or `npm run dev`; env files are read only at startup |