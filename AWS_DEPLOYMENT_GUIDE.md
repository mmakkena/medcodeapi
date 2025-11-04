# Nuvii API - AWS Deployment Guide
## Deploy to AWS Free Tier (12 Months FREE)

---

## 🎯 What You'll Deploy

```
nuvii.ai
    ↓ (Vercel - FREE)
    Frontend (Next.js)
    
api.nuvii.ai
    ↓ (AWS - FREE for 12 months)
    ├── Application Load Balancer (ALB)
    ├── ECS Fargate (Docker Container)
    ├── RDS PostgreSQL (Database)
    ├── ElastiCache Redis (Cache)
    └── Route53 (DNS)
```

**Total Cost:** $0.00 for first 12 months (AWS Free Tier)
**After 12 months:** ~$30-50/month

---

## 📋 Prerequisites

- [ ] AWS Account (create at aws.amazon.com)
- [ ] Credit card (required for AWS, but won't be charged on Free Tier)
- [ ] AWS CLI installed
- [ ] Docker installed locally
- [ ] Domain: nuvii.ai (you have this ✓)

---

## 🚀 PART 1: AWS Account Setup (10 mins)

### Step 1: Create AWS Account

1. Go to https://aws.amazon.com
2. Click "Create an AWS Account"
3. Follow signup process:
   - Email and password
   - Contact information
   - Credit card (won't be charged)
   - Phone verification
   - Choose "Basic Support - Free"

### Step 2: Verify Free Tier Eligibility

1. Log in to AWS Console
2. Top right → Your Name → "Billing and Cost Management"
3. Left sidebar → "Free Tier"
4. Verify you see "12 months free" for:
   - ✅ EC2 (750 hours/month)
   - ✅ RDS (750 hours/month)
   - ✅ ElastiCache (750 hours/month)

### Step 3: Create IAM User (Security Best Practice)

**Don't use root account for daily work!**

1. **Go to IAM Console:**
   - Services → IAM → Users → "Add users"

2. **Create User:**
   ```
   User name: medcode-admin
   Access type: 
     ✓ Programmatic access (for AWS CLI)
     ✓ AWS Management Console access
   Console password: Custom password (set a strong one)
   ✓ Require password reset: No
   ```

3. **Set Permissions:**
   - Click "Attach existing policies directly"
   - Select: `AdministratorAccess` (for now, restrict later)

4. **Review and Create:**
   - Click "Create user"
   - **IMPORTANT:** Download the credentials CSV
   - Save Access Key ID and Secret Access Key

### Step 4: Install AWS CLI

**macOS:**
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Verify installation
aws --version
```

**Configure AWS CLI:**
```bash
aws configure

# Enter your credentials:
AWS Access Key ID: [from CSV file]
AWS Secret Access Key: [from CSV file]
Default region name: us-east-2
Default output format: json
```

**Test:**
```bash
aws sts get-caller-identity
# Should show your AWS account info
```

---

## 🗄️ PART 2: Create RDS PostgreSQL Database (15 mins)

### Step 1: Create Database Subnet Group

1. **Go to RDS Console:** Services → RDS

2. **Subnet Groups:**
   - Left sidebar → "Subnet groups"
   - Click "Create DB subnet group"
   
   ```
   Name: nuvii-db-subnet-group
   Description: Database subnet group for nuvii API
   VPC: (select default VPC)
   Availability Zones: Select at least 2 (us-east-2a, us-east-2b)
   Subnets: Select all available subnets
   ```
   
   - Click "Create"

### Step 2: Create PostgreSQL Database

1. **Create Database:**
   - Click "Create database"
   
2. **Choose Database Creation Method:**
   - ✓ Standard create

3. **Engine Options:**
   ```
   Engine type: PostgreSQL
   Version: PostgreSQL 15.x (latest)
   ```

4. **Templates:**
   - ✓ **Free tier** ← IMPORTANT!

5. **Settings:**
   ```
   DB instance identifier: nuvii-db
   Master username: postgres
   Master password: [create strong password]
   Confirm password: [same password]
   ```
   
   **SAVE THIS PASSWORD!** You'll need it.

6. **Instance Configuration:**
   - Already set to `db.t3.micro` (Free Tier) ✓

7. **Storage:**
   ```
   Storage type: General Purpose SSD (gp2)
   Allocated storage: 20 GB (Free Tier limit)
   ✓ Enable storage autoscaling: No
   ```

8. **Connectivity:**
   ```
   VPC: (default VPC)
   Subnet group: nuvii-db-subnet-group
   Public access: No
   VPC security group: Create new
   New VPC security group name: nuvii-db-sg
   Availability Zone: No preference
   ```

9. **Database Authentication:**
   - ✓ Password authentication

10. **Additional Configuration:**
    ```
    Initial database name: nuviiapi
    ✓ Automated backups: Enabled (7 days)
    Encryption: Disable (to stay in free tier)
    ```

11. **Click "Create database"**

**Wait 5-10 minutes for database to be created.**

### Step 3: Get Database Endpoint

Once status shows "Available":

1. Click on `nuvii-db`
2. Copy **Endpoint**: `nuvii-db.xxxxxxxxxx.us-east-2.rds.amazonaws.com`
3. Copy **Port**: `5432`

**Your DATABASE_URL will be:**
```
postgresql://postgres:YOUR_PASSWORD@nuvii-db.xxxxxxxxxx.us-east-2.rds.amazonaws.com:5432/nuviiapi
```

---

## 🔴 PART 3: Create ElastiCache Redis (10 mins)

### Step 1: Create Redis Cluster

1. **Go to ElastiCache Console:** Services → ElastiCache

2. **Create Cluster:**
   - Click "Get started"
   - Choose "Redis"

3. **Cluster Settings:**
   ```
   Cluster name: medcode-redis
   Engine version: 7.x (latest)
   Port: 6379
   Parameter group: default
   Node type: cache.t2.micro (Free Tier) ← IMPORTANT
   Number of replicas: 0 (to stay free)
   ```

4. **Subnet Group:**
   - Create new
   - Name: `medcode-redis-subnet`
   - VPC: (default VPC)
   - Select all subnets

5. **Security:**
   - Security groups: Create new
   - Name: `medcode-redis-sg`

6. **Backup:**
   - Disable (to stay free)

7. **Create**

**Wait 5-10 minutes for Redis to be created.**

### Step 2: Get Redis Endpoint

Once status shows "Available":

1. Click on `medcode-redis`
2. Copy **Primary Endpoint**: `medcode-redis.xxxxxx.0001.use1.cache.amazonaws.com:6379`

**Your REDIS_URL will be:**
```
redis://medcode-redis.xxxxxx.0001.use1.cache.amazonaws.com:6379/0
```

---

## 🐳 PART 4: Deploy Backend with ECS Fargate (20 mins)

### Step 1: Create ECR Repository (Docker Image Storage)

```bash
# Create repository
aws ecr create-repository \
  --repository-name nuvii-api \
  --region us-east-2

# Get login password and login to ECR
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 793523315434.dkr.ecr.us-east-2.amazonaws.com
```

**Get your AWS Account ID:**
```bash
aws sts get-caller-identity --query Account --output text
```

### Step 2: Build and Push Docker Image

```bash
cd /Users/murali.local/nuviiapi/backend

# Build image
docker build -t nuvii-api .

# Tag image for ECR
docker tag nuvii-api:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-2.amazonaws.com/nuvii-api:latest

# Push to ECR
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-2.amazonaws.com/nuvii-api:latest
```

### Step 3: Create ECS Cluster

1. **Go to ECS Console:** Services → ECS

2. **Create Cluster:**
   - Click "Create Cluster"
   - Cluster name: `nuvii-cluster`
   - Infrastructure: AWS Fargate (serverless)
   - Click "Create"

### Step 4: Create Task Definition

1. **Task Definitions:**
   - Left sidebar → "Task definitions"
   - Click "Create new task definition"

2. **Configure Task Definition:**
   ```
   Family: nuvii-api-task
   Launch type: Fargate
   Operating system: Linux
   CPU: 0.25 vCPU (256)
   Memory: 0.5 GB (512)
   Task role: None (for now)
   Task execution role: Create new role
   ```

3. **Container Definition:**
   ```
   Container name: nuvii-api
   Image URI: YOUR_ACCOUNT_ID.dkr.ecr.us-east-2.amazonaws.com/nuvii-api:latest
   Memory: 512
   Port mappings: 8000 (TCP)
   ```

4. **Environment Variables:**
   Add these:
   ```
   DATABASE_URL=postgresql://postgres:PASSWORD@nuvii-db.xxx.rds.amazonaws.com:5432/nuviiapi
   REDIS_URL=redis://nuvii-redis.xxx.cache.amazonaws.com:6379/0
   SECRET_KEY=[generate with: python -c "import secrets; print(secrets.token_urlsafe(48))"]
   JWT_SECRET_KEY=[generate another one]
   STRIPE_SECRET_KEY=sk_test_your_key
   STRIPE_WEBHOOK_SECRET=whsec_test
   STRIPE_PUBLISHABLE_KEY=pk_test_your_key
   CORS_ORIGINS=https://nuvii.ai,https://www.nuvii.ai
   ENVIRONMENT=production
   DEBUG=false
   ```

5. **Create**

### Step 5: Create Security Group for ECS

```bash
# Get default VPC ID
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text)

# Create security group for ECS tasks
aws ec2 create-security-group \
  --group-name nuvii-ecs-sg \
  --description "Security group for nuvii API ECS tasks" \
  --vpc-id $VPC_ID

# Get the security group ID
ECS_SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=nuvii-ecs-sg" --query "SecurityGroups[0].GroupId" --output text)

# Allow inbound traffic on port 8000 from anywhere (we'll restrict this with ALB later)
aws ec2 authorize-security-group-ingress \
  --group-id $ECS_SG_ID \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0
```

### Step 6: Update Database Security Group

```bash
# Get RDS security group ID
RDS_SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=nuvii-db-sg" --query "SecurityGroups[0].GroupId" --output text)

# Allow ECS tasks to connect to RDS
aws ec2 authorize-security-group-ingress \
  --group-id $RDS_SG_ID \
  --protocol tcp \
  --port 5432 \
  --source-group $ECS_SG_ID

# Get Redis security group ID
REDIS_SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=nuvii-redis-sg" --query "SecurityGroups[0].GroupId" --output text)

# Allow ECS tasks to connect to Redis
aws ec2 authorize-security-group-ingress \
  --group-id $REDIS_SG_ID \
  --protocol tcp \
  --port 6379 \
  --source-group $ECS_SG_ID
```

---

## ⚖️ PART 5: Create Application Load Balancer (15 mins)

### Step 1: Create Target Group

1. **Go to EC2 Console:** Services → EC2 → Target Groups

2. **Create Target Group:**
   ```
   Target type: IP addresses
   Target group name: nuvii-tg
   Protocol: HTTP
   Port: 8000
   VPC: (default VPC)
   
   Health check:
   Protocol: HTTP
   Path: /health
   ```

3. **Create** (don't register targets yet)

### Step 2: Create Application Load Balancer

1. **Load Balancers:**
   - Click "Create Load Balancer"
   - Select "Application Load Balancer"

2. **Basic Configuration:**
   ```
   Name: nuvii-alb
   Scheme: Internet-facing
   IP address type: IPv4
   ```

3. **Network Mapping:**
   ```
   VPC: (default VPC)
   Mappings: Select ALL availability zones
   ```

4. **Security Groups:**
   - Create new security group: `nuvii-alb-sg`
   - Allow inbound:
     - HTTP (80) from 0.0.0.0/0
     - HTTPS (443) from 0.0.0.0/0

5. **Listeners:**
   ```
   Protocol: HTTP
   Port: 80
   Default action: Forward to nuvii-tg
   ```

6. **Create Load Balancer**

**Copy the Load Balancer DNS name:** `nuvii-alb-xxxxxxxxx.us-east-2.elb.amazonaws.com`

---

## 🔒 PART 6: Set Up SSL Certificate (10 mins)

### Step 1: Request Certificate in ACM

1. **Go to Certificate Manager:** Services → Certificate Manager

2. **Make sure you're in us-east-2 region** (required for ALB)

3. **Request Certificate:**
   ```
   Certificate type: Public certificate
   
   Fully qualified domain names:
   - api.nuvii.ai
   - *.nuvii.ai (optional, for future subdomains)
   
   Validation method: DNS validation
   ```

4. **Click "Request"**

### Step 2: Add DNS Records for Validation

1. Click on the certificate

2. You'll see CNAME records to add

3. **Go to your domain registrar** and add these CNAME records

4. **Wait 5-30 minutes** for validation

### Step 3: Add HTTPS Listener to ALB

Once certificate is validated:

1. **Go back to EC2 → Load Balancers**

2. **Select nuvii-alb**

3. **Listeners tab → Add listener:**
   ```
   Protocol: HTTPS
   Port: 443
   Default action: Forward to nuvii-tg
   
   Default SSL certificate: 
   - Select the certificate you just created
   ```

4. **Save**

5. **Redirect HTTP to HTTPS:**
   - Edit the HTTP:80 listener
   - Change default action to: Redirect to HTTPS:443

---

## 🚀 PART 7: Deploy ECS Service (10 mins)

### Step 1: Create ECS Service

1. **Go to ECS Console → Clusters → nuvii-cluster**

2. **Services → Create:**
   ```
   Launch type: Fargate
   Task definition: nuvii-api-task (latest)
   Service name: nuvii-api-service
   Number of tasks: 1
   
   Deployment type: Rolling update
   Minimum healthy percent: 100
   Maximum percent: 200
   ```

3. **Networking:**
   ```
   VPC: (default)
   Subnets: Select all
   Security groups: nuvii-ecs-sg
   Auto-assign public IP: Enabled
   ```

4. **Load Balancing:**
   ```
   Load balancer type: Application Load Balancer
   Load balancer: nuvii-alb
   
   Container to load balance: nuvii-api:8000
   Target group: nuvii-tg
   ```

5. **Create Service**

**Wait 3-5 minutes for service to deploy**

### Step 2: Verify Deployment

```bash
# Get load balancer DNS
ALB_DNS=$(aws elbv2 describe-load-balancers --names nuvii-alb --query "LoadBalancers[0].DNSName" --output text)

# Test health endpoint
curl http://$ALB_DNS/health

# Should return: {"status":"healthy",...}
```

---

## 🌐 PART 8: Configure DNS with Route53 (15 mins)

### Step 1: Create Hosted Zone

1. **Go to Route53:** Services → Route53

2. **Create Hosted Zone:**
   ```
   Domain name: nuvii.ai
   Type: Public hosted zone
   ```

3. **Create**

4. **Copy the 4 nameserver records** (look like: ns-123.awsdns-45.com)

### Step 2: Update Nameservers at Domain Registrar

Go to your domain registrar (where you bought nuvii.ai) and:

1. Find "DNS Settings" or "Nameservers"
2. Change to "Custom nameservers"
3. Enter the 4 AWS nameservers from Route53
4. Save

**Wait 15-60 minutes for propagation**

### Step 3: Create DNS Records

1. **Back in Route53 → Hosted zones → nuvii.ai**

2. **Create Record for API:**
   ```
   Record name: api
   Record type: A
   Alias: Yes
   Route traffic to: 
     - Alias to Application Load Balancer
     - Region: us-east-2
     - Load balancer: nuvii-alb
   ```

3. **Create** 

### Step 4: Test

```bash
# Wait a few minutes, then test
curl https://api.nuvii.ai/health

# Should return: {"status":"healthy",...}
```

---

## 💻 PART 9: Deploy Frontend to Vercel (10 mins)

Same as before, but with updated API URL:

1. **Push to GitHub** (if not done):
   ```bash
   cd /Users/murali.local/nuviiapi
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/nuviiapi.git
   git push -u origin main
   ```

2. **Deploy to Vercel:**
   - Go to https://vercel.com
   - Import GitHub repository
   - Root directory: `frontend`
   - Environment variable:
     ```
     NEXT_PUBLIC_API_URL=https://api.nuvii.ai
     ```
   - Deploy

3. **Add Domain:**
   - Project Settings → Domains
   - Add: `nuvii.ai`

4. **Update Route53:**
   - Create A record for `@` pointing to Vercel
   - Or use Vercel nameservers

---

## 🗃️ PART 10: Run Database Migrations (5 mins)

### Option A: From Local Machine

```bash
cd /Users/murali.local/nuviiapi/backend

# Update .env with production DATABASE_URL
DATABASE_URL="postgresql://postgres:PASSWORD@nuvii-db.xxx.rds.amazonaws.com:5432/nuviiapi"

# Run migrations
alembic upgrade head

# Seed data
python scripts/seed_codes.py
```

### Option B: From ECS Task (Better)

```bash
# Run one-off task for migrations
aws ecs run-task \
  --cluster nuvii-cluster \
  --launch-type FARGATE \
  --task-definition nuvii-api-task \
  --count 1 \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --overrides '{"containerOverrides":[{"name":"nuvii-api","command":["alembic","upgrade","head"]}]}'
```

---

## ✅ PART 11: Final Testing (10 mins)

### Test Backend:

```bash
# Health check
curl https://api.nuvii.ai/health

# Swagger docs
open https://api.nuvii.ai/docs

# Sign up (should work)
curl -X POST https://api.nuvii.ai/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
```

### Test Frontend:

1. Visit https://nuvii.ai
2. Sign up
3. Log in
4. Create API key
5. Test API call with key

---

## 💰 AWS Free Tier Usage Tracking

**Monitor your usage:**

1. **Billing Dashboard:**
   - Services → Billing → Bills
   - View charges by service

2. **Set Up Billing Alerts:**
   - Billing → Billing preferences
   - ✓ Receive Free Tier Usage Alerts
   - ✓ Receive Billing Alerts
   - Enter email

3. **Create Budget:**
   - Billing → Budgets → Create budget
   - Set $10 threshold alert

**Free Tier Limits:**
- EC2/ECS: 750 hours/month (1 instance 24/7)
- RDS: 750 hours/month db.t3.micro
- ElastiCache: 750 hours/month cache.t2.micro
- Data transfer: 15GB/month

**You should stay under $5/month easily within Free Tier!**

---

## 🔧 Useful AWS CLI Commands

```bash
# View ECS service status
aws ecs describe-services --cluster nuvii-cluster --services nuvii-api-service

# View task logs
aws logs tail /ecs/nuvii-api-task --follow

# Update service (after pushing new Docker image)
aws ecs update-service --cluster nuvii-cluster --service nuvii-api-service --force-new-deployment

# Stop all tasks (for maintenance)
aws ecs update-service --cluster nuvii-cluster --service nuvii-api-service --desired-count 0

# Start tasks again
aws ecs update-service --cluster nuvii-cluster --service nuvii-api-service --desired-count 1
```

---

## 🚨 Troubleshooting

### ECS Task Not Starting:
```bash
# Check task status
aws ecs describe-tasks --cluster nuvii-cluster --tasks TASK_ID

# View logs in CloudWatch
aws logs tail /ecs/nuvii-api-task --follow
```

### Database Connection Failed:
- Verify security group allows ECS → RDS
- Check DATABASE_URL format
- Verify database is "Available"

### Load Balancer 503 Error:
- Check target group health
- Verify ECS task is running
- Check security group rules

### DNS Not Resolving:
- Wait 24 hours for full propagation
- Check nameservers: `dig nuvii.ai NS`
- Verify Route53 records

---

## 📊 Architecture Summary

**What you deployed:**

```
User Request
    ↓
Route53 (DNS)
    ↓
Application Load Balancer (SSL/TLS termination)
    ↓
ECS Fargate Task (Docker container with your FastAPI app)
    ↓
├── RDS PostgreSQL (Database)
└── ElastiCache Redis (Cache)
```

**All on AWS Free Tier for 12 months!**

---

## 🎯 Next Steps

- [ ] Set up CloudWatch alarms
- [ ] Configure automatic backups
- [ ] Set up CI/CD with GitHub Actions
- [ ] Add production Stripe keys
- [ ] Load full ICD-10/CPT datasets
- [ ] Set up monitoring with Sentry
- [ ] Configure auto-scaling policies

---

## 📚 Additional Resources

- **AWS Free Tier:** https://aws.amazon.com/free
- **ECS Documentation:** https://docs.aws.amazon.com/ecs
- **RDS Guide:** https://docs.aws.amazon.com/rds
- **Route53 Guide:** https://docs.aws.amazon.com/route53

---

**Congratulations! Your production-ready API is now live on AWS! 🎉**

