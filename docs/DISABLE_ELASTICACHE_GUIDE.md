# How to Disable ElastiCache (Redis) and Save Costs

## TL;DR - Quick Answer

**Yes, you can safely disable ElastiCache!** Your app already has an in-memory fallback for rate limiting. ElastiCache is completely optional.

**Estimated Monthly Savings:** $15-50+ depending on instance type

---

## What Redis is Used For

Redis/ElastiCache is **only** used for:
- ✅ Rate limiting API requests (per-minute, per-day counters)
- ✅ Signup rate limiting (bot protection)

**That's it!** Nothing else depends on Redis.

## Built-in Fallback

Your app already has automatic fallback to in-memory rate limiting. See `backend/app/middleware/rate_limit.py`:

```python
if redis_client:
    # Redis-based rate limiting
    await _check_rate_limit_redis(user_id, per_minute, per_day)
else:
    # In-memory rate limiting (FALLBACK)
    await _check_rate_limit_memory(user_id, per_minute, per_day)
```

### Limitations of In-Memory Fallback

⚠️ **Single Instance Only** - In-memory rate limiting only works correctly if you run a **single ECS task/container**. If you scale to multiple containers, each will have its own independent rate limit counters.

**Example:**
- With Redis: User makes 100 requests → hits rate limit across all containers
- Without Redis (2 containers): User can make 100 requests to each container = 200 total

**Recommendation:**
- ✅ **1 ECS task** - Disable Redis, save money, works perfectly
- ⚠️ **2+ ECS tasks** - Keep Redis OR accept less strict rate limiting

---

## Option 1: Quick Disable (No Infrastructure Changes)

Just remove the REDIS_URL and the app will automatically fall back to in-memory.

### Step 1: Remove REDIS_URL from Parameter Store

```bash
aws ssm delete-parameter \
  --name "/medcodeapi/production/REDIS_URL" \
  --region us-east-2
```

### Step 2: Restart ECS Tasks

```bash
# Get cluster name
CLUSTER_NAME="medcodeapi-cluster"

# Force new deployment
aws ecs update-service \
  --cluster $CLUSTER_NAME \
  --service medcodeapi-service \
  --force-new-deployment \
  --region us-east-2
```

### Step 3: Verify Fallback

Check logs to confirm:
```bash
# Fetch latest logs
aws logs tail /ecs/medcodeapi --follow --region us-east-2
```

You should see:
```
INFO: Redis disabled, using in-memory rate limiting
```

**✅ Done!** Your app is now using in-memory rate limiting. ElastiCache is still running but not being used. You can stop here if you want to test before fully removing.

---

## Option 2: Full Removal (Delete ElastiCache via Terraform)

Completely remove ElastiCache from your infrastructure to save costs.

### Step 1: Backup Terraform Files

```bash
cd infrastructure/terraform
cp rds.tf rds.tf.backup
cp alb.tf alb.tf.backup
cp ecs.tf ecs.tf.backup
cp outputs.tf outputs.tf.backup
```

### Step 2: Remove Redis Resources from Terraform

**File: `infrastructure/terraform/rds.tf`**

Remove lines 42-66:
```terraform
# DELETE THIS SECTION:
# ElastiCache Redis
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-redis-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.project_name}-redis-subnet"
  }
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.project_name}-redis"
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]

  tags = {
    Name = "${var.project_name}-redis"
  }
}
```

**File: `infrastructure/terraform/alb.tf`**

Remove Redis security group (around lines 158-182):
```terraform
# DELETE THIS SECTION:
resource "aws_security_group" "redis" {
  name        = "${var.project_name}-redis-sg"
  description = "Security group for Redis"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Redis from ECS tasks"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-redis-sg"
  }
}
```

**File: `infrastructure/terraform/ecs.tf`**

Remove REDIS_URL environment variable (around lines 57-58):
```terraform
# DELETE THESE LINES:
          {
            name  = "REDIS_URL"
            value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}"
          },
```

**File: `infrastructure/terraform/outputs.tf`**

Remove Redis output (around lines 32-35):
```terraform
# DELETE THIS SECTION:
output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = "${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}"
}
```

**File: `infrastructure/terraform/variables.tf`**

Remove Redis variable (around lines 94-99):
```terraform
# DELETE THIS SECTION:
# Redis
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
}
```

### Step 3: Apply Terraform Changes

```bash
cd infrastructure/terraform

# Review changes
terraform plan

# You should see:
# - aws_elasticache_cluster.redis will be destroyed
# - aws_elasticache_subnet_group.main will be destroyed
# - aws_security_group.redis will be destroyed

# Apply changes
terraform apply
```

### Step 4: Clean Up Parameter Store

```bash
# Remove REDIS_URL if still present
aws ssm delete-parameter \
  --name "/medcodeapi/production/REDIS_URL" \
  --region us-east-2 \
  || echo "Already deleted"
```

### Step 5: Verify Deployment

```bash
# Check ECS service
aws ecs describe-services \
  --cluster medcodeapi-cluster \
  --services medcodeapi-service \
  --region us-east-2

# Check logs
aws logs tail /ecs/medcodeapi --follow --region us-east-2
```

Look for:
```
INFO: Redis disabled, using in-memory rate limiting
```

---

## Cost Savings

### ElastiCache Costs (Monthly)

| Instance Type | Monthly Cost | Your Likely Cost |
|---------------|--------------|------------------|
| cache.t3.micro | ~$12 | ✅ Most common |
| cache.t3.small | ~$24 | |
| cache.t3.medium | ~$49 | |
| cache.t4g.micro | ~$10 | ✅ ARM-based |
| cache.m6g.large | ~$100+ | |

**Additional costs saved:**
- Data transfer: ~$1-5/month
- Snapshots (if configured): Varies

**Total Savings: $15-50+ per month**

---

## When to Keep Redis

Keep Redis/ElastiCache if:

1. ✅ **Running multiple ECS tasks** - Need consistent rate limiting across instances
2. ✅ **High traffic** - Millions of requests/day (in-memory could use RAM)
3. ✅ **Future caching needs** - Planning to add caching features
4. ✅ **Strict rate limiting required** - Bot protection is critical

## When to Remove Redis

Remove Redis/ElastiCache if:

1. ✅ **Single ECS task** - Only running 1 container
2. ✅ **Low/medium traffic** - < 100K requests/day
3. ✅ **Cost-conscious** - Every dollar counts
4. ✅ **Simple deployment** - Less infrastructure to manage

---

## Monitoring After Removal

### Check Application Logs

```bash
# Real-time logs
aws logs tail /ecs/medcodeapi --follow --region us-east-2

# Filter for rate limiting
aws logs tail /ecs/medcodeapi --follow --filter-pattern "rate" --region us-east-2
```

### Monitor Memory Usage

Without Redis, rate limiting data is stored in memory:

```bash
# Check ECS task memory
aws ecs describe-tasks \
  --cluster medcodeapi-cluster \
  --tasks $(aws ecs list-tasks --cluster medcodeapi-cluster --service medcodeapi-service --query 'taskArns[0]' --output text) \
  --region us-east-2
```

**Expected memory impact:** < 10MB for typical usage

### Test Rate Limiting

```bash
# Test API rate limiting
for i in {1..100}; do
  curl -H "Authorization: Bearer YOUR_API_KEY" \
    https://api.nuvii.ai/api/v1/icd10/search?query=diabetes
  sleep 0.1
done
```

You should get `429 Too Many Requests` when limit is exceeded.

---

## Rollback Plan

If you need to re-enable Redis:

### Quick Rollback (Terraform)

```bash
cd infrastructure/terraform

# Restore backups
cp rds.tf.backup rds.tf
cp alb.tf.backup alb.tf
cp ecs.tf.backup ecs.tf
cp outputs.tf.backup outputs.tf

# Apply
terraform apply
```

### Manual Rollback (AWS Console)

1. Go to ElastiCache console
2. Create new Redis cluster:
   - Name: `medcodeapi-redis`
   - Engine: Redis 7.0
   - Instance: cache.t3.micro
   - VPC: Same as your ECS
3. Update Parameter Store with new endpoint
4. Restart ECS tasks

---

## FAQ

**Q: Will this break my app?**
A: No! The app automatically falls back to in-memory rate limiting. It's designed for this.

**Q: What if I scale to multiple containers later?**
A: You can always add Redis back. Or accept slightly less strict rate limiting.

**Q: How much memory will in-memory rate limiting use?**
A: Very little (~1-10MB). It only stores timestamps for recent requests.

**Q: Does this affect database caching?**
A: No. Your database (RDS PostgreSQL) has its own caching. Redis is only for rate limiting.

**Q: Can I use a free Redis alternative?**
A: You could use Redis on a free tier EC2 instance, but the in-memory fallback is simpler and free.

---

## Recommended Approach

**For most users:**

1. ✅ **Test in-memory first** (Option 1)
   - Remove REDIS_URL
   - Run for a week
   - Monitor logs and costs

2. ✅ **Full removal** (Option 2)
   - If everything works well
   - Remove from Terraform
   - Save ongoing costs

**For high-traffic production:**

Keep Redis if:
- Running 2+ ECS tasks
- > 100K requests/day
- Strict rate limiting is critical

---

## Need Help?

If you encounter issues:

1. Check logs: `aws logs tail /ecs/medcodeapi --follow`
2. Verify fallback: Look for "using in-memory rate limiting"
3. Test rate limits: Send rapid requests and verify 429 errors
4. Rollback if needed: Restore Terraform backups

The application is designed to work without Redis - it's a cost optimization, not a breaking change!
