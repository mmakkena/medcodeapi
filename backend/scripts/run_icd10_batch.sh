#!/bin/bash
# Run ICD-10 data operations via ECS one-off task
#
# This script runs batch tasks on ECS for:
# - Downloading ICD-10-CM codes from CMS
# - Loading ICD-10-CM codes into database
# - Parsing PDF guidelines and extracting code-specific guidance
# - Generating embeddings for semantic search
# - Generating AI facets
#
# Usage:
#   ./scripts/run_icd10_batch.sh download 2026
#   ./scripts/run_icd10_batch.sh load 2026
#   ./scripts/run_icd10_batch.sh download-load 2026  # Both download and load
#   ./scripts/run_icd10_batch.sh embeddings 2026
#   ./scripts/run_icd10_batch.sh facets
#
# Prerequisites:
# - AWS CLI configured
# - ECS cluster and task definition exist
# - Database accessible from ECS tasks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CLUSTER="nuvii-api-cluster"
TASK_DEFINITION="nuvii-batch-task"
REGION="us-east-2"
SUBNETS="subnet-052e86ae1eed57aa0,subnet-06896e788b2a2bdc5,subnet-01040f05784d29041"
SECURITY_GROUPS="sg-080fcd566f9302e10"

# Parse arguments
OPERATION=${1:-help}
YEAR=${2:-2026}

# Function to run an ECS task and wait for completion
run_ecs_task() {
    local task_name=$1
    local command=$2
    local cpu=${3:-512}
    local memory=${4:-1024}

    echo -e "${BLUE}Starting task: ${task_name}${NC}"
    echo "Command: $command"
    echo ""

    TASK_ARN=$(aws ecs run-task \
        --cluster "$CLUSTER" \
        --task-definition "$TASK_DEFINITION" \
        --launch-type FARGATE \
        --region "$REGION" \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUPS],assignPublicIp=ENABLED}" \
        --overrides "{
            \"containerOverrides\": [{
                \"name\": \"nuvii-batch\",
                \"command\": [\"sh\", \"-c\", \"$command\"]
            }],
            \"cpu\": \"$cpu\",
            \"memory\": \"$memory\"
        }" \
        --query 'tasks[0].taskArn' \
        --output text)

    if [ -z "$TASK_ARN" ]; then
        echo -e "${RED}✗ Failed to start task${NC}"
        exit 1
    fi

    echo "Task ARN: $TASK_ARN"
    echo "Waiting for task to complete..."
    echo ""

    # Wait for task to complete
    while true; do
        TASK_STATUS=$(aws ecs describe-tasks \
            --cluster "$CLUSTER" \
            --tasks "$TASK_ARN" \
            --region "$REGION" \
            --query 'tasks[0].lastStatus' \
            --output text 2>/dev/null || echo "UNKNOWN")

        if [ "$TASK_STATUS" = "STOPPED" ]; then
            EXIT_CODE=$(aws ecs describe-tasks \
                --cluster "$CLUSTER" \
                --tasks "$TASK_ARN" \
                --region "$REGION" \
                --query 'tasks[0].containers[0].exitCode' \
                --output text)

            if [ "$EXIT_CODE" = "0" ]; then
                echo -e "${GREEN}✓ Task completed successfully${NC}"
                echo ""
                return 0
            else
                echo -e "${RED}✗ Task failed with exit code: $EXIT_CODE${NC}"
                echo ""
                echo "View logs in CloudWatch:"
                echo "  Task ID: $(basename $TASK_ARN)"
                echo ""
                return 1
            fi
        fi

        echo "  Status: $TASK_STATUS"
        sleep 10
    done
}

# Function to run task in background (fire and forget)
run_ecs_task_async() {
    local task_name=$1
    local command=$2
    local cpu=${3:-512}
    local memory=${4:-1024}

    echo -e "${BLUE}Starting background task: ${task_name}${NC}"
    echo "Command: $command"
    echo ""

    TASK_ARN=$(aws ecs run-task \
        --cluster "$CLUSTER" \
        --task-definition "$TASK_DEFINITION" \
        --launch-type FARGATE \
        --region "$REGION" \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUPS],assignPublicIp=ENABLED}" \
        --overrides "{
            \"containerOverrides\": [{
                \"name\": \"nuvii-batch\",
                \"command\": [\"sh\", \"-c\", \"$command\"]
            }],
            \"cpu\": \"$cpu\",
            \"memory\": \"$memory\"
        }" \
        --query 'tasks[0].taskArn' \
        --output text)

    if [ -z "$TASK_ARN" ]; then
        echo -e "${RED}✗ Failed to start task${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Task started${NC}"
    echo "Task ARN: $TASK_ARN"
    echo ""
    echo "To monitor task status:"
    echo "  aws ecs describe-tasks --cluster $CLUSTER --tasks $TASK_ARN --region $REGION --query 'tasks[0].lastStatus'"
    echo ""
    echo "To view logs in CloudWatch:"
    echo "  Check logs for task: $(basename $TASK_ARN)"
    echo ""
}

# Print usage
print_usage() {
    echo -e "${GREEN}ICD-10 Batch Operations${NC}"
    echo ""
    echo "Usage: $0 <operation> [year]"
    echo ""
    echo "Operations:"
    echo "  migrate              Run Alembic database migration"
    echo "  download <year>       Download ICD-10-CM data from CMS (default: 2026)"
    echo "  load <year>          Load ICD-10-CM codes into database (default: 2026)"
    echo "  download-load <year> Download and load in one operation (default: 2026)"
    echo "  parse-guidelines <year> Parse PDF guidelines and extract code-specific guidance (default: 2026)"
    echo "  embeddings <year>    Generate MedCPT embeddings (long-running, async)"
    echo "  facets               Generate AI clinical facets"
    echo ""
    echo "Examples:"
    echo "  $0 migrate"
    echo "  $0 download 2026"
    echo "  $0 load 2026"
    echo "  $0 download-load 2025"
    echo "  $0 parse-guidelines 2026"
    echo "  $0 embeddings 2026"
    echo "  $0 facets"
    echo ""
    echo "Configuration:"
    echo "  Cluster:      $CLUSTER"
    echo "  Region:       $REGION"
    echo "  Task Def:     $TASK_DEFINITION"
    echo ""
}

# Main operations
case "$OPERATION" in
    migrate)
        echo -e "${YELLOW}=== Run Database Migration ===${NC}"
        echo ""
        run_ecs_task \
            "Run Alembic Migration" \
            "alembic upgrade head && echo MIGRATION_COMPLETE" \
            512 \
            1024
        ;;

    download)
        echo -e "${YELLOW}=== Download ICD-10-CM Data for Year $YEAR ===${NC}"
        echo ""
        run_ecs_task \
            "Download ICD-10-CM $YEAR" \
            "python scripts/download_icd10_data.py --year $YEAR && echo DOWNLOAD_COMPLETE" \
            512 \
            1024
        ;;

    load)
        echo -e "${YELLOW}=== Load ICD-10-CM Codes for Year $YEAR ===${NC}"
        echo ""
        run_ecs_task \
            "Load ICD-10-CM $YEAR" \
            "python scripts/load_icd10_data.py --year $YEAR && echo LOAD_COMPLETE" \
            512 \
            1024
        ;;

    download-load)
        echo -e "${YELLOW}=== Download and Load ICD-10-CM Data for Year $YEAR ===${NC}"
        echo ""
        run_ecs_task \
            "Download and Load ICD-10-CM $YEAR" \
            "python scripts/download_icd10_data.py --year $YEAR && python scripts/load_icd10_data.py --year $YEAR && echo COMPLETE" \
            1024 \
            2048
        ;;

    parse-guidelines)
        echo -e "${YELLOW}=== Parse ICD-10-CM Guidelines for Year $YEAR ===${NC}"
        echo ""
        run_ecs_task \
            "Parse Guidelines $YEAR" \
            "python scripts/parse_icd10_guidelines.py --year $YEAR && echo GUIDELINES_PARSED" \
            1024 \
            2048
        ;;

    embeddings)
        echo -e "${YELLOW}=== Generate MedCPT Embeddings for Year $YEAR ===${NC}"
        echo -e "${RED}WARNING: This operation takes 1-2 hours on CPU!${NC}"
        echo "The task will run in the background."
        echo ""
        read -p "Continue? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Cancelled"
            exit 0
        fi

        run_ecs_task_async \
            "Generate Embeddings $YEAR" \
            "python scripts/generate_embeddings.py --batch-size 32 --year $YEAR && echo EMBEDDINGS_COMPLETE" \
            1024 \
            2048
        ;;

    facets)
        echo -e "${YELLOW}=== Generate AI Clinical Facets ===${NC}"
        echo ""
        run_ecs_task \
            "Generate AI Facets" \
            "python scripts/populate_ai_facets.py && echo FACETS_COMPLETE" \
            512 \
            1024
        ;;

    help|--help|-h)
        print_usage
        exit 0
        ;;

    *)
        echo -e "${RED}Unknown operation: $OPERATION${NC}"
        echo ""
        print_usage
        exit 1
        ;;
esac

echo -e "${GREEN}Done!${NC}"
