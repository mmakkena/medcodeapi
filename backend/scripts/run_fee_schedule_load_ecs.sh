#!/bin/bash
# Load CMS Medicare Fee Schedule data via ECS Batch Task
#
# This script runs an ECS task that:
# 1. Downloads CMS fee schedule data (RVU, GPCI, ZIP locality)
# 2. Loads data into the database
#
# Usage:
#   ./scripts/run_fee_schedule_load_ecs.sh [--year YEAR]
#
# Example:
#   ./scripts/run_fee_schedule_load_ecs.sh --year 2025

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CLUSTER="nuvii-api-cluster"
TASK_DEFINITION="nuvii-batch-task"
REGION="us-east-2"
SUBNETS="subnet-052e86ae1eed57aa0,subnet-06896e788b2a2bdc5,subnet-01040f05784d29041"
SECURITY_GROUPS="sg-080fcd566f9302e10"

# Default year
YEAR=2025
LOAD_RVU=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --year)
            YEAR="$2"
            shift 2
            ;;
        --load-rvu)
            LOAD_RVU=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--year YEAR] [--load-rvu]"
            echo "  --year YEAR    Fee schedule year (default: 2025)"
            echo "  --load-rvu     Also load full RVU data (18,875 codes)"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}=== CMS Fee Schedule Data Load via ECS ===${NC}"
echo "Year: $YEAR"
echo "Cluster: $CLUSTER"
echo "Task Definition: $TASK_DEFINITION"
echo "Load RVU: $LOAD_RVU"
echo ""

# Build the load command based on options
if [ "$LOAD_RVU" = true ]; then
    LOAD_CMD="python scripts/load_fee_schedule_data.py --year $YEAR --gpci-file data/fee_schedule/$YEAR/gpci_$YEAR.csv --zip-file data/fee_schedule/$YEAR/zip_locality_$YEAR.csv --mpfs-file data/fee_schedule/$YEAR/mpfs_rvu_$YEAR.csv"
    echo -e "${YELLOW}Starting fee schedule data load task (with full RVU)...${NC}"
    echo "This will load:"
    echo "  - GPCI data (~110 localities)"
    echo "  - ZIP locality mappings (~43,000 ZIP codes)"
    echo "  - MPFS RVU data (~18,875 codes)"
else
    LOAD_CMD="python scripts/load_fee_schedule_data.py --year $YEAR --gpci-file data/fee_schedule/$YEAR/gpci_$YEAR.csv --zip-file data/fee_schedule/$YEAR/zip_locality_$YEAR.csv"
    echo -e "${YELLOW}Starting fee schedule data load task...${NC}"
    echo "This will load:"
    echo "  - GPCI data (~110 localities)"
    echo "  - ZIP locality mappings (~43,000 ZIP codes)"
fi
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
            \"command\": [\"sh\", \"-c\", \"if [ ! -f data/fee_schedule/$YEAR/gpci_$YEAR.csv ]; then echo 'CSV files not found, downloading...' && python scripts/download_feescheduler_cms_data.py --year $YEAR; fi && $LOAD_CMD && echo FEE_SCHEDULE_LOAD_COMPLETE\"]
        }]
    }" \
    --query 'tasks[0].taskArn' \
    --output text)

if [ -z "$TASK_ARN" ] || [ "$TASK_ARN" = "None" ]; then
    echo -e "${RED}Failed to start ECS task${NC}"
    exit 1
fi

echo -e "${GREEN}Task started: $TASK_ARN${NC}"
echo ""

# Extract task ID for easier reference
TASK_ID=$(echo "$TASK_ARN" | rev | cut -d'/' -f1 | rev)

# Step 2: Wait for task to complete
echo -e "${YELLOW}Waiting for task to complete...${NC}"
echo "Task ID: $TASK_ID"
echo ""

while true; do
    TASK_INFO=$(aws ecs describe-tasks \
        --cluster "$CLUSTER" \
        --tasks "$TASK_ARN" \
        --region "$REGION" \
        --query 'tasks[0].{status:lastStatus,exitCode:containers[0].exitCode,reason:stoppedReason}' \
        --output json)

    TASK_STATUS=$(echo "$TASK_INFO" | jq -r '.status')

    if [ "$TASK_STATUS" = "STOPPED" ]; then
        EXIT_CODE=$(echo "$TASK_INFO" | jq -r '.exitCode')
        REASON=$(echo "$TASK_INFO" | jq -r '.reason // empty')

        if [ "$EXIT_CODE" = "0" ]; then
            echo -e "${GREEN}Task completed successfully!${NC}"
            break
        else
            echo -e "${RED}Task failed with exit code: $EXIT_CODE${NC}"
            if [ -n "$REASON" ]; then
                echo "Reason: $REASON"
            fi
            echo ""
            echo "Check CloudWatch logs for details:"
            echo "  Log group: /ecs/nuvii-batch-task"
            echo "  Task ID: $TASK_ID"
            exit 1
        fi
    fi

    echo "  Status: $TASK_STATUS"
    sleep 10
done

# Summary
echo ""
echo -e "${GREEN}=== Fee Schedule Load Complete ===${NC}"
echo "Year: $YEAR"
echo "Data loaded:"
echo "  - GPCI localities (~110 records)"
echo "  - ZIP to locality mappings (~43,000 records)"
echo ""
echo "To verify, test the API:"
echo "  curl 'https://api.nuvii.ai/api/v1/fee-schedule/price?code=99213&locality=01'"
echo ""
echo -e "${GREEN}Done!${NC}"
