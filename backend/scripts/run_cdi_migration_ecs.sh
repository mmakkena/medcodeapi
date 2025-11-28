#!/bin/bash
# Run CDI Knowledge Base Migration on ECS
#
# Executes the CDI knowledge base migration script as an ECS Fargate task.
# Downloads data from S3 and loads into PostgreSQL with vector embeddings.
#
# Prerequisites:
#   1. Upload knowledge base to S3:
#      ./scripts/upload_cdi_knowledge_base_to_s3.sh
#   2. AWS CLI configured with appropriate credentials
#   3. ECS task definition registered (nuvii-batch-task)
#
# Usage:
#   ./scripts/run_cdi_migration_ecs.sh [--all|--em-codes|--protocols|--guidelines] [--generate-embeddings]
#
# Examples:
#   ./scripts/run_cdi_migration_ecs.sh --all
#   ./scripts/run_cdi_migration_ecs.sh --all --generate-embeddings
#   ./scripts/run_cdi_migration_ecs.sh --em-codes
#   ./scripts/run_cdi_migration_ecs.sh --verify-only

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# AWS Configuration
AWS_REGION="us-east-2"
CLUSTER_NAME="nuvii-api-cluster"
TASK_DEFINITION="nuvii-batch-task"
SUBNETS="subnet-052e86ae1eed57aa0,subnet-06896e788b2a2bdc5,subnet-01040f05784d29041"
SECURITY_GROUP="sg-080fcd566f9302e10"

# S3 Configuration
S3_BUCKET="nuvii-data-793523315434"
S3_PREFIX="cdi-knowledge-base"

# Default options
OPERATION="--all"
GENERATE_EMBEDDINGS=""
WAIT_FOR_COMPLETION=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            OPERATION="--all"
            shift
            ;;
        --em-codes)
            OPERATION="--em-codes"
            shift
            ;;
        --protocols)
            OPERATION="--protocols"
            shift
            ;;
        --guidelines)
            OPERATION="--guidelines"
            shift
            ;;
        --verify-only)
            OPERATION="--verify-only"
            shift
            ;;
        --generate-embeddings)
            GENERATE_EMBEDDINGS="--generate-embeddings"
            shift
            ;;
        --no-wait)
            WAIT_FOR_COMPLETION=false
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Operations (choose one):"
            echo "  --all               Run all migrations (default)"
            echo "  --em-codes          Load E/M codes only"
            echo "  --protocols         Load investigation protocols only"
            echo "  --guidelines        Load CDI guidelines only"
            echo "  --verify-only       Only verify existing migration"
            echo ""
            echo "Additional options:"
            echo "  --generate-embeddings  Generate vector embeddings (takes longer)"
            echo "  --no-wait              Don't wait for task completion"
            echo "  --help                 Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}CDI Knowledge Base Migration (ECS)${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "Operation: ${YELLOW}${OPERATION}${NC}"
echo -e "Generate Embeddings: ${YELLOW}${GENERATE_EMBEDDINGS:-No}${NC}"
echo -e "S3 Source: ${YELLOW}s3://${S3_BUCKET}/${S3_PREFIX}${NC}"
echo -e "Cluster: ${YELLOW}${CLUSTER_NAME}${NC}"
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI not installed${NC}"
    exit 1
fi

# Verify AWS credentials
echo -e "${BLUE}Verifying AWS credentials...${NC}"
if ! aws sts get-caller-identity --region ${AWS_REGION} > /dev/null 2>&1; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    exit 1
fi
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}AWS Account: ${ACCOUNT_ID}${NC}"
echo ""

# Check if S3 data exists
echo -e "${BLUE}Checking S3 data...${NC}"
S3_COUNT=$(aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/" --recursive --region ${AWS_REGION} 2>/dev/null | wc -l)
if [ "$S3_COUNT" -eq 0 ]; then
    echo -e "${RED}Error: No data found in S3 at s3://${S3_BUCKET}/${S3_PREFIX}${NC}"
    echo -e "${YELLOW}Run upload script first:${NC}"
    echo -e "  ./scripts/upload_cdi_knowledge_base_to_s3.sh"
    exit 1
fi
echo -e "${GREEN}Found ${S3_COUNT} objects in S3${NC}"
echo ""

# Build the command
CMD="python scripts/migrate_cdi_agent_data.py --use-s3 ${OPERATION}"
if [ -n "${GENERATE_EMBEDDINGS}" ]; then
    CMD="${CMD} ${GENERATE_EMBEDDINGS}"
fi

echo -e "${BLUE}Running ECS Task...${NC}"
echo -e "Command: ${YELLOW}${CMD}${NC}"
echo ""

# Create network configuration JSON
NETWORK_CONFIG=$(cat <<EOF
{
    "awsvpcConfiguration": {
        "subnets": ["${SUBNETS//,/\",\"}"],
        "securityGroups": ["${SECURITY_GROUP}"],
        "assignPublicIp": "ENABLED"
    }
}
EOF
)

# Create container overrides JSON
OVERRIDES=$(cat <<EOF
{
    "containerOverrides": [
        {
            "name": "nuvii-api",
            "command": ["sh", "-c", "${CMD}"],
            "environment": [
                {"name": "CDI_USE_S3", "value": "true"},
                {"name": "CDI_S3_BUCKET", "value": "${S3_BUCKET}"},
                {"name": "CDI_S3_PREFIX", "value": "${S3_PREFIX}"}
            ]
        }
    ]
}
EOF
)

# Run the ECS task
TASK_OUTPUT=$(aws ecs run-task \
    --cluster ${CLUSTER_NAME} \
    --task-definition ${TASK_DEFINITION} \
    --launch-type FARGATE \
    --network-configuration "${NETWORK_CONFIG}" \
    --overrides "${OVERRIDES}" \
    --region ${AWS_REGION} \
    2>&1)

# Extract task ARN
TASK_ARN=$(echo "${TASK_OUTPUT}" | jq -r '.tasks[0].taskArn' 2>/dev/null)

if [ -z "$TASK_ARN" ] || [ "$TASK_ARN" == "null" ]; then
    echo -e "${RED}Error: Failed to start ECS task${NC}"
    echo "${TASK_OUTPUT}"
    exit 1
fi

TASK_ID=$(echo "${TASK_ARN}" | awk -F'/' '{print $NF}')
echo -e "${GREEN}Task started successfully${NC}"
echo -e "Task ARN: ${YELLOW}${TASK_ARN}${NC}"
echo -e "Task ID: ${YELLOW}${TASK_ID}${NC}"
echo ""

# CloudWatch logs URL
LOG_GROUP="/ecs/nuvii-batch-task"
LOGS_URL="https://${AWS_REGION}.console.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#logsV2:log-groups/log-group/\$252Fecs\$252Fnuvii-batch-task/log-events/ecs\$252Fnuvii-api\$252F${TASK_ID}"
echo -e "CloudWatch Logs: ${BLUE}${LOGS_URL}${NC}"
echo ""

if [ "$WAIT_FOR_COMPLETION" = false ]; then
    echo -e "${YELLOW}Task running in background. Check CloudWatch logs for progress.${NC}"
    exit 0
fi

# Wait for task completion
echo -e "${BLUE}Waiting for task completion...${NC}"
echo -e "(Press Ctrl+C to stop waiting - task will continue running)"
echo ""

LAST_STATUS=""
while true; do
    TASK_DESC=$(aws ecs describe-tasks \
        --cluster ${CLUSTER_NAME} \
        --tasks ${TASK_ARN} \
        --region ${AWS_REGION} \
        2>/dev/null)

    CURRENT_STATUS=$(echo "${TASK_DESC}" | jq -r '.tasks[0].lastStatus')
    STOP_CODE=$(echo "${TASK_DESC}" | jq -r '.tasks[0].stopCode // empty')
    STOPPED_REASON=$(echo "${TASK_DESC}" | jq -r '.tasks[0].stoppedReason // empty')

    if [ "$CURRENT_STATUS" != "$LAST_STATUS" ]; then
        echo -e "$(date '+%H:%M:%S') Status: ${YELLOW}${CURRENT_STATUS}${NC}"
        LAST_STATUS="$CURRENT_STATUS"
    fi

    if [ "$CURRENT_STATUS" == "STOPPED" ]; then
        # Get exit code
        EXIT_CODE=$(echo "${TASK_DESC}" | jq -r '.tasks[0].containers[0].exitCode // "unknown"')

        echo ""
        if [ "$EXIT_CODE" == "0" ]; then
            echo -e "${GREEN}======================================${NC}"
            echo -e "${GREEN}Task completed successfully!${NC}"
            echo -e "${GREEN}======================================${NC}"
        else
            echo -e "${RED}======================================${NC}"
            echo -e "${RED}Task failed${NC}"
            echo -e "${RED}======================================${NC}"
            echo -e "Exit Code: ${YELLOW}${EXIT_CODE}${NC}"
            if [ -n "$STOP_CODE" ]; then
                echo -e "Stop Code: ${YELLOW}${STOP_CODE}${NC}"
            fi
            if [ -n "$STOPPED_REASON" ]; then
                echo -e "Reason: ${YELLOW}${STOPPED_REASON}${NC}"
            fi
        fi
        echo ""
        echo -e "View full logs: ${BLUE}${LOGS_URL}${NC}"

        # Fetch recent logs
        echo ""
        echo -e "${BLUE}Recent logs:${NC}"
        echo "----------------------------------------"
        aws logs tail "${LOG_GROUP}" \
            --log-stream-name-prefix "ecs/nuvii-api/${TASK_ID}" \
            --since 5m \
            --region ${AWS_REGION} \
            2>/dev/null | tail -30 || echo "(No recent logs available)"

        if [ "$EXIT_CODE" == "0" ]; then
            exit 0
        else
            exit 1
        fi
    fi

    sleep 10
done
