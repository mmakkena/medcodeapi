# Nuvii API - Quick Start Guide

## 🎯 Choose Your Path

### Path A: Launch Fast (30 mins) 💨
**Use Railway** - Get live today, optimize later

### Path B: Launch Free (3 hours) 🆓  
**Use AWS** - FREE for 12 months, pro infrastructure

---

## 🚀 PATH A: Railway (Fastest)

### Prerequisites:
- [ ] Frontend pages created (copy from FRONTEND_FILES.md)
- [ ] GitHub account
- [ ] Credit card (for Railway)

### Steps:

**1. Test Locally (15 mins)**
```bash
cd /Users/murali.local/nuviiapi/frontend
npm install
npm run dev
# Visit http://localhost:3000 and test
```

**2. Push to GitHub (5 mins)**
```bash
cd /Users/murali.local/nuviiapi
git init
git add .
git commit -m "Initial commit"
gh repo create nuviiapi --private --source=. --push
```

**3. Deploy Backend to Railway (10 mins)**
- Go to https://railway.app
- "New Project" → "Deploy from GitHub"
- Select repository
- Add PostgreSQL database
- Add Redis database
- Add environment variables (see DEPLOYMENT_GUIDE.md)
- Deploy!

**4. Deploy Frontend to Vercel (5 mins)**
- Go to https://vercel.com
- "Import Project" → GitHub
- Root directory: `frontend`
- Add env: `NEXT_PUBLIC_API_URL=<your-railway-url>`
- Deploy!

**5. Configure Domain (5 mins)**
- Railway: Set custom domain `api.nuvii.ai`
- Vercel: Set custom domain `nuvii.ai`
- Update DNS at registrar

**Total Time: 30-40 minutes**
**Cost: $5-20/month**

---

## 🆓 PATH B: AWS Free Tier (Most Economical)

### Prerequisites:
- [ ] Frontend pages created
- [ ] AWS account
- [ ] AWS CLI installed
- [ ] 2-3 hours free time

### Steps:

Follow **AWS_DEPLOYMENT_GUIDE.md** step by step:

1. Create AWS account (10 mins)
2. Create RDS PostgreSQL (15 mins)
3. Create ElastiCache Redis (10 mins)
4. Deploy with ECS Fargate (20 mins)
5. Set up Load Balancer (15 mins)
6. Configure SSL (10 mins)
7. Set up Route53 DNS (15 mins)
8. Deploy frontend to Vercel (10 mins)
9. Run migrations (5 mins)
10. Test! (10 mins)

**Total Time: 2-3 hours**
**Cost: $0 for 12 months**

---

## 📋 Before You Deploy (Any Path)

### 1. Complete Frontend Pages

Copy code from `frontend/FRONTEND_FILES.md` into:

```bash
cd /Users/murali.local/nuviiapi/frontend

# Create these files:
app/page.tsx                      # Landing page
app/login/page.tsx                # Login
app/signup/page.tsx               # Signup
app/dashboard/layout.tsx          # Dashboard shell
app/dashboard/page.tsx            # Usage stats
app/dashboard/api-keys/page.tsx   # API keys
app/dashboard/docs/page.tsx       # Docs viewer
app/dashboard/billing/page.tsx    # Billing
```

### 2. Test Backend Locally

```bash
cd /Users/murali.local/nuviiapi/backend
docker-compose ps

# Should see:
# ✓ backend-db-1
# ✓ backend-redis-1  
# ✓ backend-api-1
```

### 3. Test Frontend Locally

```bash
cd /Users/murali.local/nuviiapi/frontend
npm install
npm run dev

# Visit http://localhost:3000
# Sign up, create API key, test search
```

---

## 🎯 Post-Deployment Checklist

Once deployed:

- [ ] Visit https://nuvii.ai (frontend)
- [ ] Visit https://api.nuvii.ai/docs (backend API docs)
- [ ] Sign up for account
- [ ] Log in to dashboard
- [ ] Create API key
- [ ] Test API call:
  ```bash
  curl "https://api.nuvii.ai/api/v1/icd10/search?query=diabetes" \
    -H "Authorization: Bearer YOUR_API_KEY"
  ```
- [ ] Check usage appears in dashboard
- [ ] Verify SSL certificate (🔒 in browser)

---

## 📚 Documentation Reference

| Document | Purpose |
|----------|---------|
| **QUICK_START.md** (this file) | Choose deployment path |
| **AWS_DEPLOYMENT_GUIDE.md** | Detailed AWS setup (FREE) |
| **DEPLOYMENT_GUIDE.md** | Railway + all options |
| **DEPLOYMENT_COMPARISON.md** | Compare all options |
| **frontend/FRONTEND_FILES.md** | All page code |
| **frontend/SETUP_GUIDE.md** | Frontend local setup |
| **backend/README.md** | Backend documentation |
| **PROJECT_STATUS.md** | Overall project status |

---

## 💡 My Recommendation

**For nuvii.ai:**

### Week 1: Railway
Get live fast, test with users

### Month 2: AWS  
Migrate to free tier, save money

**Why?**
- Launch in 30 minutes vs 3 hours
- Test idea quickly
- Migrate later (Docker makes it easy)
- Best of both worlds

---

## 🆘 Need Help?

**Stuck on setup?**
- Read the detailed guides above
- Check troubleshooting sections
- AWS/Railway have great support docs

**Still stuck?**
- Railway: Discord community
- AWS: Extensive documentation
- Vercel: Great docs + Discord

---

## ✅ Success Criteria

You're done when:

1. ✅ https://nuvii.ai loads
2. ✅ Can sign up for account
3. ✅ Can log in to dashboard
4. ✅ Can create API key
5. ✅ Can search medical codes
6. ✅ Usage shows in dashboard
7. ✅ SSL certificate active (🔒)

---

## 🚀 Ready to Launch?

**Choose your path:**

- **Fast launch → Railway** (DEPLOYMENT_GUIDE.md)
- **Free launch → AWS** (AWS_DEPLOYMENT_GUIDE.md)
- **Compare first** (DEPLOYMENT_COMPARISON.md)

**Then share your launch!** 🎉

- Product Hunt
- Twitter/X
- LinkedIn
- Reddit r/SideProject

---

**You've got this! Your app is ready to deploy.** 🚀

All the hard work is done. Now just pick a path and follow the guide.

Good luck! 🍀

