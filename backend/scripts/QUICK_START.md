# ICD-10 Enhancement Quick Start Guide

## TL;DR - Run This Command

```bash
cd /Users/murali.local/medcodeapi/backend
./scripts/run_migration_ecs.sh
```

This automated script will:
1. ✅ Create RDS snapshot (optional)
2. ✅ Run Alembic migration
3. ✅ Download CMS data (~72,000 codes)
4. ✅ Load codes into database
5. ✅ Generate AI facets
6. ⏳ Generate embeddings (1-2 hours, optional)

## Prerequisites (IMPORTANT!)

### 1. Install pgvector Extension on RDS

**This is CRITICAL - the migration will fail without it!**

Connect to your RDS database and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

To verify it's installed:

```sql
SELECT * FROM pg_extension WHERE extname IN ('vector', 'pg_trgm');
```

If you can't create extensions (permission denied), you need to:
- Use the RDS master user account
- Or contact AWS support to enable pgvector

### 2. Verify AWS CLI is Configured

```bash
aws sts get-caller-identity
```

Should return your AWS account info.

### 3. Check RDS Storage

Ensure you have at least 1GB free storage:

```bash
aws rds describe-db-instances \
  --db-instance-identifier nuvii-db \
  --region us-east-2 \
  --query 'DBInstances[0].{AllocatedStorage:AllocatedStorage,UsedStorage:UsedStorage}'
```

## Running the Migration

### Option A: Automated Script (Recommended)

```bash
cd /Users/murali.local/medcodeapi/backend
./scripts/run_migration_ecs.sh
```

The script will:
- Guide you through each step
- Wait for each task to complete
- Show progress and status
- Provide CloudWatch log links
- Handle errors gracefully

### Option B: Manual Step-by-Step

If you prefer to run each step manually:

#### Step 1: Snapshot (Optional but Recommended)

```bash
aws rds create-db-snapshot \
  --db-instance-identifier nuvii-db \
  --db-snapshot-identifier nuvii-db-pre-icd10-$(date +%Y%m%d) \
  --region us-east-2
```

#### Step 2: Run Migration

```bash
aws ecs run-task \
  --cluster nuvii-api-cluster \
  --task-definition nuvii-api-task \
  --launch-type FARGATE \
  --region us-east-2 \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-052e86ae1eed57aa0,subnet-06896e788b2a2bdc5,subnet-01040f05784d29041],securityGroups=[sg-080fcd566f9302e10],assignPublicIp=ENABLED}" \
  --overrides '{"containerOverrides":[{"name":"nuvii-api","command":["sh","-c","alembic upgrade head"]}]}'
```

#### Step 3: Load Data

```bash
aws ecs run-task \
  --cluster nuvii-api-cluster \
  --task-definition nuvii-api-task \
  --launch-type FARGATE \
  --region us-east-2 \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-052e86ae1eed57aa0,subnet-06896e788b2a2bdc5,subnet-01040f05784d29041],securityGroups=[sg-080fcd566f9302e10],assignPublicIp=ENABLED}" \
  --overrides '{"containerOverrides":[{"name":"nuvii-api","command":["sh","-c","python scripts/download_icd10_data.py --year 2024 && python scripts/load_icd10_data.py --year 2024"]}]}'
```

#### Step 4: Generate Facets

```bash
aws ecs run-task \
  --cluster nuvii-api-cluster \
  --task-definition nuvii-api-task \
  --launch-type FARGATE \
  --region us-east-2 \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-052e86ae1eed57aa0,subnet-06896e788b2a2bdc5,subnet-01040f05784d29041],securityGroups=[sg-080fcd566f9302e10],assignPublicIp=ENABLED}" \
  --overrides '{"containerOverrides":[{"name":"nuvii-api","command":["sh","-c","python scripts/populate_ai_facets.py"]}]}'
```

#### Step 5: Generate Embeddings (Long Running!)

```bash
aws ecs run-task \
  --cluster nuvii-api-cluster \
  --task-definition nuvii-api-task \
  --launch-type FARGATE \
  --region us-east-2 \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-052e86ae1eed57aa0,subnet-06896e788b2a2bdc5,subnet-01040f05784d29041],securityGroups=[sg-080fcd566f9302e10],assignPublicIp=ENABLED}" \
  --overrides '{"containerOverrides":[{"name":"nuvii-api","command":["sh","-c","python scripts/generate_embeddings.py --batch-size 32"]}],"cpu":"1024","memory":"2048"}'
```

## Monitoring Progress

### Check Task Status

```bash
# List recent tasks
aws ecs list-tasks \
  --cluster nuvii-api-cluster \
  --region us-east-2

# Check specific task
aws ecs describe-tasks \
  --cluster nuvii-api-cluster \
  --tasks <TASK_ARN> \
  --region us-east-2
```

### View Logs

1. Go to AWS Console → CloudWatch → Log Groups
2. Find `/ecs/nuvii-api-task`
3. Look for recent log streams
4. Or use CLI:

```bash
aws logs tail /ecs/nuvii-api-task --follow --region us-east-2
```

## Verification

After all tasks complete, verify the data:

```bash
# Connect to RDS (from within VPC or using bastion)
psql postgresql://postgres:password@nuvii-db.cvumwwyw0gae.us-east-2.rds.amazonaws.com:5432/nuviiapi

# Run verification queries
SELECT code_system, COUNT(*) FROM icd10_codes GROUP BY code_system;

SELECT
  COUNT(*) as total_codes,
  COUNT(embedding) as codes_with_embeddings,
  COUNT(embedding)::float / COUNT(*) * 100 as coverage_percent
FROM icd10_codes WHERE code_system = 'ICD10-CM';

SELECT COUNT(*) as codes_with_facets
FROM icd10_ai_facets WHERE code_system = 'ICD10-CM';
```

Expected results:
- **Total codes**: ~72,000
- **Codes with embeddings**: ~72,000 (100%)
- **Codes with facets**: ~72,000 (100%)

## Troubleshooting

### "extension vector does not exist"

**Solution**: Install pgvector on RDS:
```sql
CREATE EXTENSION vector;
```

### "Task failed to start"

**Reasons**:
- Not enough CPU/memory (default is 256/512)
- Container image not found
- Network configuration issues

**Solution**: Check CloudWatch logs for exact error

### "Connection timeout"

**Reason**: Security group doesn't allow connection from ECS to RDS

**Solution**: Ensure security group `sg-080fcd566f9302e10` allows outbound to RDS port 5432

### "Out of memory during embedding generation"

**Solution**: Use larger task size:
```bash
--overrides '{"containerOverrides":[...],"cpu":"1024","memory":"2048"}'
```

### "Embedding generation too slow"

**Expected**: 1-2 hours on CPU (256 CPU units)
**Faster options**:
- Use larger CPU: `"cpu":"2048"` (~30 mins)
- Skip for now and run later
- Use GPU instance (requires EC2, not supported in Fargate)

## Rollback

If something goes wrong:

```bash
# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier nuvii-db-restored \
  --db-snapshot-identifier nuvii-db-pre-icd10-YYYYMMDD \
  --region us-east-2

# Or rollback migration
# (Connect to RDS from ECS task)
alembic downgrade -1
```

## Time Estimates

- **Migration**: ~30 seconds
- **Data download**: ~2 minutes
- **Data load**: ~5 minutes
- **Facet generation**: ~2 minutes
- **Embedding generation**: 1-2 hours (CPU) or 5-10 mins (GPU)

**Total**: ~2 hours (mostly embedding generation)

## Cost Estimate

- **ECS Tasks**: ~$0.10 (5 tasks × 2 hours max)
- **Data Transfer**: ~$0.01 (downloading CMS data)
- **RDS Storage**: ~$0.12/GB/month (~1GB added)

**Total**: ~$0.25 one-time + $0.12/month ongoing

## Next Steps

After successful deployment:

1. ✅ Test semantic search API
2. ✅ Test hybrid search API
3. ✅ Test faceted filtering
4. ✅ Update API documentation
5. ✅ Monitor performance (< 300ms for top-10 results)
6. ✅ Delete RDS snapshot after 7 days if all is well

## Need Help?

- **Detailed docs**: `scripts/DEPLOYMENT_GUIDE.md`
- **Script usage**: `scripts/README_DATA_POPULATION.md`
- **CloudWatch logs**: AWS Console → CloudWatch → Log Groups → `/ecs/nuvii-api-task`
- **Database access**: Must be from within VPC (use ECS task or bastion)

## Quick Commands Cheat Sheet

```bash
# Run everything
./scripts/run_migration_ecs.sh

# Check recent tasks
aws ecs list-tasks --cluster nuvii-api-cluster --region us-east-2

# View task logs
aws logs tail /ecs/nuvii-api-task --follow --region us-east-2

# Create snapshot
aws rds create-db-snapshot --db-instance-identifier nuvii-db --db-snapshot-identifier nuvii-db-backup-$(date +%Y%m%d) --region us-east-2

# List snapshots
aws rds describe-db-snapshots --db-instance-identifier nuvii-db --region us-east-2

# Check RDS status
aws rds describe-db-instances --db-instance-identifier nuvii-db --region us-east-2 --query 'DBInstances[0].DBInstanceStatus'
```
