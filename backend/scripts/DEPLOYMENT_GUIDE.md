# ICD-10 Enhancement Deployment Guide

This guide explains how to deploy the ICD-10 enhancements to your production database.

## Problem: Database Access

The production RDS database is in a private VPC and cannot be accessed directly from your local machine. This is a security best practice, but it means we need to run migrations and data population scripts from within AWS.

## Solution Options

### Option 1: Local Development/Testing (Recommended First Step)

1. **Install PostgreSQL Locally**
   ```bash
   # macOS
   brew install postgresql@15
   brew install pgvector

   # Start PostgreSQL
   brew services start postgresql@15
   ```

2. **Create Local Database**
   ```bash
   createdb medcodeapi_dev
   psql medcodeapi_dev -c "CREATE EXTENSION vector;"
   ```

3. **Run Migrations Locally**
   ```bash
   export DATABASE_URL="postgresql://localhost:5432/medcodeapi_dev"
   alembic upgrade head
   ```

4. **Test Data Population**
   ```bash
   # Download data
   python scripts/download_icd10_data.py --year 2024

   # Load codes
   python scripts/load_icd10_data.py --year 2024

   # Generate embeddings (small sample for testing)
   python scripts/generate_embeddings.py --batch-size 32

   # Generate facets
   python scripts/populate_ai_facets.py
   ```

### Option 2: Deploy to Production via ECS Task

The recommended way to run these scripts in production is to create a one-time ECS task that has access to the RDS database.

#### Step 1: Create a Migration Task Script

Create a script that runs in your ECS environment:

```bash
#!/bin/bash
# run_migration_and_populate.sh

set -e

echo "Starting ICD-10 data population..."

# Run migrations
echo "Running Alembic migrations..."
alembic upgrade head

# Download data
echo "Downloading CMS data..."
python scripts/download_icd10_data.py --year 2024

# Load codes
echo "Loading codes to database..."
python scripts/load_icd10_data.py --year 2024

# Generate embeddings
echo "Generating embeddings..."
python scripts/generate_embeddings.py --batch-size 32

# Generate facets
echo "Generating AI facets..."
python scripts/populate_ai_facets.py

echo "Data population complete!"
```

#### Step 2: Run as ECS Task

You can run this as a one-time ECS task using the same Docker image as your API:

```bash
# Using AWS CLI
aws ecs run-task \
  --cluster nuvii-api-cluster \
  --task-definition nuvii-api-task \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --overrides '{
    "containerOverrides": [{
      "name": "nuvii-api",
      "command": ["/bin/bash", "-c", "alembic upgrade head && python scripts/download_icd10_data.py && python scripts/load_icd10_data.py && python scripts/generate_embeddings.py --batch-size 32 && python scripts/populate_ai_facets.py"]
    }]
  }'
```

### Option 3: Use AWS Systems Manager Session Manager

If you have an EC2 bastion host or can create one:

```bash
# Connect to bastion
aws ssm start-session --target i-xxxxxxxxx

# On the bastion, install dependencies
sudo yum install python3 git

# Clone repo
git clone <your-repo>
cd medcodeapi/backend

# Install Python dependencies
pip3 install -r requirements.txt

# Set DATABASE_URL
export DATABASE_URL="postgresql://postgres:password@nuvii-db.cvumwwyw0gae.us-east-2.rds.amazonaws.com:5432/nuviiapi"

# Run migrations and scripts
alembic upgrade head
python3 scripts/download_icd10_data.py --year 2024
python3 scripts/load_icd10_data.py --year 2024
python3 scripts/generate_embeddings.py --batch-size 32
python3 scripts/populate_ai_facets.py
```

### Option 4: Create a Dedicated Migration Container

Create a separate Dockerfile for migrations:

```dockerfile
# Dockerfile.migration
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run migration script
CMD ["/bin/bash", "scripts/run_migration_and_populate.sh"]
```

Build and run:

```bash
# Build migration image
docker build -f Dockerfile.migration -t medcodeapi-migration .

# Run with DATABASE_URL
docker run --rm \
  -e DATABASE_URL="postgresql://postgres:password@nuvii-db.cvumwwyw0gae.us-east-2.rds.amazonaws.com:5432/nuviiapi" \
  medcodeapi-migration
```

## Recommended Approach

For your production deployment, I recommend:

1. **Test Locally First** (Option 1)
   - Install PostgreSQL locally
   - Run all migrations and scripts
   - Verify everything works with a small dataset
   - This helps catch issues before touching production

2. **Deploy to Production** (Option 2 or 3)
   - Use ECS run-task for a one-time migration
   - Or create a bastion host with SSM access
   - Run scripts from within AWS network

## Important Considerations

### 1. pgvector Extension

The production database MUST have the pgvector extension installed:

```sql
-- Connect to RDS as superuser
CREATE EXTENSION IF NOT EXISTS vector;
```

If you don't have superuser access, contact AWS support or use RDS parameter groups to enable it.

### 2. Embedding Generation Time

Generating embeddings for 72,000 codes will take significant time:
- **CPU**: 1-2 hours
- **GPU**: 5-10 minutes

For production, consider:
- Running on a GPU-enabled EC2 instance
- Or running overnight on CPU
- Or processing in batches over time

### 3. Data Volume

The complete dataset will add approximately:
- **Codes**: ~500MB
- **Embeddings**: ~500MB
- **Facets**: ~100MB
- **Total**: ~1GB additional database storage

Ensure your RDS instance has sufficient storage.

### 4. Rollback Plan

Before running in production:

```bash
# Backup the database
aws rds create-db-snapshot \
  --db-instance-identifier nuvii-db \
  --db-snapshot-identifier nuvii-db-pre-icd10-enhancement-$(date +%Y%m%d)
```

If something goes wrong:

```bash
# Rollback migration
alembic downgrade -1

# Or restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier nuvii-db-restored \
  --db-snapshot-identifier nuvii-db-pre-icd10-enhancement-YYYYMMDD
```

## Step-by-Step Production Deployment

### Pre-Deployment Checklist

- [ ] Test locally with PostgreSQL + pgvector
- [ ] Verify all 19 model tests pass
- [ ] Create RDS snapshot
- [ ] Verify pgvector extension is installed on RDS
- [ ] Verify sufficient RDS storage (~1GB free)
- [ ] Plan for embedding generation time (1-2 hours CPU)
- [ ] Notify stakeholders of potential downtime

### Deployment Steps

1. **Create RDS Snapshot**
   ```bash
   aws rds create-db-snapshot \
     --db-instance-identifier nuvii-db \
     --db-snapshot-identifier nuvii-db-pre-icd10-$(date +%Y%m%d)
   ```

2. **Install pgvector Extension**
   ```sql
   -- Connect to RDS and run:
   CREATE EXTENSION IF NOT EXISTS vector;
   CREATE EXTENSION IF NOT EXISTS pg_trgm;
   ```

3. **Run Migration**
   ```bash
   # From ECS task or bastion
   alembic upgrade head
   ```

4. **Verify Migration**
   ```sql
   -- Check new tables exist
   SELECT table_name FROM information_schema.tables
   WHERE table_schema = 'public'
   AND table_name IN ('icd10_ai_facets', 'code_mappings', 'icd10_relations', 'icd10_synonyms');

   -- Check new columns in icd10_codes
   SELECT column_name, data_type
   FROM information_schema.columns
   WHERE table_name = 'icd10_codes'
   AND column_name IN ('embedding', 'code_system', 'short_desc', 'long_desc');
   ```

5. **Download and Load Data**
   ```bash
   python scripts/download_icd10_data.py --year 2024
   python scripts/load_icd10_data.py --year 2024
   ```

6. **Verify Data Load**
   ```sql
   SELECT code_system, COUNT(*)
   FROM icd10_codes
   GROUP BY code_system;
   ```

7. **Generate Embeddings** (Long-running)
   ```bash
   # This will take 1-2 hours on CPU
   nohup python scripts/generate_embeddings.py --batch-size 32 > embeddings.log 2>&1 &

   # Monitor progress
   tail -f embeddings.log
   ```

8. **Generate Facets** (Fast)
   ```bash
   python scripts/populate_ai_facets.py
   ```

9. **Verify Complete System**
   ```sql
   -- Check coverage
   SELECT
     (SELECT COUNT(*) FROM icd10_codes WHERE code_system = 'ICD10-CM') as total_codes,
     (SELECT COUNT(*) FROM icd10_codes WHERE code_system = 'ICD10-CM' AND embedding IS NOT NULL) as codes_with_embeddings,
     (SELECT COUNT(*) FROM icd10_ai_facets WHERE code_system = 'ICD10-CM') as codes_with_facets;
   ```

10. **Test API Endpoints**
    - Test semantic search
    - Test hybrid search
    - Test faceted filtering

### Post-Deployment

- [ ] Verify all endpoints work
- [ ] Monitor database performance
- [ ] Check query latency (should be < 300ms for top-10 results)
- [ ] Update API documentation
- [ ] Delete RDS snapshot after 7 days if all is well

## Troubleshooting

### Issue: "extension vector does not exist"

**Solution**: Install pgvector on RDS
```sql
CREATE EXTENSION vector;
```

If you can't create extensions, you need to:
1. Use RDS superuser account
2. Or modify RDS parameter group to allow extensions

### Issue: "Connection timeout to RDS"

**Solution**: Ensure you're running from within AWS VPC
- Use ECS task in same VPC as RDS
- Or use bastion host in same VPC
- Check security group allows connections from source

### Issue: "Embedding generation too slow"

**Solution**: Use GPU instance
```bash
# Launch GPU-enabled EC2 (p3.2xlarge or g4dn.xlarge)
# Install CUDA and run scripts there
```

Or run in batches:
```python
# Modify script to process in chunks
python scripts/generate_embeddings.py --batch-size 32 --limit 1000
```

### Issue: "Out of memory during embedding generation"

**Solution**: Reduce batch size
```bash
python scripts/generate_embeddings.py --batch-size 8
```

## Monitoring

Monitor these metrics during deployment:

```sql
-- Database size
SELECT pg_size_pretty(pg_database_size('nuviiapi'));

-- Table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Long-running queries
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;
```

## Support

If you encounter issues:
1. Check logs in `/var/log/` or CloudWatch
2. Verify database connectivity
3. Check security groups and network ACLs
4. Review RDS error logs in AWS Console
5. Consult scripts/README_DATA_POPULATION.md for detailed troubleshooting
