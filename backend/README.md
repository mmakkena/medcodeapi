# MedCode API - Backend

Medical coding lookup API for ICD-10 and CPT codes.

## Features

- 🔐 **Authentication**: JWT-based user authentication + API key authentication
- 📊 **Code Search**: Search ICD-10 and CPT codes by code or description
- 🧠 **Semantic Search**: AI-powered semantic search using MedCPT clinical embeddings (768-dim vectors)
- 🔀 **Hybrid Search**: Combines semantic (AI) + keyword matching for best results
- 🏷️ **Faceted Search**: Filter by clinical facets (body system, severity, chronicity, etc.)
- 🤖 **Code Suggestions**: AI-powered code suggestions from clinical text
- 🔑 **API Key Management**: Create, rotate, and revoke API keys
- 📈 **Usage Tracking**: Track API usage with detailed logs and statistics
- 💳 **Billing**: Stripe integration for subscription management
- ⚡ **Rate Limiting**: Redis-based rate limiting with in-memory fallback
- 🐳 **Dockerized**: Fully containerized with Docker Compose

## Tech Stack

- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15 + pgvector extension
- **ORM**: SQLAlchemy 2.0 + Alembic
- **Cache/Rate Limiting**: Redis (optional)
- **Payments**: Stripe
- **Search**: PostgreSQL full-text search (pg_trgm + tsvector)
- **Embeddings**: MedCPT (ncbi/MedCPT-Query-Encoder) - 768-dimensional clinical embeddings
- **Vector Search**: pgvector for cosine similarity search

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── middleware/      # Auth, API key, rate limiting
│   ├── services/        # Business logic (Stripe, usage tracking)
│   ├── utils/           # Security utilities
│   ├── config.py        # Configuration
│   ├── database.py      # Database connection
│   └── main.py          # FastAPI app
├── alembic/             # Database migrations
├── scripts/             # Seed scripts
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

4. **Seed data**:
   ```bash
   python scripts/seed_codes.py
   ```

5. **Start the server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

For complete API documentation with detailed request/response formats, authentication details, and code examples, see:

**[Complete API Reference](../docs/API_REFERENCE.md)**

### Quick Reference

#### Authentication (JWT)
- `POST /api/v1/auth/signup` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `POST /api/v1/auth/oauth/signin` - OAuth sign-in (Google/Microsoft)
- `GET /api/v1/auth/me` - Get current user profile

#### Code Search (API Key Required)
- `GET /api/v1/icd10/search` - Search ICD-10 diagnosis codes (keyword-based)
- `GET /api/v1/icd10/semantic-search` - AI-powered semantic search using clinical embeddings
- `GET /api/v1/icd10/hybrid-search` - Hybrid search (combines semantic + keyword matching)
- `GET /api/v1/icd10/faceted-search` - Search by clinical facets (body system, severity, etc.)
- `GET /api/v1/cpt/search` - Search CPT procedure codes
- `POST /api/v1/suggest` - AI-powered code suggestions from clinical text

#### API Key Management (JWT Required)
- `GET /api/v1/api-keys` - List user's API keys
- `POST /api/v1/api-keys` - Create new API key
- `DELETE /api/v1/api-keys/{id}` - Revoke API key

#### Usage Tracking (JWT Required)
- `GET /api/v1/usage/logs` - Get usage logs with request details
- `GET /api/v1/usage/stats` - Get usage statistics and quota info

#### Billing (JWT Required)
- `GET /api/v1/billing/subscription` - Get current subscription details
- `POST /api/v1/billing/checkout` - Create Stripe checkout session
- `GET /api/v1/billing/portal` - Get Stripe billing portal URL
- `POST /api/v1/billing/webhook` - Stripe webhook endpoint (internal)

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs (when running locally)
- **ReDoc**: http://localhost:8000/redoc (when running locally)
- **Production**: https://api.nuvii.ai/docs

## Example Usage

### 1. Register and Login

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword"}'
```

### 2. Create API Key

```bash
curl -X POST http://localhost:8000/api/v1/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My API Key"}'
```

### 3. Search ICD-10 Codes

```bash
# Keyword search
curl -X GET "http://localhost:8000/api/v1/icd10/search?query=hypertension" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Semantic search (AI-powered, understands medical context)
curl -X GET "http://localhost:8000/api/v1/icd10/semantic-search?query=patient%20with%20chest%20pain&limit=10" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Hybrid search (combines semantic + keyword)
curl -X GET "http://localhost:8000/api/v1/icd10/hybrid-search?query=diabetes&semantic_weight=0.7" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Faceted search (filter by clinical characteristics)
curl -X GET "http://localhost:8000/api/v1/icd10/faceted-search?body_system=Cardiovascular&severity=Severe" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 4. Get Code Suggestions

```bash
curl -X POST http://localhost:8000/api/v1/suggest \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "Patient presents with chronic hypertension and type 2 diabetes", "max_results": 5}'
```

## Security Features

✅ **Hashed API Keys** - SHA-256 hashed, never stored in plaintext
✅ **Hashed Passwords** - bcrypt hashing
✅ **JWT Tokens** - Secure session management
✅ **Rate Limiting** - Per-user rate limits (Redis or in-memory)
✅ **SQL Injection Prevention** - SQLAlchemy ORM
✅ **CORS Configuration** - Restricted to frontend domain

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black app/
isort app/
```

## Production Deployment

1. Set `ENVIRONMENT=production` in `.env`
2. Set `DEBUG=false`
3. Use strong `SECRET_KEY` and `JWT_SECRET_KEY`
4. Configure HTTPS/TLS
5. Set up proper CORS origins
6. Enable Redis for rate limiting
7. Configure Stripe production keys
8. Set up database backups

## Data Sources

### ICD-10 Codes

- **Current**: Sample dataset (20 codes)
- **Production**: Download from [CMS ICD-10 Codes](https://www.cms.gov/medicare/coding-billing/icd-10-codes)

### CPT Codes

- **Current**: Mock dataset (20 codes)
- **Production**: Requires AMA license - [AMA CPT](https://www.ama-assn.org/practice-management/cpt)

## License

MIT

## Support

For issues and questions, please open an issue on GitHub or contact support@nuvii.ai
