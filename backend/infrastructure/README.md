# Infrastructure Setup

## ECS Batch Task Definition

The `nuvii-batch-task` is used for running one-off background tasks like:
- Downloading ICD-10-CM codes from CMS
- Loading codes into the database
- Generating embeddings
- Generating AI facets

### Register the Batch Task Definition

**IMPORTANT**: Before registering, update the environment variables in `nuvii-batch-task-definition.json` with your actual values:

1. **Edit the task definition file**:
   ```bash
   # Replace placeholders with actual values:
   # - DATABASE_URL: Your PostgreSQL connection string
   # - SECRET_KEY: Your application secret key
   # - JWT_SECRET_KEY: Your JWT signing key
   # - REDIS_URL: Your Redis connection string
   # - STRIPE_*: Your Stripe API keys
   # - GOOGLE_*: Your Google OAuth credentials
   ```

2. **Register the task definition**:
   ```bash
   cd backend/infrastructure

   # Register the batch task definition
   aws ecs register-task-definition \
     --cli-input-json file://nuvii-batch-task-definition.json \
     --region us-east-2
   ```

**Alternative**: Copy environment variables from your existing `nuvii-api-task` definition:
```bash
# Get current API task environment variables
aws ecs describe-task-definition \
  --task-definition nuvii-api-task \
  --region us-east-2 \
  --query 'taskDefinition.containerDefinitions[0].environment' \
  --output json

# Copy the environment array into nuvii-batch-task-definition.json
```

### Verify Registration

```bash
aws ecs describe-task-definition \
  --task-definition nuvii-batch-task \
  --region us-east-2 \
  --query 'taskDefinition.{family:family,revision:revision,status:status,cpu:cpu,memory:memory}'
```

### Update the Task Definition

When you need to update (e.g., to use a new Docker image):

```bash
# Modify nuvii-batch-task-definition.json
# Then re-register
aws ecs register-task-definition \
  --cli-input-json file://nuvii-batch-task-definition.json \
  --region us-east-2
```

## Running Batch Tasks

Use the helper script to run batch operations:

```bash
cd backend

# Download ICD-10-CM data for 2026
./scripts/run_icd10_batch.sh download 2026

# Load ICD-10-CM data for 2026
./scripts/run_icd10_batch.sh load 2026

# Download and load in one command
./scripts/run_icd10_batch.sh download-load 2026

# Generate embeddings (long-running, runs in background)
./scripts/run_icd10_batch.sh embeddings 2026

# Generate AI facets
./scripts/run_icd10_batch.sh facets
```

## Task Definition Details

- **Family**: `nuvii-batch-task`
- **CPU**: 512 (can be overridden at runtime for heavy operations)
- **Memory**: 1024 MB (can be overridden at runtime)
- **Network Mode**: awsvpc
- **Launch Type**: FARGATE
- **Image**: Uses same image as API (`nuvii-api:latest`)
- **Logs**: CloudWatch Logs at `/ecs/nuvii-batch-task`

## Environment Variables

The batch task has access to:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - Application secret
- `JWT_SECRET_KEY` - JWT signing key
- `STRIPE_*` - Stripe API keys
- `GOOGLE_*` - Google OAuth credentials

## Monitoring

### View Running Tasks

```bash
aws ecs list-tasks \
  --cluster nuvii-api-cluster \
  --family nuvii-batch-task \
  --region us-east-2
```

### Check Task Status

```bash
aws ecs describe-tasks \
  --cluster nuvii-api-cluster \
  --tasks TASK_ARN \
  --region us-east-2 \
  --query 'tasks[0].{status:lastStatus,exitCode:containers[0].exitCode,reason:containers[0].reason}'
```

### View Logs

```bash
# Get log stream name from task ID
TASK_ID=$(basename TASK_ARN)

# View logs
aws logs tail /ecs/nuvii-batch-task \
  --follow \
  --log-stream-name-prefix batch/$TASK_ID \
  --region us-east-2
```

## Troubleshooting

### Task Fails to Start

1. Check task definition is registered:
   ```bash
   aws ecs describe-task-definition --task-definition nuvii-batch-task --region us-east-2
   ```

2. Check security group allows outbound internet access (for downloading CMS data)

3. Check database connectivity from ECS subnet

### Task Fails During Execution

1. Check CloudWatch Logs:
   ```bash
   aws logs tail /ecs/nuvii-batch-task --follow --region us-east-2
   ```

2. Verify environment variables are correct in task definition

3. Check database has sufficient storage and connections available

## Cost Optimization

- Batch tasks only run when needed (no ongoing costs)
- Uses FARGATE Spot for 70% cost savings (optional)
- Tasks automatically stop when complete

To use FARGATE Spot, modify the `run_icd10_batch.sh` script to add:
```bash
--capacity-provider-strategy capacityProvider=FARGATE_SPOT,weight=1
```
