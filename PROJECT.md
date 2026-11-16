# B2B SaaS — Best Buy Retail Analytics Dashboard

**CSE 4207 Final Project | Fall 2026**

**Team:** Lauren Lal, Katherine Feng, Abby Shen

**Tech Stack:** React, Recharts, Python, AWS Lambda, EventBridge Scheduler, DynamoDB, API Gateway, CloudWatch, AWS SAM

## 1. Project Setup

- [ ] Create GitHub repository and invite all team members
- [ ] Initialize React frontend using Vite
- [ ] Install frontend dependencies (`recharts`, `lucide-react`)
- [ ] Create Python virtual environment and `backend/requirements.txt`
- [ ] Create repository folder structure
- [ ] Add `.gitignore`, `.env.example`, and `.nvmrc`
- [ ] Configure AWS CLI and AWS SAM
- [ ] Confirm Best Buy API access and obtain API key
- [ ] Create sample product JSON for local development

## 2. Best Buy API & Data Ingestion

**Files:** `backend/ingestion/`

- [ ] Implement `bestbuy_client.py`
  - [ ] Connect to Best Buy Products API
  - [ ] Fetch products from selected categories
  - [ ] Handle pagination and API errors
  - [ ] Respect API rate limits
- [ ] Implement product normalization
  - [ ] Extract SKU, name, brand, category
  - [ ] Extract regular price, sale price, discount
  - [ ] Extract online availability
  - [ ] Add UTC collection timestamp
- [ ] Implement `handler.py`
  - [ ] Call Best Buy API client
  - [ ] Process and validate product records
  - [ ] Write current product data to DynamoDB
  - [ ] Write timestamped price snapshots
  - [ ] Log number of products processed and errors
- [ ] Test ingestion locally with 10–20 products

## 3. DynamoDB Database

**Files:** `backend/shared/database.py`, `infrastructure/template.yaml`

- [ ] Create `Products` table
  - [ ] Partition key: `sku`
  - [ ] Store latest product information
- [ ] Create `PriceHistory` table
  - [ ] Partition key: `sku`
  - [ ] Sort key: `timestamp`
  - [ ] Store historical prices and availability
- [ ] Implement database functions
  - [ ] `upsert_product()`
  - [ ] `insert_price_snapshot()`
  - [ ] `get_products()`
  - [ ] `get_product(sku)`
  - [ ] `get_price_history(sku)`
- [ ] Test reads and writes
- [ ] Verify historical observations are stored correctly

## 4. AWS Lambda & EventBridge

**Files:** `backend/ingestion/handler.py`, `infrastructure/template.yaml`

- [ ] Create ingestion Lambda using Python 3.12
- [ ] Configure Lambda environment variables
- [ ] Configure API key access securely
- [ ] Configure IAM permissions for DynamoDB and CloudWatch
- [ ] Package shared Python modules and dependencies
- [ ] Deploy Lambda using AWS SAM
- [ ] Manually invoke Lambda and verify DynamoDB writes
- [ ] Create EventBridge Scheduler schedule (every 3 hours)
- [ ] Configure Scheduler IAM execution role
- [ ] Test automatic scheduled execution
- [ ] Verify execution logs in CloudWatch

## 5. Backend API

**Files:** `backend/api/handler.py`, `backend/shared/analytics.py`

- [ ] Create API Lambda function
- [ ] Configure API Gateway routes
- [ ] Implement endpoints:
  - [ ] `GET /products` — all tracked products
  - [ ] `GET /products/{sku}` — individual product
  - [ ] `GET /price-history/{sku}` — historical observations
  - [ ] `GET /analytics/summary` — dashboard KPIs
  - [ ] `GET /analytics/categories` — category metrics
  - [ ] `GET /health` — health check
- [ ] Implement analytics calculations
  - [ ] Discount percentage
  - [ ] Average discount
  - [ ] Number of products on sale
  - [ ] Price changes over time
  - [ ] Availability rate
- [ ] Implement category and brand filtering
- [ ] Configure CORS for React frontend
- [ ] Test API endpoints using Postman or curl
- [ ] Verify API Gateway returns DynamoDB data

## 6. React Dashboard

**Files:** `frontend/src/`

- [ ] Create dashboard layout and navigation
- [ ] Build reusable components:
  - [ ] `MetricCard.jsx`
  - [ ] `ProductTable.jsx`
  - [ ] `PriceHistoryChart.jsx`
  - [ ] `CategoryChart.jsx`
  - [ ] `FilterBar.jsx`
- [ ] Implement KPI cards:
  - [ ] Total products tracked
  - [ ] Products on sale
  - [ ] Average discount
  - [ ] Products available online
- [ ] Implement product table with sorting
- [ ] Implement category and brand filters
- [ ] Implement product search
- [ ] Implement price history line chart using Recharts
- [ ] Implement category comparison chart
- [ ] Display last successful data refresh
- [ ] Create `services/api.js` for backend requests
- [ ] Connect frontend to API Gateway
- [ ] Add loading and error states
- [ ] Test dashboard with real stored data

## 7. AWS Infrastructure & Deployment

**Files:** `infrastructure/template.yaml`

- [ ] Define DynamoDB tables in AWS SAM
- [ ] Define ingestion Lambda
- [ ] Define API Lambda
- [ ] Define API Gateway routes
- [ ] Define EventBridge schedule and execution role
- [ ] Configure IAM permissions
- [ ] Configure environment variables and secrets
- [ ] Configure CloudWatch logging
- [ ] Run `sam build`
- [ ] Run `sam deploy --guided`
- [ ] Verify deployed AWS resources
- [ ] Configure frontend with deployed API URL
- [ ] Deploy React frontend to S3/CloudFront (optional)

## 8. Testing & Integration

- [ ] Test product normalization
- [ ] Test discount and analytics calculations
- [ ] Test DynamoDB reads and writes
- [ ] Test ingestion Lambda manually
- [ ] Test EventBridge scheduled execution
- [ ] Test all API endpoints
- [ ] Test frontend filters and charts
- [ ] Test complete pipeline:

  `EventBridge → Lambda → Best Buy API → DynamoDB → API Gateway/Lambda → React`

- [ ] Test missing data and API failures
- [ ] Verify CloudWatch logs
- [ ] Run `pytest`
- [ ] Run `npm run lint`
- [ ] Run `npm run build`

## 9. Final Demo

- [ ] Display dashboard with product data
- [ ] Show price history and discount analytics
- [ ] Manually invoke ingestion Lambda
- [ ] Show successful execution in CloudWatch
- [ ] Show stored records in DynamoDB
- [ ] Refresh dashboard to demonstrate updated data
- [ ] Demonstrate a simulated price drop
- [ ] Explain serverless architecture and AWS Lambda

---

## Suggested Work Split

| Workstream | Main Responsibilities | Owner |
|---|---|---|
| Cloud Infrastructure | AWS SAM, Lambda deployment, EventBridge, IAM, CloudWatch | TBD |
| Data Engineering | Best Buy API, ingestion, DynamoDB operations, analytics | TBD |
| Dashboard & API | React, Recharts, API Gateway endpoints, frontend integration | TBD |

All team members contribute to testing, integration, and the final demo.

## Recommended Development Order

1. **Setup:** GitHub repo, React, Python, mock product data
2. **Data:** Best Buy API client, normalization, database functions
3. **Cloud:** DynamoDB, ingestion Lambda, EventBridge
4. **API:** API Gateway, read endpoints, analytics
5. **Frontend:** Dashboard components and API integration
6. **Integration:** End-to-end testing and deployment
7. **Demo:** CloudWatch, Lambda execution, price-change demonstration

**MVP Priority:** Get one complete end-to-end workflow running with 10–20 products before adding additional features.