#!/bin/bash
# Run ICD-10 enhancement migration and data population via ECS Task
#
# This script runs a one-time ECS task that:
# 1. Runs Alembic migration
# 2. Downloads CMS ICD-10-CM data
# 3. Loads codes into database
# 4. Generates embeddings (takes 1-2 hours)
# 5. Generates AI facets
#
# Prerequisites:
# - AWS CLI configured
# - pgvector extension installed on RDS
# - Sufficient RDS storage (~1GB free)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CLUSTER="nuvii-api-cluster"
TASK_DEFINITION="nuvii-api-task"
REGION="us-east-2"
SUBNETS="subnet-052e86ae1eed57aa0,subnet-06896e788b2a2bdc5,subnet-01040f05784d29041"
SECURITY_GROUPS="sg-080fcd566f9302e10"

echo -e "${GREEN}=== ICD-10 Enhancement Migration via ECS ===${NC}\n"

# Step 1: Create snapshot (optional but recommended)
echo -e "${YELLOW}Step 1: Creating RDS snapshot (recommended)${NC}"
read -p "Create RDS snapshot before migration? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    SNAPSHOT_ID="nuvii-db-pre-icd10-$(date +%Y%m%d-%H%M%S)"
    echo "Creating snapshot: $SNAPSHOT_ID"
    aws rds create-db-snapshot \
        --db-instance-identifier nuvii-db \
        --db-snapshot-identifier "$SNAPSHOT_ID" \
        --region "$REGION"

    echo -e "${GREEN}✓ Snapshot created: $SNAPSHOT_ID${NC}\n"
else
    echo -e "${YELLOW}⚠ Skipping snapshot creation${NC}\n"
fi

# Step 2: Verify pgvector extension
echo -e "${YELLOW}Step 2: Verify pgvector extension${NC}"
echo "IMPORTANT: The RDS database must have pgvector extension installed."
echo "To check, connect to RDS and run:"
echo "  SELECT * FROM pg_extension WHERE extname = 'vector';"
echo ""
echo "If not installed, run as superuser:"
echo "  CREATE EXTENSION vector;"
echo ""
read -p "Has pgvector extension been installed on RDS? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo -e "${RED}✗ Please install pgvector extension first${NC}"
    echo "See DEPLOYMENT_GUIDE.md for instructions"
    exit 1
fi
echo -e "${GREEN}✓ pgvector confirmed${NC}\n"

# Step 3: Run migration only (fast)
echo -e "${YELLOW}Step 3: Running Alembic migration${NC}"
echo "This will create new tables and columns..."
echo ""

MIGRATION_TASK_ARN=$(aws ecs run-task \
    --cluster "$CLUSTER" \
    --task-definition "$TASK_DEFINITION" \
    --launch-type FARGATE \
    --region "$REGION" \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUPS],assignPublicIp=ENABLED}" \
    --overrides '{
        "containerOverrides": [{
            "name": "nuvii-api",
            "command": ["sh", "-c", "alembic upgrade head && echo MIGRATION_COMPLETE"]
        }]
    }' \
    --query 'tasks[0].taskArn' \
    --output text)

echo "Migration task started: $MIGRATION_TASK_ARN"
echo "Waiting for migration to complete..."

# Wait for task to complete
while true; do
    TASK_STATUS=$(aws ecs describe-tasks \
        --cluster "$CLUSTER" \
        --tasks "$MIGRATION_TASK_ARN" \
        --region "$REGION" \
        --query 'tasks[0].lastStatus' \
        --output text)

    if [ "$TASK_STATUS" = "STOPPED" ]; then
        EXIT_CODE=$(aws ecs describe-tasks \
            --cluster "$CLUSTER" \
            --tasks "$MIGRATION_TASK_ARN" \
            --region "$REGION" \
            --query 'tasks[0].containers[0].exitCode' \
            --output text)

        if [ "$EXIT_CODE" = "0" ]; then
            echo -e "${GREEN}✓ Migration completed successfully${NC}\n"
            break
        else
            echo -e "${RED}✗ Migration failed with exit code: $EXIT_CODE${NC}"
            echo "Check CloudWatch logs for details"
            exit 1
        fi
    fi

    echo "  Status: $TASK_STATUS"
    sleep 10
done

# Step 4: Download and load data
echo -e "${YELLOW}Step 4: Downloading CMS data and loading codes${NC}"
echo "This will download ~72,000 ICD-10-CM codes..."
echo ""

DATA_TASK_ARN=$(aws ecs run-task \
    --cluster "$CLUSTER" \
    --task-definition "$TASK_DEFINITION" \
    --launch-type FARGATE \
    --region "$REGION" \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUPS],assignPublicIp=ENABLED}" \
    --overrides '{
        "containerOverrides": [{
            "name": "nuvii-api",
            "command": ["sh", "-c", "python scripts/download_icd10_data.py --year 2024 && python scripts/load_icd10_data.py --year 2024 && echo DATA_LOAD_COMPLETE"]
        }]
    }' \
    --query 'tasks[0].taskArn' \
    --output text)

echo "Data load task started: $DATA_TASK_ARN"
echo "Waiting for data load to complete..."

# Wait for task to complete
while true; do
    TASK_STATUS=$(aws ecs describe-tasks \
        --cluster "$CLUSTER" \
        --tasks "$DATA_TASK_ARN" \
        --region "$REGION" \
        --query 'tasks[0].lastStatus' \
        --output text)

    if [ "$TASK_STATUS" = "STOPPED" ]; then
        EXIT_CODE=$(aws ecs describe-tasks \
            --cluster "$CLUSTER" \
            --tasks "$DATA_TASK_ARN" \
            --region "$REGION" \
            --query 'tasks[0].containers[0].exitCode' \
            --output text)

        if [ "$EXIT_CODE" = "0" ]; then
            echo -e "${GREEN}✓ Data load completed successfully${NC}\n"
            break
        else
            echo -e "${RED}✗ Data load failed with exit code: $EXIT_CODE${NC}"
            echo "Check CloudWatch logs for details"
            exit 1
        fi
    fi

    echo "  Status: $TASK_STATUS"
    sleep 15
done

# Step 5: Generate facets (fast)
echo -e "${YELLOW}Step 5: Generating AI facets${NC}"
echo "This will generate clinical metadata for all codes..."
echo ""

FACET_TASK_ARN=$(aws ecs run-task \
    --cluster "$CLUSTER" \
    --task-definition "$TASK_DEFINITION" \
    --launch-type FARGATE \
    --region "$REGION" \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUPS],assignPublicIp=ENABLED}" \
    --overrides '{
        "containerOverrides": [{
            "name": "nuvii-api",
            "command": ["sh", "-c", "python scripts/populate_ai_facets.py && echo FACETS_COMPLETE"]
        }]
    }' \
    --query 'tasks[0].taskArn' \
    --output text)

echo "Facet generation task started: $FACET_TASK_ARN"
echo "Waiting for facet generation to complete..."

# Wait for task to complete
while true; do
    TASK_STATUS=$(aws ecs describe-tasks \
        --cluster "$CLUSTER" \
        --tasks "$FACET_TASK_ARN" \
        --region "$REGION" \
        --query 'tasks[0].lastStatus' \
        --output text)

    if [ "$TASK_STATUS" = "STOPPED" ]; then
        EXIT_CODE=$(aws ecs describe-tasks \
            --cluster "$CLUSTER" \
            --tasks "$FACET_TASK_ARN" \
            --region "$REGION" \
            --query 'tasks[0].containers[0].exitCode' \
            --output text)

        if [ "$EXIT_CODE" = "0" ]; then
            echo -e "${GREEN}✓ Facet generation completed successfully${NC}\n"
            break
        else
            echo -e "${RED}✗ Facet generation failed with exit code: $EXIT_CODE${NC}"
            echo "Check CloudWatch logs for details"
            exit 1
        fi
    fi

    echo "  Status: $TASK_STATUS"
    sleep 10
done

# Step 6: Generate embeddings (LONG RUNNING - 1-2 hours on CPU)
echo -e "${YELLOW}Step 6: Generating MedCPT embeddings${NC}"
echo -e "${RED}WARNING: This step will take 1-2 hours on CPU!${NC}"
echo "The task will run in the background. You can monitor it via CloudWatch."
echo ""
read -p "Start embedding generation now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    # Use larger task size for embedding generation
    echo "Starting embedding generation task (this may take 1-2 hours)..."

    EMBEDDING_TASK_ARN=$(aws ecs run-task \
        --cluster "$CLUSTER" \
        --task-definition "$TASK_DEFINITION" \
        --launch-type FARGATE \
        --region "$REGION" \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUPS],assignPublicIp=ENABLED}" \
        --overrides '{
            "containerOverrides": [{
                "name": "nuvii-api",
                "command": ["sh", "-c", "python scripts/generate_embeddings.py --batch-size 32 && echo EMBEDDINGS_COMPLETE"]
            }],
            "cpu": "1024",
            "memory": "2048"
        }' \
        --query 'tasks[0].taskArn' \
        --output text)

    echo "Embedding generation task started: $EMBEDDING_TASK_ARN"
    echo ""
    echo "To monitor progress:"
    echo "  aws ecs describe-tasks --cluster $CLUSTER --tasks $EMBEDDING_TASK_ARN --region $REGION"
    echo ""
    echo "To view logs in CloudWatch:"
    echo "  Check CloudWatch Logs for task: $EMBEDDING_TASK_ARN"
    echo ""
    echo -e "${YELLOW}Note: This task will run for 1-2 hours. You can close this terminal.${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠ Skipping embedding generation${NC}"
    echo "You can run it later with:"
    echo "  python scripts/generate_embeddings.py --batch-size 32"
    echo ""
fi

# Summary
echo -e "${GREEN}=== Migration Summary ===${NC}"
echo "✓ Migration completed"
echo "✓ Data loaded (~72,000 codes)"
echo "✓ AI facets generated"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "⏳ Embeddings generating (1-2 hours)"
    echo "   Task ARN: $EMBEDDING_TASK_ARN"
else
    echo "⚠ Embeddings not started (run manually)"
fi
echo ""
echo "Next steps:"
echo "1. Wait for embedding generation to complete (if started)"
echo "2. Verify data in database (see DEPLOYMENT_GUIDE.md)"
echo "3. Test API endpoints"
echo "4. Update API documentation"
echo ""
echo -e "${GREEN}Done!${NC}"
