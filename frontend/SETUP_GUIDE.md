# MedCode API Frontend - Setup Guide

## ✅ What's Already Created

### Core Files
- ✅ `package.json` - All dependencies configured
- ✅ `tsconfig.json` - TypeScript configuration
- ✅ `tailwind.config.ts` - Tailwind CSS setup
- ✅ `next.config.js` - Next.js configuration
- ✅ `.env.local` - Environment variables
- ✅ `app/layout.tsx` - Root layout with AuthProvider
- ✅ `app/globals.css` - Global styles with Tailwind

### Library Files
- ✅ `lib/api.ts` - Complete API client with all endpoints
- ✅ `lib/auth.tsx` - Authentication context with login/signup/logout
- ✅ `lib/utils.ts` - Utility functions

### Directory Structure
```
frontend/
├── app/           (created)
├── lib/           (created, all files added)
├── components/    (created)
└── components/ui/ (created)
```

## 🎯 Pages to Create

You need to create these page files in the `app/` directory. Full code is provided in `FRONTEND_FILES.md`.

### 1. Landing Page
**File:** `app/page.tsx`
- Hero section
- Features section (6 cards)
- Pricing section (4 tiers)
- Header with navigation

### 2. Authentication Pages
**Files:** 
- `app/login/page.tsx`
- `app/signup/page.tsx`

Both use the `useAuth()` hook for authentication.

### 3. Dashboard Pages
**Files:**
- `app/dashboard/layout.tsx` - Sidebar navigation
- `app/dashboard/page.tsx` - Usage stats
- `app/dashboard/api-keys/page.tsx` - API key management
- `app/dashboard/docs/page.tsx` - API documentation
- `app/dashboard/billing/page.tsx` - Billing (Stripe portal)

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
cd /Users/murali.local/medcodeapi/frontend
npm install
```

### Step 2: Verify Backend is Running
```bash
# In backend directory
cd ../backend
docker-compose ps
```

You should see:
- ✅ PostgreSQL running on port 5432
- ✅ Redis running on port 6379
- ✅ API running on port 8000

### Step 3: Create the Page Files

Copy the code from `FRONTEND_FILES.md` into the respective files:

```bash
# Create directories
mkdir -p app/login app/signup app/dashboard/api-keys app/dashboard/docs app/dashboard/billing

# Then create each .tsx file with the provided code
```

### Step 4: Start the Frontend
```bash
npm run dev
```

Visit: http://localhost:3000

## 📁 Required Files Summary

| File | Purpose | Status |
|------|---------|--------|
| `app/page.tsx` | Landing page | ⚠️ Create from FRONTEND_FILES.md |
| `app/login/page.tsx` | Login form | ⚠️ Create from FRONTEND_FILES.md |
| `app/signup/page.tsx` | Signup form | ⚠️ Create from FRONTEND_FILES.md |
| `app/dashboard/layout.tsx` | Dashboard shell | ⚠️ Create from FRONTEND_FILES.md |
| `app/dashboard/page.tsx` | Usage stats | ⚠️ Create from FRONTEND_FILES.md |
| `app/dashboard/api-keys/page.tsx` | API key mgmt | ⚠️ Create from FRONTEND_FILES.md |
| `app/dashboard/docs/page.tsx` | API docs viewer | ⚠️ Create (simple) |
| `app/dashboard/billing/page.tsx` | Billing portal | ⚠️ Create (simple) |

## 🎨 UI Components (Optional)

For better styling, you can create these reusable components in `components/ui/`:

- `Button.tsx`
- `Input.tsx`
- `Card.tsx`
- `Badge.tsx`

Or just use regular HTML elements with Tailwind classes.

## 🔌 API Endpoints Available

The API client (`lib/api.ts`) provides:

```typescript
// Auth
authAPI.signup(email, password)
authAPI.login(email, password)
authAPI.getMe()

// API Keys
apiKeysAPI.list()
apiKeysAPI.create(name)
apiKeysAPI.revoke(id)

// Usage
usageAPI.getLogs(limit)
usageAPI.getStats()

// Billing
billingAPI.getPortal()

// Code Search (with API key)
codeAPI.searchICD10(query, apiKey, limit)
codeAPI.searchCPT(query, apiKey, limit)
codeAPI.suggest(text, apiKey, maxResults)
```

## 🧪 Testing the Frontend

### 1. Test Landing Page
Visit http://localhost:3000 - should show the landing page

### 2. Test Signup
1. Click "Get Started" or "Sign up"
2. Enter email and password
3. Should redirect to dashboard after signup

### 3. Test Login
1. Go to http://localhost:3000/login
2. Enter credentials from signup
3. Should redirect to dashboard

### 4. Test Dashboard
1. View usage stats
2. Create an API key
3. Copy the API key (shown once only!)
4. View recent API logs

### 5. Test API Key Usage
Use the created API key to test the backend:
```bash
curl -X GET "http://localhost:8000/api/v1/icd10/search?query=diabetes" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## 🎯 What Works Out of the Box

Since `lib/api.ts` and `lib/auth.tsx` are complete:

✅ Authentication (login/signup/logout)
✅ Token management (automatic)
✅ API calls with auth headers
✅ Protected routes (dashboard)
✅ User session management

You just need to create the UI pages that use these!

## 📝 Simplified Workflow

If you want to test quickly:

1. Create ONLY these 3 files:
   - `app/page.tsx` - Simple landing with link to /login
   - `app/login/page.tsx` - Login form
   - `app/dashboard/page.tsx` - Basic dashboard

2. Start with:
```bash
npm install && npm run dev
```

3. Test the auth flow

4. Then add the other pages incrementally

## 🔥 Common Issues

### Port 3000 in use
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Backend not responding
```bash
# Check backend status
cd ../backend
docker-compose ps
docker-compose logs api
```

### CORS errors
Backend is already configured for `http://localhost:3000` in CORS_ORIGINS.

## 📚 Next Steps

1. Create the page files from FRONTEND_FILES.md
2. Run `npm install`
3. Run `npm run dev`
4. Test the full application
5. Deploy to Vercel (frontend) and your choice for backend

---

**Need Help?** Check `FRONTEND_FILES.md` for complete code examples of all pages!

