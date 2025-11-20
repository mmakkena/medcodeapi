# Redis Configuration Documentation

## Current Configuration (Captured: 2025-11-20)

### ElastiCache Serverless Details

```yaml
Cluster Name: medcode-redis
Engine: Redis 7.1
Type: ElastiCache Serverless
Region: us-east-2
Status: Available (as of capture date)

Endpoint:
  Primary: medcode-redis-a39n2s.serverless.use2.cache.amazonaws.com:6379
  Reader:  medcode-redis-a39n2s.serverless.use2.cache.amazonaws.com:6380

Network:
  VPC Security Group: sg-00d94a19d50a936da (nuvii-redis-sg)
  Subnets:
    - subnet-052e86ae1eed57aa0
    - subnet-01040f05784d29041

Backup:
  Snapshot Retention: 1 day
  Daily Snapshot Time: 04:58 UTC

Created: 2025-11-04 14:21:29 UTC
ARN: arn:aws:elasticache:us-east-2:793523315434:serverlesscache:medcode-redis
```

### Security Group Configuration

**Group:** `nuvii-redis-sg` (sg-00d94a19d50a936da)

**Inbound Rules:**
- Protocol: TCP
- Port: 6379
- Source: sg-080fcd566f9302e10 (ECS tasks security group)
- Description: "Allow access to Redis"

**Outbound Rules:**
- All traffic allowed

### Task Definition Configuration

**Environment Variable:**
```bash
REDIS_URL=redis://medcode-redis-a39n2s.serverless.use2.cache.amazonaws.com:6379/0
```

**Location:** Task definition `nuvii-api-task` (hardcoded in environment variables)

---

## Cost Information

### Monthly Costs (Estimated)

| Component | Cost |
|-----------|------|
| Base ElastiCache Serverless | ~$90/month |
| Data storage | ~$5-20/month |
| ECPU usage (traffic-based) | ~$10-40/month |
| Snapshots (1 day retention) | ~$1-5/month |
| **Total** | **~$90-150/month** |

### Savings Opportunity

**If deleted:** Save $90-150/month by using in-memory rate limiting fallback

---

## Management Scripts

### Delete Redis Cluster

```bash
# Delete with final snapshot (recommended)
./scripts/redis-delete.sh

# Delete without snapshot
./scripts/redis-delete.sh --no-snapshot
```

**What happens:**
- ✅ App automatically falls back to in-memory rate limiting
- ✅ No code changes required
- ✅ Save ~$90-150/month
- ⚠️ In-memory rate limiting only accurate with single ECS task

### Recreate Redis Cluster

```bash
./scripts/redis-recreate.sh
```

**What happens:**
- Creates new serverless cache with identical configuration
- Same name, engine version, security groups, subnets
- New endpoint will be generated (update task definition)
- Takes 5-10 minutes to provision

---

## Usage in Application

### Rate Limiting with Redis

**File:** `backend/app/middleware/rate_limit.py`

**Behavior:**
1. App tries to connect to Redis on startup
2. If Redis available: Uses Redis for distributed rate limiting
3. If Redis unavailable: Falls back to in-memory rate limiting

**Code:**
```python
if settings.use_redis:
    try:
        redis_client = await redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        logger.info("Redis connection successful")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        logger.info("Falling back to in-memory rate limiting")
        redis_client = None
```

### Fallback Behavior

**With Redis:**
- Rate limits enforced across all ECS tasks
- Counters persist across container restarts
- Accurate tracking for distributed systems

**Without Redis (in-memory):**
- Rate limits per ECS task (not global)
- Counters reset on container restart
- Works perfectly for single-task deployments

---

## Decision Guide

### When to Keep Redis

Keep Redis if you have:
- ✅ Multiple ECS tasks/containers (need distributed rate limiting)
- ✅ High traffic (millions of requests/day)
- ✅ Strict rate limiting requirements
- ✅ Need for persistent session storage
- ✅ Future caching needs planned

### When to Delete Redis

Delete Redis if you have:
- ✅ Single ECS task (in-memory works perfectly)
- ✅ Low/medium traffic (< 100K requests/day)
- ✅ Cost-conscious budget (save ~$100/month)
- ✅ Simple infrastructure preference
- ✅ Rate limiting is not mission-critical

---

## Current Deployment Status

### ECS Configuration

**Cluster:** (Check with `aws ecs list-clusters`)
**Service:** (Check with `aws ecs list-services`)
**Task Count:** (Check current running tasks)

To check your current setup:
```bash
# List clusters
aws ecs list-clusters --region us-east-2

# List services
aws ecs list-services --cluster <cluster-name> --region us-east-2

# Get task count
aws ecs describe-services \
  --cluster <cluster-name> \
  --services <service-name> \
  --region us-east-2 \
  --query 'services[0].desiredCount'
```

### Recommendation Based on Task Count

- **1 task:** Delete Redis, save money, in-memory works great
- **2-3 tasks:** Consider deleting, accept slightly less strict rate limiting
- **4+ tasks:** Keep Redis for accurate distributed rate limiting

---

## Testing Fallback Behavior

### Option 1: Block Security Group (Temporary)

Test fallback without deleting:

```bash
# Remove Redis access
aws ec2 revoke-security-group-ingress \
  --group-id sg-00d94a19d50a936da \
  --protocol tcp \
  --port 6379 \
  --source-group sg-080fcd566f9302e10 \
  --region us-east-2

# Watch logs
aws logs tail /ecs/nuvii-api --follow --region us-east-2

# Restore access
aws ec2 authorize-security-group-ingress \
  --group-id sg-00d94a19d50a936da \
  --protocol tcp \
  --port 6379 \
  --source-group sg-080fcd566f9302e10 \
  --region us-east-2
```

### Option 2: Delete and Recreate

Use the provided scripts for full delete/recreate cycle.

---

## Monitoring After Deletion

### Check Logs

```bash
# Real-time logs
aws logs tail /ecs/nuvii-api --follow --region us-east-2

# Filter for Redis/rate limiting
aws logs tail /ecs/nuvii-api --follow --filter-pattern "redis|rate" --region us-east-2
```

**Expected messages after deletion:**
```
ERROR: Failed to connect to Redis: [Errno -2] Name or service not known
INFO: Falling back to in-memory rate limiting
```

### Test Rate Limiting

```bash
# Rapid fire requests to test rate limiting
for i in {1..100}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -H "Authorization: Bearer YOUR_API_KEY" \
    https://api.nuvii.ai/api/v1/procedure/search?query=test
  sleep 0.1
done

# You should see 429 errors when limit is hit
```

### Monitor Memory Usage

In-memory rate limiting uses minimal RAM (~1-10MB):

```bash
# Check ECS task memory
aws ecs describe-tasks \
  --cluster <cluster-name> \
  --tasks $(aws ecs list-tasks --cluster <cluster-name> --service <service-name> --query 'taskArns[0]' --output text) \
  --region us-east-2 \
  --query 'tasks[0].memory'
```

---

## Rollback Plan

### Quick Rollback

```bash
# Recreate with saved configuration
./scripts/redis-recreate.sh

# Update task definition with new endpoint
# (Endpoint will be different after recreation)
```

### Manual Rollback

If scripts fail, use AWS Console:

1. Go to ElastiCache → Serverless caches
2. Create serverless cache
3. Use settings from configuration above
4. Update task definition with new endpoint

---

## Snapshot Management

### List Snapshots

```bash
aws elasticache describe-serverless-cache-snapshots \
  --region us-east-2 \
  --query 'ServerlessCacheSnapshots[?contains(ServerlessCacheSnapshotName, `medcode-redis`)]'
```

### Delete Old Snapshots

```bash
aws elasticache delete-serverless-cache-snapshot \
  --serverless-cache-snapshot-name <snapshot-name> \
  --region us-east-2
```

**Note:** Snapshots cost ~$0.05/GB/month. Delete when no longer needed.

---

## Related Files

- **Deletion Script:** `scripts/redis-delete.sh`
- **Recreation Script:** `scripts/redis-recreate.sh`
- **Rate Limiting Code:** `backend/app/middleware/rate_limit.py`
- **Configuration Code:** `backend/app/config.py`
- **Disable Guide:** `docs/DISABLE_ELASTICACHE_GUIDE.md`

---

## Support

For issues or questions:
1. Check logs for fallback behavior confirmation
2. Test rate limiting with rapid requests
3. Monitor memory usage if concerned
4. Recreate cluster if needed using provided script

The application is designed to work seamlessly with or without Redis!
