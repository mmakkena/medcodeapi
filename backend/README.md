# Nuvii API - Backend

Medical coding API with CDI (Clinical Documentation Improvement) agent capabilities.

## Features

### Core API Features
- **Authentication**: JWT-based user authentication + API key authentication
- **Code Search**: Search ICD-10 and CPT codes by code or description
- **Semantic Search**: AI-powered semantic search using MedCPT clinical embeddings (768-dim vectors)
- **Hybrid Search**: Combines semantic (AI) + keyword matching for best results
- **Faceted Search**: Filter by clinical facets (body system, severity, chronicity, etc.)
- **Code Suggestions**: AI-powered code suggestions from clinical text
- **API Key Management**: Create, rotate, and revoke API keys
- **Usage Tracking**: Track API usage with detailed logs and statistics
- **Billing**: Stripe integration for subscription management
- **Rate Limiting**: Redis-based rate limiting with in-memory fallback

### CDI Agent Features (NEW)
- **Clinical Entity Extraction**: Extract diagnoses, medications, labs, vitals from clinical notes
- **Documentation Gap Analysis**: Identify missing documentation opportunities
- **CDI Query Generation**: Generate physician queries for documentation improvement
- **Revenue Optimization**: Analyze E/M coding and DRG optimization opportunities
- **HEDIS Evaluation**: Quality measure compliance checking (CBP, CDC, BCS, CCS, COL, SPR)
- **MCP Server**: Model Context Protocol support for AI assistant integration

## Tech Stack

- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15 + pgvector extension
- **ORM**: SQLAlchemy 2.0 + Alembic
- **Cache/Rate Limiting**: Redis (optional)
- **Payments**: Stripe
- **Search**: PostgreSQL full-text search (pg_trgm + tsvector)
- **Embeddings**: MedCPT (ncbi/MedCPT-Query-Encoder) - 768-dimensional clinical embeddings
- **Vector Search**: pgvector for cosine similarity search
- **LLM Integration**: Anthropic Claude for CDI features

## Project Structure (Clean Architecture)

```
backend/
├── adapters/                    # Interface adapters (API, bots)
│   ├── api/
│   │   ├── main.py             # FastAPI application entry point
│   │   ├── routes/             # API route handlers
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── icd10.py        # ICD-10 search endpoints
│   │   │   ├── procedure.py    # CPT/HCPCS search endpoints
│   │   │   ├── cdi.py          # CDI analysis endpoints (NEW)
│   │   │   ├── revenue.py      # Revenue optimization endpoints (NEW)
│   │   │   ├── hedis.py        # HEDIS evaluation endpoints (NEW)
│   │   │   └── ...
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   └── middleware/         # Auth, API key, rate limiting
│   ├── slack/                  # Slack bot adapter
│   └── teams/                  # Microsoft Teams bot adapter
│
├── domain/                      # Business logic (framework-independent)
│   ├── entity_extraction.py    # Clinical entity extraction
│   ├── documentation_gaps.py   # Gap analysis logic
│   ├── query_generation.py     # CDI query generation
│   ├── revenue_optimization.py # Revenue impact analysis
│   ├── hedis_evaluation.py     # HEDIS measure evaluation
│   └── common/                 # Shared domain models
│
├── infrastructure/              # External services & persistence
│   ├── config/                 # Configuration management
│   ├── db/
│   │   ├── postgres.py         # Database connection
│   │   ├── models/             # SQLAlchemy models
│   │   └── repositories/       # Data access layer
│   ├── llm/                    # LLM service integrations
│   └── logging/                # Logging configuration
│
├── mcp/                        # MCP server for AI assistants
├── scripts/                    # Data loading & utility scripts
├── tests/                      # Test suite
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Setup Instructions

### Prerequisites

- Docker & Docker Compose
- (Optional) Python 3.11+ for local development

### Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` with your configuration:
   ```env
   SECRET_KEY=your-secret-key-here
   JWT_SECRET_KEY=your-jwt-secret-here
   STRIPE_SECRET_KEY=sk_test_your_stripe_key
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
   DATABASE_URL=postgresql://postgres:postgres@db:5432/nuviiapi
   REDIS_URL=redis://redis:6379/0
   ANTHROPIC_API_KEY=your-anthropic-key  # For CDI features
   ```

### Running with Docker Compose

1. **Start all services**:
   ```bash
   docker-compose up -d
   ```

2. **Run database migrations**:
   ```bash
   docker-compose exec api alembic upgrade head
   ```

3. **Seed the database** with ICD-10 and CPT codes:
   ```bash
   docker-compose exec api python scripts/seed_codes.py
   ```

4. **Access the API**:
   - API: http://localhost:8000
   - Swagger Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Running Locally (Without Docker)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL and Redis** (or use Docker for just these services):
   ```bash
   docker-compose up -d db redis
   ```

3. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Start the server**:
   ```bash
   uvicorn adapters.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### Authentication (JWT)
- `POST /api/v1/auth/signup` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user profile

### Code Search (API Key Required)
- `GET /api/v1/icd10/search` - Search ICD-10 diagnosis codes
- `GET /api/v1/icd10/semantic-search` - AI-powered semantic search
- `GET /api/v1/icd10/hybrid-search` - Hybrid search (semantic + keyword)
- `GET /api/v1/icd10/faceted-search` - Search by clinical facets
- `GET /api/v1/procedure/search` - Search procedure codes (CPT/HCPCS)
- `GET /api/v1/procedure/semantic-search` - AI-powered procedure search
- `GET /api/v1/procedure/hybrid-search` - Hybrid procedure search
- `POST /api/v1/suggest` - AI-powered code suggestions

### CDI Agent Endpoints (NEW - API Key Required)
- `POST /api/v1/cdi/analyze` - Full CDI analysis of clinical note
- `POST /api/v1/cdi/extract-entities` - Extract clinical entities only
- `POST /api/v1/cdi/documentation-gaps` - Analyze documentation gaps
- `POST /api/v1/cdi/generate-queries` - Generate CDI queries

### Revenue Optimization (NEW - API Key Required)
- `POST /api/v1/revenue/analyze` - Full revenue impact analysis
- `POST /api/v1/revenue/em-analysis` - E/M coding analysis
- `POST /api/v1/revenue/drg-opportunities` - DRG optimization opportunities

### HEDIS Quality Measures (NEW - API Key Required)
- `POST /api/v1/hedis/evaluate` - Evaluate HEDIS compliance
- `GET /api/v1/hedis/measures` - List available HEDIS measures
- `GET /api/v1/hedis/targets` - Get performance targets

### API Key Management (JWT Required)
- `GET /api/v1/api-keys` - List user's API keys
- `POST /api/v1/api-keys` - Create new API key
- `DELETE /api/v1/api-keys/{id}` - Revoke API key

### Usage & Billing (JWT Required)
- `GET /api/v1/usage/logs` - Get usage logs
- `GET /api/v1/usage/stats` - Get usage statistics
- `GET /api/v1/billing/subscription` - Get subscription details
- `POST /api/v1/billing/checkout` - Create Stripe checkout session

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Production**: https://api.nuvii.ai/docs

## Example Usage

### CDI Analysis

```bash
curl -X POST "https://api.nuvii.ai/api/v1/cdi/analyze" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "clinical_note": "65 yo male with history of CHF presenting with shortness of breath. BP 148/92, HR 88. Labs show BNP 450, Cr 1.8. Assessment: Acute on chronic systolic heart failure exacerbation.",
    "include_queries": true,
    "include_revenue_impact": true
  }'
```

### HEDIS Evaluation

```bash
curl -X POST "https://api.nuvii.ai/api/v1/hedis/evaluate" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "clinical_note": "58 yo female with HTN and diabetes. BP 138/86. HbA1c 7.2%. On lisinopril 20mg, metformin 1000mg BID.",
    "patient_age": 58,
    "patient_gender": "female",
    "include_exclusions": true
  }'
```

### Revenue Analysis

```bash
curl -X POST "https://api.nuvii.ai/api/v1/revenue/analyze" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "clinical_note": "New patient visit, 45 minutes spent on comprehensive history and exam...",
    "encounter_type": "outpatient"
  }'
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=adapters --cov=domain --cov=infrastructure

# Run specific test file
pytest tests/test_domain_entity_extraction.py -v
```

## Security Features

- **Hashed API Keys** - SHA-256 hashed, never stored in plaintext
- **Hashed Passwords** - bcrypt hashing
- **JWT Tokens** - Secure session management
- **Rate Limiting** - Per-user rate limits (Redis or in-memory)
- **SQL Injection Prevention** - SQLAlchemy ORM
- **CORS Configuration** - Restricted to frontend domain

## Production Deployment

The backend is deployed to AWS ECS Fargate via GitHub Actions:

1. Push to `main` branch triggers deployment
2. Docker image built and pushed to ECR
3. ECS service updated with new task definition
4. Health checks verify successful deployment

### Manual Deployment

```bash
# Build Docker image
docker build -t nuvii-api .

# Tag for ECR
docker tag nuvii-api:latest <account>.dkr.ecr.us-east-2.amazonaws.com/nuvii-api:latest

# Push to ECR
docker push <account>.dkr.ecr.us-east-2.amazonaws.com/nuvii-api:latest
```

## License

MIT

## Support

For issues and questions, please open an issue on GitHub or contact support@nuvii.ai
