# MedCode API - Quick Start Guide

## 🚀 Get Started in 3 Minutes

### Step 1: Start Services

```bash
cd backend
docker-compose up -d
```

This starts:
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- FastAPI backend (port 8000)

### Step 2: Run Migrations

```bash
docker-compose exec api alembic upgrade head
```

### Step 3: Seed Data

```bash
docker-compose exec api python scripts/seed_codes.py
```

### Step 4: Test the API

Open http://localhost:8000/docs in your browser to see the interactive API documentation (Swagger UI).

---

## 📖 API Flow Example

### 1️⃣ Create Account

```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

### 2️⃣ Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

**Save the `access_token` from the response!**

### 3️⃣ Create API Key

```bash
curl -X POST http://localhost:8000/api/v1/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First API Key"
  }'
```

**Save the `api_key` from the response - it's only shown once!**

### 4️⃣ Search ICD-10 Codes

```bash
curl -X GET "http://localhost:8000/api/v1/icd10/search?query=diabetes" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 5️⃣ Get Code Suggestions

```bash
curl -X POST http://localhost:8000/api/v1/suggest \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient presents with chronic hypertension and type 2 diabetes mellitus",
    "max_results": 5
  }'
```

---

## 🎯 API Endpoints Summary

| Endpoint | Auth | Description |
|----------|------|-------------|
| `POST /api/v1/auth/signup` | None | Create account |
| `POST /api/v1/auth/login` | None | Get JWT token |
| `GET /api/v1/auth/me` | JWT | Get user info |
| `GET /api/v1/icd10/search` | API Key | Search ICD-10 codes |
| `GET /api/v1/cpt/search` | API Key | Search CPT codes |
| `POST /api/v1/suggest` | API Key | Get code suggestions |
| `GET /api/v1/api-keys` | JWT | List API keys |
| `POST /api/v1/api-keys` | JWT | Create API key |
| `DELETE /api/v1/api-keys/{id}` | JWT | Revoke API key |
| `GET /api/v1/usage/logs` | JWT | View usage logs |
| `GET /api/v1/usage/stats` | JWT | View usage stats |
| `GET /api/v1/billing/portal` | JWT | Get billing portal URL |

---

## 🛠️ Useful Commands

### View Logs
```bash
docker-compose logs -f api
```

### Restart API
```bash
docker-compose restart api
```

### Stop All Services
```bash
docker-compose down
```

### Stop and Remove Volumes (Fresh Start)
```bash
docker-compose down -v
```

### Access Database
```bash
docker-compose exec db psql -U postgres -d nuviiapi
```

### Access Redis
```bash
docker-compose exec redis redis-cli
```

---

## 📊 Test Data

The seed script includes:
- **20 ICD-10 codes** (sample - hypertension, diabetes, COPD, etc.)
- **20 CPT codes** (sample - office visits, lab tests, imaging)
- **4 pricing plans** (Free, Developer, Growth, Enterprise)

For production, replace with:
- Full CMS ICD-10 dataset (~70,000 codes)
- Licensed AMA CPT dataset (~10,000 codes)

---

## 🔒 Security Notes

- ✅ API keys are SHA-256 hashed
- ✅ Passwords are bcrypt hashed
- ✅ JWT tokens expire in 30 minutes
- ✅ Rate limiting: 60 req/min, 10,000 req/day (default)
- ✅ CORS restricted to configured origins

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8000
lsof -i :8000

# Change port in docker-compose.yml
```

### Database Connection Error
```bash
# Wait for DB to be ready
docker-compose exec db pg_isready

# Check DB logs
docker-compose logs db
```

### Redis Connection Error
```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Should respond: PONG
```

---

## 📚 Next Steps

1. **Explore the API**: http://localhost:8000/docs
2. **Review the code**: Check `app/` directory
3. **Customize plans**: Edit `scripts/seed_codes.py`
4. **Add real Stripe keys**: Update `.env` with production keys
5. **Load full datasets**: Replace sample ICD-10/CPT data

---

## 🎓 Architecture Highlights

- **Clean Architecture**: Models → Schemas → Services → Routes
- **Dependency Injection**: FastAPI's `Depends()` for middleware
- **Rate Limiting**: Redis-backed with in-memory fallback
- **Database Migrations**: Alembic for version control
- **Full-Text Search**: PostgreSQL pg_trgm + tsvector
- **API Documentation**: Auto-generated Swagger + ReDoc
- **Extensible Suggestions**: Keyword-based MVP, LLM-ready interface

---

**Built with ❤️ using FastAPI, PostgreSQL, and Redis**
