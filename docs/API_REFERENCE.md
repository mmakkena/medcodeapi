# MedCode API - Complete API Reference

**Base URL**: `https://api.nuvii.ai`
**Version**: v1
**Protocol**: HTTPS only

## Table of Contents

- [Authentication](#authentication)
- [Error Responses](#error-responses)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
  - [Authentication](#authentication-endpoints)
  - [Code Search](#code-search-endpoints)
  - [Code Suggestions](#code-suggestion-endpoint)
  - [API Key Management](#api-key-management-endpoints)
  - [Usage Tracking](#usage-tracking-endpoints)
  - [Billing](#billing-endpoints)

---

## Authentication

The API supports two types of authentication:

### 1. JWT Bearer Token (For User Management)

Used for managing account settings, API keys, and viewing usage statistics.

```http
Authorization: Bearer <jwt_token>
```

Obtain a JWT token by calling the `/api/v1/auth/login` or `/api/v1/auth/signup` endpoint.

### 2. API Key (For Code Lookups)

Used for searching medical codes and getting code suggestions.

```http
Authorization: Bearer <api_key>
```

Create an API key through `/api/v1/api-keys` endpoint (requires JWT authentication).

---

## Error Responses

All error responses follow this structure:

```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Resource created |
| `204` | Success with no content |
| `400` | Bad request - Invalid input |
| `401` | Unauthorized - Invalid or missing authentication |
| `403` | Forbidden - Valid auth but insufficient permissions |
| `404` | Resource not found |
| `429` | Too many requests - Rate limit exceeded |
| `500` | Internal server error |

---

## Rate Limiting

Rate limits are applied per user and vary by subscription plan:

| Plan | Requests per Month | Rate Limit |
|------|-------------------|------------|
| Free | 100 | Enforced |
| Developer | 10,000 | Enforced |
| Startup | 100,000 | Enforced |
| Enterprise | 1,000,000 | Enforced |

When you exceed your rate limit, you'll receive a `429 Too Many Requests` response.

---

## Endpoints

### Authentication Endpoints

#### POST /api/v1/auth/signup

Register a new user account.

**Authentication**: None
**Request Body**:

```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | User's email address (used for login) |
| `password` | string | Yes | Password (minimum 8 characters recommended) |

**Response** (201 Created):

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z",
  "full_name": null,
  "company_name": null,
  "role": null,
  "auth_provider": "email"
}
```

**Error Responses**:
- `400`: Email already registered

---

#### POST /api/v1/auth/login

Login with email and password to receive JWT token.

**Authentication**: None
**Request Body**:

```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response** (200 OK):

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | JWT token for authenticated requests |
| `token_type` | string | Always "bearer" |

**Error Responses**:
- `401`: Incorrect email or password
- `403`: Inactive user account

**Token Usage**:
Include the access token in subsequent requests:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

#### GET /api/v1/auth/me

Get current user's profile information.

**Authentication**: JWT Bearer Token (required)

**Response** (200 OK):

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z",
  "last_login_at": "2025-01-20T14:20:00Z",
  "full_name": "John Doe",
  "company_name": "Healthcare Inc",
  "role": "developer",
  "auth_provider": "email"
}
```

**Error Responses**:
- `401`: Invalid or expired token

---

#### POST /api/v1/auth/oauth/signin

Sign in or register using OAuth (Google/Microsoft).

**Authentication**: None
**Request Body**:

```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "provider": "google",
  "providerId": "google_user_id_12345",
  "company_name": "Healthcare Inc",
  "role": "developer"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | User's email from OAuth provider |
| `name` | string | No | User's full name |
| `provider` | string | Yes | OAuth provider ("google" or "microsoft") |
| `providerId` | string | Yes | Unique user ID from OAuth provider |
| `company_name` | string | No | User's company name |
| `role` | string | No | User's role/job title |

**Response** (200 OK):

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "company_name": "Healthcare Inc",
    "role": "developer",
    "is_active": true,
    "auth_provider": "google"
  }
}
```

---

### Code Search Endpoints

#### GET /api/v1/icd10/search

Search ICD-10 diagnosis codes by code or description.

**Authentication**: API Key (required)
**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search term (code or description keyword) |
| `limit` | integer | No | 10 | Maximum results (1-100) |

**Example Request**:

```bash
curl -X GET "https://api.nuvii.ai/api/v1/icd10/search?query=hypertension&limit=5" \
  -H "Authorization: Bearer your_api_key_here"
```

**Response** (200 OK):

```json
[
  {
    "code": "I10",
    "description": "Essential (primary) hypertension",
    "category": "Diseases of the circulatory system"
  },
  {
    "code": "I11.0",
    "description": "Hypertensive heart disease with heart failure",
    "category": "Diseases of the circulatory system"
  },
  {
    "code": "I11.9",
    "description": "Hypertensive heart disease without heart failure",
    "category": "Diseases of the circulatory system"
  }
]
```

**Search Behavior**:
1. First searches for exact code prefix match (e.g., "I10" matches "I10", "I10.1", etc.)
2. If no matches, performs fuzzy text search on descriptions
3. Results are case-insensitive

**Error Responses**:
- `401`: Missing or invalid API key
- `429`: Rate limit exceeded
- `500`: Internal server error

---

#### GET /api/v1/cpt/search

Search CPT procedure codes by code or description.

**Authentication**: API Key (required)
**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search term (code or description keyword) |
| `limit` | integer | No | 10 | Maximum results (1-100) |

**Example Request**:

```bash
curl -X GET "https://api.nuvii.ai/api/v1/cpt/search?query=office visit&limit=5" \
  -H "Authorization: Bearer your_api_key_here"
```

**Response** (200 OK):

```json
[
  {
    "code": "99213",
    "description": "Office or other outpatient visit, established patient, 20-29 minutes",
    "category": "Evaluation and Management"
  },
  {
    "code": "99214",
    "description": "Office or other outpatient visit, established patient, 30-39 minutes",
    "category": "Evaluation and Management"
  },
  {
    "code": "99203",
    "description": "Office or other outpatient visit, new patient, 30-44 minutes",
    "category": "Evaluation and Management"
  }
]
```

**Search Behavior**:
- Same search logic as ICD-10 search
- Exact code match first, then fuzzy description search

**Error Responses**:
- `401`: Missing or invalid API key
- `429`: Rate limit exceeded
- `500`: Internal server error

---

### Code Suggestion Endpoint

#### POST /api/v1/suggest

Get AI-powered code suggestions from clinical free-text notes.

**Authentication**: API Key (required)
**Request Body**:

```json
{
  "text": "Patient presents with chronic hypertension and type 2 diabetes mellitus. Blood pressure 160/95. A1C 8.2%.",
  "max_results": 10
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `text` | string | Yes | - | Clinical text/notes to analyze |
| `max_results` | integer | No | 10 | Maximum number of code suggestions to return |

**Example Request**:

```bash
curl -X POST "https://api.nuvii.ai/api/v1/suggest" \
  -H "Authorization: Bearer your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient with acute bronchitis and fever. Prescribed antibiotics.",
    "max_results": 5
  }'
```

**Response** (200 OK):

```json
{
  "suggestions": [
    {
      "code": "J20.9",
      "description": "Acute bronchitis, unspecified",
      "type": "icd10",
      "score": 0.85
    },
    {
      "code": "R50.9",
      "description": "Fever, unspecified",
      "type": "icd10",
      "score": 0.75
    },
    {
      "code": "99213",
      "description": "Office visit, established patient, 20-29 minutes",
      "type": "cpt",
      "score": 0.60
    }
  ],
  "query": "Patient with acute bronchitis and fever. Prescribed antibiotics."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `code` | string | Medical code (ICD-10 or CPT) |
| `description` | string | Human-readable description of the code |
| `type` | string | Code type: "icd10" or "cpt" |
| `score` | float | Relevance score (0.0 to 1.0, higher is more relevant) |

**Algorithm**:
1. Extracts keywords from clinical text (filters common stop words)
2. Searches both ICD-10 and CPT databases for keyword matches
3. Calculates relevance score based on keyword frequency
4. Deduplicates and ranks results by score
5. Returns top N suggestions

**Error Responses**:
- `401`: Missing or invalid API key
- `429`: Rate limit exceeded
- `500`: Internal server error

---

### API Key Management Endpoints

#### GET /api/v1/api-keys

List all active API keys for the current user.

**Authentication**: JWT Bearer Token (required)

**Response** (200 OK):

```json
[
  {
    "id": "key_123e4567-e89b-12d3-a456-426614174000",
    "key_prefix": "nv_live_abcd1234",
    "name": "Production API Key",
    "created_at": "2025-01-15T10:30:00Z",
    "last_used_at": "2025-01-20T14:20:00Z"
  },
  {
    "id": "key_987f6543-c21a-98b7-d654-321987654321",
    "key_prefix": "nv_live_xyz98765",
    "name": "Development Key",
    "created_at": "2025-01-18T09:15:00Z",
    "last_used_at": null
  }
]
```

**Note**: Only the prefix is shown. Full API keys are never stored or retrievable.

---

#### POST /api/v1/api-keys

Create a new API key.

**Authentication**: JWT Bearer Token (required)
**Request Body**:

```json
{
  "name": "Production API Key"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Descriptive name for the API key |

**Response** (201 Created):

```json
{
  "id": "key_123e4567-e89b-12d3-a456-426614174000",
  "key_prefix": "nv_live_abcd1234",
  "name": "Production API Key",
  "api_key": "nv_live_abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx",
  "created_at": "2025-01-20T15:00:00Z"
}
```

**Important**:
- The `api_key` field contains the full API key
- **This is the only time you'll see the full key**
- Store it securely - it cannot be retrieved later
- If lost, you must create a new key and revoke the old one

---

#### DELETE /api/v1/api-keys/{key_id}

Revoke (deactivate) an API key.

**Authentication**: JWT Bearer Token (required)
**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `key_id` | string | UUID of the API key to revoke |

**Response** (204 No Content):
No response body.

**Error Responses**:
- `404`: API key not found or doesn't belong to user

**Note**: Revoked keys are soft-deleted and can be viewed in logs but cannot be used for API requests.

---

### Usage Tracking Endpoints

#### GET /api/v1/usage/logs

Get recent API usage logs for your account.

**Authentication**: JWT Bearer Token (required)
**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 50 | Number of logs to return (1-100) |

**Response** (200 OK):

```json
[
  {
    "id": "log_123e4567-e89b-12d3-a456-426614174000",
    "endpoint": "/api/v1/icd10/search",
    "method": "GET",
    "query_params": {
      "query": "diabetes",
      "limit": 10
    },
    "status_code": 200,
    "response_time_ms": 45,
    "ip_address": "192.168.1.100",
    "created_at": "2025-01-20T15:30:00Z"
  },
  {
    "id": "log_987f6543-c21a-98b7-d654-321987654321",
    "endpoint": "/api/v1/suggest",
    "method": "POST",
    "query_params": {
      "text_length": 128
    },
    "status_code": 200,
    "response_time_ms": 120,
    "ip_address": "192.168.1.100",
    "created_at": "2025-01-20T15:28:00Z"
  }
]
```

---

#### GET /api/v1/usage/stats

Get usage statistics and quota information for your account.

**Authentication**: JWT Bearer Token (required)

**Response** (200 OK):

```json
{
  "total_requests": 1247,
  "requests_this_month": 89,
  "monthly_limit": 10000,
  "percentage_used": 0.89,
  "most_used_endpoint": "/api/v1/icd10/search",
  "period_start": "2025-01-01T00:00:00Z",
  "period_end": "2025-01-31T23:59:59Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `total_requests` | integer | Total API requests all-time |
| `requests_this_month` | integer | API requests in current billing period |
| `monthly_limit` | integer | Monthly request limit based on plan |
| `percentage_used` | float | Percentage of monthly quota used (0-100) |
| `most_used_endpoint` | string | Your most frequently called endpoint |
| `period_start` | string | Start of current billing period |
| `period_end` | string | End of current billing period |

---

### Billing Endpoints

#### GET /api/v1/billing/subscription

Get current subscription and plan details.

**Authentication**: JWT Bearer Token (required)

**Response** (200 OK) - With Active Subscription:

```json
{
  "plan_name": "Developer",
  "monthly_requests": 10000,
  "price_cents": 4900,
  "status": "active",
  "current_period_end": "2025-02-15T10:30:00Z",
  "features": {
    "api_access": true,
    "code_search": true,
    "code_suggestions": true,
    "usage_analytics": true
  }
}
```

**Response** (200 OK) - Free Plan (No Subscription):

```json
{
  "plan_name": "Free",
  "monthly_requests": 100,
  "price_cents": 0,
  "status": "active",
  "features": {
    "api_access": true,
    "code_search": true,
    "code_suggestions": false,
    "usage_analytics": false
  }
}
```

**Subscription Statuses**:
- `active`: Subscription is active and paid
- `trialing`: In trial period
- `past_due`: Payment failed but still accessible
- `canceled`: Subscription canceled (falls back to Free plan)
- `incomplete`: Payment not completed yet

---

#### POST /api/v1/billing/checkout

Create a Stripe checkout session to subscribe to a plan.

**Authentication**: JWT Bearer Token (required)
**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `plan_name` | string | Yes | Plan to subscribe to ("Developer", "Startup", "Enterprise") |

**Example Request**:

```bash
curl -X POST "https://api.nuvii.ai/api/v1/billing/checkout?plan_name=Developer" \
  -H "Authorization: Bearer your_jwt_token"
```

**Response** (200 OK):

```json
{
  "url": "https://checkout.stripe.com/c/pay/cs_test_a1B2c3D4..."
}
```

**Flow**:
1. Call this endpoint to get checkout URL
2. Redirect user to the Stripe checkout page
3. User completes payment on Stripe
4. User is redirected back to your app
5. Subscription is activated via webhook

**Error Responses**:
- `404`: Plan not found
- `400`: Plan does not have Stripe price configured

---

#### GET /api/v1/billing/portal

Get Stripe billing portal URL to manage subscription.

**Authentication**: JWT Bearer Token (required)

**Response** (200 OK):

```json
{
  "url": "https://billing.stripe.com/p/session/test_YWNjdF..."
}
```

**Portal Features**:
- Update payment method
- View billing history and invoices
- Cancel subscription
- Download receipts

**Error Responses**:
- `404`: No active subscription found

---

#### POST /api/v1/billing/webhook

Stripe webhook endpoint for subscription events.

**Authentication**: Stripe signature verification
**Headers**:

```http
stripe-signature: t=1234567890,v1=abc123def456...
```

**Webhook Events Handled**:
- `checkout.session.completed`: New subscription created
- `customer.subscription.created`: Subscription initiated
- `customer.subscription.updated`: Plan changed or renewed
- `customer.subscription.deleted`: Subscription canceled
- `invoice.payment_succeeded`: Payment successful
- `invoice.payment_failed`: Payment failed

**Response** (200 OK):

```json
{
  "status": "success"
}
```

**Note**: This endpoint is called automatically by Stripe. Configure webhook URL in Stripe dashboard:
```
https://api.nuvii.ai/api/v1/billing/webhook
```

**Error Responses**:
- `400`: Invalid webhook signature

---

## Code Examples

### Complete Authentication Flow

```javascript
// 1. Sign up
const signupResponse = await fetch('https://api.nuvii.ai/api/v1/auth/signup', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'dev@example.com',
    password: 'securepassword123'
  })
});
const user = await signupResponse.json();

// 2. Login
const loginResponse = await fetch('https://api.nuvii.ai/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'dev@example.com',
    password: 'securepassword123'
  })
});
const { access_token } = await loginResponse.json();

// 3. Create API Key
const keyResponse = await fetch('https://api.nuvii.ai/api/v1/api-keys', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({ name: 'My App API Key' })
});
const { api_key } = await keyResponse.json();

// 4. Use API Key for code search
const searchResponse = await fetch(
  'https://api.nuvii.ai/api/v1/icd10/search?query=diabetes&limit=5',
  {
    headers: { 'Authorization': `Bearer ${api_key}` }
  }
);
const codes = await searchResponse.json();
console.log(codes);
```

### Python Example

```python
import requests

# Login
login_response = requests.post(
    'https://api.nuvii.ai/api/v1/auth/login',
    json={
        'email': 'dev@example.com',
        'password': 'securepassword123'
    }
)
jwt_token = login_response.json()['access_token']

# Create API Key
key_response = requests.post(
    'https://api.nuvii.ai/api/v1/api-keys',
    headers={'Authorization': f'Bearer {jwt_token}'},
    json={'name': 'Python API Key'}
)
api_key = key_response.json()['api_key']

# Search ICD-10 codes
search_response = requests.get(
    'https://api.nuvii.ai/api/v1/icd10/search',
    params={'query': 'hypertension', 'limit': 5},
    headers={'Authorization': f'Bearer {api_key}'}
)
codes = search_response.json()

for code in codes:
    print(f"{code['code']}: {code['description']}")
```

### Code Suggestion Example

```python
import requests

api_key = 'your_api_key_here'

# Clinical note
clinical_text = """
Patient is a 65-year-old male with chief complaint of chest pain.
History of hypertension and type 2 diabetes mellitus.
Physical exam reveals blood pressure 160/95, heart rate 88.
EKG shows no acute changes. Troponin negative.
Assessment: Likely angina. Rule out acute coronary syndrome.
Plan: Cardiology consult, stress test scheduled.
"""

response = requests.post(
    'https://api.nuvii.ai/api/v1/suggest',
    headers={'Authorization': f'Bearer {api_key}'},
    json={
        'text': clinical_text,
        'max_results': 10
    }
)

suggestions = response.json()['suggestions']

print("ICD-10 Codes:")
for suggestion in suggestions:
    if suggestion['type'] == 'icd10':
        print(f"  {suggestion['code']}: {suggestion['description']} (score: {suggestion['score']:.2f})")

print("\nCPT Codes:")
for suggestion in suggestions:
    if suggestion['type'] == 'cpt':
        print(f"  {suggestion['code']}: {suggestion['description']} (score: {suggestion['score']:.2f})")
```

---

## Best Practices

### Security

1. **Never expose API keys in client-side code**
   - Use environment variables or secure configuration
   - Implement a backend proxy if calling from browsers

2. **Rotate API keys regularly**
   - Create new keys before revoking old ones
   - Update all systems before revocation

3. **Store JWT tokens securely**
   - Use httpOnly cookies or secure storage
   - Never store in localStorage in production

### Performance

1. **Cache results when possible**
   - ICD-10/CPT code lists change infrequently
   - Implement client-side caching with reasonable TTL

2. **Use appropriate limit parameters**
   - Don't request more data than needed
   - Reduce payload size for faster responses

3. **Batch requests when possible**
   - Prefer fewer requests with more data over many small requests

### Rate Limiting

1. **Monitor your usage**
   - Check `/api/v1/usage/stats` regularly
   - Set up alerts before hitting limits

2. **Implement exponential backoff**
   - Retry failed requests with increasing delays
   - Respect 429 responses

3. **Upgrade plan before limits**
   - Plan ahead for traffic spikes
   - Upgrade before reaching 80% of quota

---

## Interactive API Documentation

For interactive API testing and exploration, visit:

- **Swagger UI**: https://api.nuvii.ai/docs
- **ReDoc**: https://api.nuvii.ai/redoc

These provide:
- Try-it-now functionality
- Request/response examples
- Schema validation
- OAuth 2.0 testing

---

## Support

For questions, issues, or feature requests:

- **Email**: support@nuvii.ai
- **Documentation**: https://docs.nuvii.ai
- **Status Page**: https://status.nuvii.ai
- **GitHub Issues**: https://github.com/nuvii/medcode-api/issues

---

## Changelog

### v1.0.0 (Current)
- JWT and API key authentication
- ICD-10 code search
- CPT code search
- AI-powered code suggestions
- Usage tracking and analytics
- Stripe billing integration
- OAuth support (Google, Microsoft)
- User profile management
