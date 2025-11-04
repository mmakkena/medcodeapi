Below is a structured requirements doc you can paste into Claude to generate code for a simple API product that provides ICD-10 & CPT coding lookup + developer onboarding + billing + customer support UI.

This frames the project clearly so Claude can output code, backend, DB schema, and UI.

✅ Product Name

MedCode API — Simple developer API for ICD-10 & CPT lookup + coding suggestions

✅ Product Summary (for Claude context)

Build a minimal SaaS product that allows developers and small health tech apps to:

Query ICD-10 & CPT codes via API

Search by keyword or description

Suggest likely codes based on text input

Create and manage API keys

Meter usage & billing (Stripe)

Signup/login dashboard

Support & usage logs dashboard

Self-serve onboarding

✅ Target Users

Digital health startup developers

Billing automation tools

EMR/EHR plugin builders

AI clinical documentation builders

Health apps needing code lookup

✅ Core Features
🧠 Code Search API

GET /api/icd10?query=XXX

GET /api/cpt?query=YYY

Support search by:

Code (I10, 99213)

Phrase (hypertension, office visit)

Free text suggestions (Patient presents with... → top likely codes)

🪪 API Keys

Generate, rotate, revoke keys

Store securely (hashed)

Rate limiting (per minute/day)

Usage logs per API key

💳 Billing

Stripe billing

Free tier (100 requests/month)

Tiered paid plans (usage-based)

Webhooks for active subscription status

Disable API access on non-payment

📊 Dev Dashboard

Signup/Login (email + password)

View plan & usage stats

See logs (last 50 API calls)

API Docs + examples (curl, Python, JS)

Billing management (Stripe portal)

🎫 Support

Help page

Contact form / ticket submission

Knowledge base / FAQ

✅ Tech Requirements
Backend

Language: Python (FastAPI) or Node (Express) — Claude should choose and justify

API Key auth

PostgreSQL or SQLite

Redis (rate limiting optional)

DB tables:

Table	Purpose
users	auth
api_keys	key mgmt & linking to users
plans	pricing tiers
usage_logs	track calls
stripe_subscriptions	sync billing status
icd10_codes	code table
cpt_codes	code table
Frontend

Next.js or React SPA

Components:

Page	Features
Landing Page	product, docs, pricing
Signup/Login	auth UI
Dashboard	usage, logs, API keys
Billing	Stripe portal
Docs page	swagger & examples
DevOps

Dockerfile

.env.example

Local dev environment setup instructions

✅ Data Sources (for Claude to load)

Use public ICD-10 + CPT datasets:

ICD-10: CMS public dataset

CPT: Use placeholder dataset (mock dataset now) — provide ability to load licensed CPT later

Storage format: CSV → DB table seed

✅ API Specification
ICD-10 Search
GET /api/v1/icd10/search?query=hypertension
Authorization: Bearer API_KEY


Response:

{
 "results": [
   {"code": "I10", "description": "Essential (primary) hypertension"}
 ]
}

CPT Search
GET /api/v1/cpt/search?query=office visit"

Code Suggestion
POST /api/v1/suggest
{
  "text": "Patient comes in for chronic hypertension follow up..."
}

✅ Billing Tiers
Tier	Limit	Price
Free	100 req/month	$0
Developer	10,000 req/month	$49/mo
Growth	100k req/month	$299/mo
Enterprise	Custom	Custom
✅ Deliverables for Claude

Ask Claude to produce:

✅ Full Code

Backend API

Database schema

Scripts to seed ICD-10 & CPT tables

API key middleware

Rate limiting

Stripe integration

Frontend dashboard

Docker environment

✅ Documentation

README setup

API docs

Postman collection

Example scripts in Python & JS

✅ Prompts for Claude

Tell Claude to:

“Generate code in small chunks, validate before continuing, explain tradeoffs, and ensure all code uses secure patterns and production-ready structure.”

✅ Security Checklist

Hash API keys (not store plaintext)

HTTPS only

SQL injection prevention

JWT for user sessions

CORS rules only for app domain

Usage logs truncated after X days

