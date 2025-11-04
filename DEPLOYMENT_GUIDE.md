# Nuvii API - Production Deployment Guide

## 🌐 Domain: nuvii.ai

This guide walks you through deploying your application to production.

---

## 📋 Pre-Deployment Checklist

### 1. Complete Local Development
- [ ] Create all frontend page files from `FRONTEND_FILES.md`
- [ ] Run `npm install` in frontend directory
- [ ] Test signup/login flow locally
- [ ] Test API key creation
- [ ] Test code search functionality
- [ ] Verify all dashboard pages work

### 2. Prepare Production Accounts
- [ ] Cloud provider account (AWS/GCP/DigitalOcean/Railway)
- [ ] Vercel account (for frontend)
- [ ] Stripe production account
- [ ] Domain registrar access (nuvii.ai)
- [ ] GitHub repository (for CI/CD)

---

## 🚀 Deployment Architecture

```
nuvii.ai (Frontend - Vercel)
    ↓
api.nuvii.ai (Backend - Cloud Provider)
    ↓
├── PostgreSQL Database (Managed DB)
├── Redis Cache (Managed Redis)
└── Stripe (Payments)
```

---

## 📍 STEP 1: Complete Frontend Pages

If not done yet, create the pages:

```bash
cd /Users/murali.local/nuviiapi/frontend

# Create directories
mkdir -p app/login app/signup app/dashboard/api-keys app/dashboard/docs app/dashboard/billing

# Copy code from FRONTEND_FILES.md into:
# - app/page.tsx
# - app/login/page.tsx
# - app/signup/page.tsx
# - app/dashboard/layout.tsx
# - app/dashboard/page.tsx
# - app/dashboard/api-keys/page.tsx
# - app/dashboard/docs/page.tsx (simple iframe or docs viewer)
# - app/dashboard/billing/page.tsx (Stripe portal link)

# Install and test
npm install
npm run dev
```

**Test locally:** http://localhost:3000

---

## 📍 STEP 2: Deploy Backend to Cloud

### Option A: Railway (Recommended - Easiest)

**Why Railway?**
- Easy Docker deployment
- Managed PostgreSQL & Redis
- Automatic SSL
- $5/month starter plan

**Steps:**

1. **Create Railway Account:** https://railway.app

2. **Create New Project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your GitHub account
   - Select your repository

3. **Add Services:**
   ```
   - PostgreSQL (add from marketplace)
   - Redis (add from marketplace)
   - Web Service (your backend Docker container)
   ```

4. **Configure Environment Variables:**
   ```env
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   REDIS_URL=${{Redis.REDIS_URL}}
   SECRET_KEY=<generate-strong-random-key>
   JWT_SECRET_KEY=<generate-strong-random-key>
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   STRIPE_PUBLISHABLE_KEY=pk_live_...
   CORS_ORIGINS=https://nuvii.ai,https://www.nuvii.ai
   ENVIRONMENT=production
   DEBUG=false
   ```

5. **Deploy:**
   - Railway will auto-deploy from `backend/Dockerfile`
   - Get your backend URL (e.g., `backend-production-xxx.up.railway.app`)

6. **Set Custom Domain:**
   - Railway Settings → Domains
   - Add: `api.nuvii.ai`
   - Update DNS with provided CNAME

### Option B: DigitalOcean App Platform

1. **Create Account:** https://www.digitalocean.com

2. **Create App:**
   - Apps → Create App
   - Connect GitHub repository
   - Select `backend` directory

3. **Add Databases:**
   - Add PostgreSQL Database ($15/month managed)
   - Add Redis Database ($15/month managed)

4. **Configure:**
   - Same environment variables as Railway
   - Deploy
   - Set custom domain: `api.nuvii.ai`

### Option C: AWS (Most Scalable)

1. **ECS with Fargate** for Docker container
2. **RDS** for PostgreSQL
3. **ElastiCache** for Redis
4. **Application Load Balancer** with SSL
5. **Route53** for DNS

---

## 📍 STEP 3: Deploy Frontend to Vercel

**Why Vercel?**
- Built for Next.js
- Automatic deployments
- Free SSL
- CDN included
- Free for hobby projects

**Steps:**

1. **Push to GitHub:**
   ```bash
   cd /Users/murali.local/nuviiapi
   git init
   git add .
   git commit -m "Initial commit - MedCode API"
   gh repo create nuviiapi --private --source=. --remote=origin --push
   ```

2. **Create Vercel Account:** https://vercel.com

3. **Import Project:**
   - New Project → Import from GitHub
   - Select your repository
   - Framework Preset: Next.js
   - Root Directory: `frontend`

4. **Configure Environment Variables:**
   ```env
   NEXT_PUBLIC_API_URL=https://api.nuvii.ai
   ```

5. **Deploy:**
   - Vercel will auto-build and deploy
   - Get deployment URL (e.g., `nuviiapi.vercel.app`)

6. **Set Custom Domain:**
   - Project Settings → Domains
   - Add: `nuvii.ai` and `www.nuvii.ai`
   - Vercel provides DNS instructions

---

## 📍 STEP 4: Configure DNS (Domain Settings)

Go to your domain registrar (GoDaddy, Namecheap, etc.) and add:

### For Vercel (Frontend):
```
Type: A
Name: @
Value: 76.76.21.21 (Vercel IP)

Type: CNAME
Name: www
Value: cname.vercel-dns.com
```

**OR** use Vercel's nameservers (recommended):
- Transfer DNS management to Vercel
- Vercel handles everything

### For Backend (Railway/DigitalOcean):
```
Type: CNAME
Name: api
Value: <your-backend-url> (from Railway/DO)
```

**DNS Propagation:** Takes 1-24 hours

---

## 📍 STEP 5: Set Up Production Database

### Migrate Schema:

```bash
# From your backend deployment environment
alembic upgrade head
```

### Seed Production Data:

```bash
# Run seed script
python scripts/seed_codes.py
```

### Load Full Datasets:

**ICD-10 Codes (70,000+ codes):**
1. Download from CMS: https://www.cms.gov/medicare/coding-billing/icd-10-codes
2. Parse CSV and bulk insert into database
3. Update `scripts/seed_codes.py` with production data loader

**CPT Codes (Licensed):**
1. Purchase AMA CPT license
2. Download CPT code dataset
3. Load into database
4. **Important:** CPT codes are copyrighted by AMA

---

## 📍 STEP 6: Configure Stripe Production

1. **Stripe Dashboard:** https://dashboard.stripe.com

2. **Switch to Live Mode** (toggle in top right)

3. **Create Products:**
   - Free: $0/month (100 requests)
   - Developer: $49/month (10,000 requests)
   - Growth: $299/month (100,000 requests)
   - Enterprise: Custom pricing

4. **Get API Keys:**
   - Developers → API Keys
   - Copy Live Secret Key (`sk_live_...`)
   - Copy Live Publishable Key (`pk_live_...`)

5. **Set Up Webhook:**
   - Developers → Webhooks
   - Add endpoint: `https://api.nuvii.ai/api/v1/billing/webhook`
   - Select events:
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_failed`
   - Copy webhook secret (`whsec_...`)

6. **Update Environment Variables:**
   ```env
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   STRIPE_PUBLISHABLE_KEY=pk_live_...
   ```

---

## 📍 STEP 7: Set Up SSL Certificates

### Frontend (Vercel):
- ✅ Automatic SSL (Let's Encrypt)
- ✅ Auto-renewal
- ✅ HTTP → HTTPS redirect

### Backend (Railway/DigitalOcean):
- ✅ Automatic SSL on custom domains
- ✅ Auto-renewal

### Manual (AWS/Self-hosted):
- Use Certbot for Let's Encrypt
- Or AWS Certificate Manager

---

## 📍 STEP 8: Production Security Checklist

### Backend Security:
```bash
# Update backend/.env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<64-char-random-string>
JWT_SECRET_KEY=<64-char-random-string>
CORS_ORIGINS=https://nuvii.ai,https://www.nuvii.ai
```

Generate secure keys:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Database Security:
- [ ] Enable SSL for database connections
- [ ] Restrict database access to backend IP only
- [ ] Enable automated backups
- [ ] Set up read replicas (optional)

### API Security:
- [ ] Rate limiting enabled (60 req/min)
- [ ] API keys hashed (already implemented)
- [ ] Passwords hashed (already implemented)
- [ ] CORS configured correctly
- [ ] HTTPS only

### Additional Security:
- [ ] Set up firewall rules
- [ ] Enable DDoS protection
- [ ] Set up monitoring alerts
- [ ] Regular security audits

---

## 📍 STEP 9: Monitoring & Logging

### Error Tracking:

**Sentry (Recommended):**
```bash
npm install @sentry/nextjs  # Frontend
pip install sentry-sdk       # Backend
```

Configure:
```typescript
// Frontend: app/layout.tsx
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: "your-sentry-dsn",
  environment: "production",
});
```

```python
# Backend: app/main.py
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    environment="production",
)
```

### Analytics:

**Backend API Analytics:**
- Built-in usage tracking (already implemented)
- Add Grafana/Prometheus for metrics

**Frontend Analytics:**
- Google Analytics
- Vercel Analytics (built-in)
- PostHog (open-source alternative)

### Uptime Monitoring:
- UptimeRobot (free)
- Pingdom
- Better Uptime

Monitor:
- `https://api.nuvii.ai/health`
- `https://nuvii.ai`

---

## 📍 STEP 10: CI/CD Pipeline

### GitHub Actions:

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway
        run: railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Vercel
        run: vercel --prod
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
```

**Auto-deploy on git push!**

---

## 📍 STEP 11: Post-Deployment Testing

### Test Checklist:

1. **Frontend:**
   - [ ] https://nuvii.ai loads
   - [ ] Signup works
   - [ ] Login works
   - [ ] Dashboard loads
   - [ ] Can create API key

2. **Backend:**
   - [ ] https://api.nuvii.ai/health returns 200
   - [ ] https://api.nuvii.ai/docs loads Swagger
   - [ ] Can search ICD-10 codes
   - [ ] Can search CPT codes
   - [ ] Can get code suggestions
   - [ ] Usage tracking works

3. **Integration:**
   - [ ] Frontend → Backend communication works
   - [ ] Authentication flow works end-to-end
   - [ ] API key creation and usage works
   - [ ] Usage stats display correctly

4. **Billing:**
   - [ ] Stripe checkout works
   - [ ] Webhooks receiving events
   - [ ] Subscription status updates

---

## 💰 Cost Estimate

### Minimal Production Setup:

| Service | Provider | Cost |
|---------|----------|------|
| Backend Hosting | Railway | $5-20/month |
| PostgreSQL | Railway | Included |
| Redis | Railway | Included |
| Frontend | Vercel | Free (hobby) |
| Domain | Registrar | $12/year |
| SSL Certificates | Let's Encrypt | Free |
| **Total** | | **~$5-20/month** |

### Scaled Production Setup:

| Service | Provider | Cost |
|---------|----------|------|
| Backend | AWS ECS | $30-100/month |
| PostgreSQL | AWS RDS | $50-200/month |
| Redis | AWS ElastiCache | $30-100/month |
| Frontend | Vercel Pro | $20/month |
| Monitoring | Sentry | $26/month |
| Domain | Registrar | $12/year |
| **Total** | | **~$150-450/month** |

---

## 🎯 Deployment Timeline

**Day 1:**
- [ ] Complete frontend pages
- [ ] Test locally end-to-end
- [ ] Create production accounts

**Day 2:**
- [ ] Deploy backend to Railway/DigitalOcean
- [ ] Set up production database
- [ ] Configure environment variables

**Day 3:**
- [ ] Deploy frontend to Vercel
- [ ] Configure DNS settings
- [ ] Wait for DNS propagation

**Day 4:**
- [ ] Test production deployment
- [ ] Set up Stripe production
- [ ] Configure monitoring

**Day 5:**
- [ ] Load production data
- [ ] Final testing
- [ ] Launch! 🚀

---

## 📞 Support Resources

### Documentation:
- Railway: https://docs.railway.app
- Vercel: https://vercel.com/docs
- Stripe: https://stripe.com/docs
- Next.js: https://nextjs.org/docs

### Community:
- Railway Discord
- Vercel Discord
- Stack Overflow

---

## 🚀 Quick Start Commands

```bash
# 1. Complete frontend
cd frontend
# Create page files from FRONTEND_FILES.md
npm install
npm run dev  # Test locally

# 2. Push to GitHub
cd ..
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/nuviiapi.git
git push -u origin main

# 3. Deploy backend (Railway)
# - Connect GitHub repo to Railway
# - Add PostgreSQL and Redis
# - Configure environment variables
# - Deploy

# 4. Deploy frontend (Vercel)
# - Import GitHub repo to Vercel
# - Set root directory to 'frontend'
# - Add environment variable: NEXT_PUBLIC_API_URL
# - Deploy

# 5. Configure DNS
# - Point nuvii.ai to Vercel
# - Point api.nuvii.ai to Railway

# 6. Test
curl https://api.nuvii.ai/health
open https://nuvii.ai
```

---

## ✅ Final Checklist

Before going live:

- [ ] All frontend pages created and tested
- [ ] Backend deployed and accessible
- [ ] Frontend deployed and accessible
- [ ] DNS configured correctly
- [ ] SSL certificates working
- [ ] Production database with data
- [ ] Stripe production keys configured
- [ ] CORS configured for production domain
- [ ] Error tracking set up
- [ ] Monitoring set up
- [ ] All environment variables set
- [ ] Test full user signup flow
- [ ] Test API key creation and usage
- [ ] Test code search functionality
- [ ] Test billing flow
- [ ] Terms of Service and Privacy Policy pages
- [ ] Support email configured

---

## 🎊 Launch Checklist

Once deployed:

1. **Announce:**
   - [ ] Share on Twitter/X
   - [ ] Post on Product Hunt
   - [ ] Post on Reddit (r/SideProject)
   - [ ] Share on LinkedIn

2. **SEO:**
   - [ ] Submit sitemap to Google
   - [ ] Add meta descriptions
   - [ ] Add OpenGraph tags

3. **Marketing:**
   - [ ] Create demo video
   - [ ] Write blog post
   - [ ] Create API examples

4. **Growth:**
   - [ ] Set up email marketing
   - [ ] Create free tier signup funnel
   - [ ] Track conversion metrics

---

**Need help?** Refer to:
- `PROJECT_STATUS.md` - Overall project status
- `backend/README.md` - Backend documentation
- `frontend/SETUP_GUIDE.md` - Frontend setup

**Ready to deploy? Start with Step 1!**

