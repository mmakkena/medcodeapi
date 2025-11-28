#!/bin/bash
# Upload CDI Knowledge Base to S3
#
# Uploads the CDIAgent knowledge base files to S3 for use by ECS batch tasks.
#
# Usage:
#   ./scripts/upload_cdi_knowledge_base_to_s3.sh [--bucket BUCKET] [--prefix PREFIX]
#
# Default bucket: nuvii-data-793523315434
# Default prefix: cdi-knowledge-base

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default configuration
DEFAULT_BUCKET="nuvii-data-793523315434"
DEFAULT_PREFIX="cdi-knowledge-base"
AWS_REGION="us-east-2"

# Source paths
CDIAGENT_ROOT="/Users/murali.local/CDIAgent"
KNOWLEDGE_BASE_PATH="${CDIAGENT_ROOT}/knowledge_base"
CDI_DOCUMENTS_PATH="${CDIAGENT_ROOT}/cdi_documents"

# Parse arguments
BUCKET="${DEFAULT_BUCKET}"
PREFIX="${DEFAULT_PREFIX}"

while [[ $# -gt 0 ]]; do
    case $1 in
        --bucket)
            BUCKET="$2"
            shift 2
            ;;
        --prefix)
            PREFIX="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--bucket BUCKET] [--prefix PREFIX]"
            echo ""
            echo "Options:"
            echo "  --bucket BUCKET   S3 bucket name (default: ${DEFAULT_BUCKET})"
            echo "  --prefix PREFIX   S3 key prefix (default: ${DEFAULT_PREFIX})"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

S3_BASE="s3://${BUCKET}/${PREFIX}"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}CDI Knowledge Base S3 Upload${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "Source: ${YELLOW}${CDIAGENT_ROOT}${NC}"
echo -e "Target: ${YELLOW}${S3_BASE}${NC}"
echo ""

# Check source paths exist
if [ ! -d "${KNOWLEDGE_BASE_PATH}" ]; then
    echo -e "${RED}Error: Knowledge base path not found: ${KNOWLEDGE_BASE_PATH}${NC}"
    exit 1
fi

if [ ! -d "${CDI_DOCUMENTS_PATH}" ]; then
    echo -e "${RED}Error: CDI documents path not found: ${CDI_DOCUMENTS_PATH}${NC}"
    exit 1
fi

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
echo -e "${GREEN}AWS credentials OK${NC}"
echo ""

# Create bucket if it doesn't exist
echo -e "${BLUE}Checking S3 bucket...${NC}"
if ! aws s3 ls "s3://${BUCKET}" --region ${AWS_REGION} > /dev/null 2>&1; then
    echo -e "${YELLOW}Bucket does not exist. Creating...${NC}"
    aws s3 mb "s3://${BUCKET}" --region ${AWS_REGION}
    echo -e "${GREEN}Bucket created${NC}"
else
    echo -e "${GREEN}Bucket exists${NC}"
fi
echo ""

# Upload knowledge base JSON files
echo -e "${BLUE}Uploading knowledge base files...${NC}"
echo ""

# E/M Codes
echo -e "  ${YELLOW}em_codes/${NC}"
aws s3 sync "${KNOWLEDGE_BASE_PATH}/em_codes/" "${S3_BASE}/knowledge_base/em_codes/" \
    --region ${AWS_REGION} \
    --exclude ".*"
echo -e "  ${GREEN}Done${NC}"

# Investigation protocols
echo -e "  ${YELLOW}investigations/${NC}"
aws s3 sync "${KNOWLEDGE_BASE_PATH}/investigations/" "${S3_BASE}/knowledge_base/investigations/" \
    --region ${AWS_REGION} \
    --exclude ".*"
echo -e "  ${GREEN}Done${NC}"

# CDI Documents (PDFs)
echo -e "  ${YELLOW}cdi_documents/${NC}"
aws s3 sync "${CDI_DOCUMENTS_PATH}/" "${S3_BASE}/cdi_documents/" \
    --region ${AWS_REGION} \
    --exclude ".*" \
    --exclude ".DS_Store"
echo -e "  ${GREEN}Done${NC}"

echo ""

# List uploaded files
echo -e "${BLUE}Uploaded files:${NC}"
aws s3 ls "${S3_BASE}/" --recursive --region ${AWS_REGION} | head -30

TOTAL_SIZE=$(aws s3 ls "${S3_BASE}/" --recursive --summarize --region ${AWS_REGION} | grep "Total Size" | awk '{print $3}')
TOTAL_OBJECTS=$(aws s3 ls "${S3_BASE}/" --recursive --summarize --region ${AWS_REGION} | grep "Total Objects" | awk '{print $3}')

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Upload Complete${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "Total objects: ${YELLOW}${TOTAL_OBJECTS}${NC}"
echo -e "Total size: ${YELLOW}${TOTAL_SIZE} bytes${NC}"
echo ""
echo -e "S3 Location: ${YELLOW}${S3_BASE}${NC}"
echo ""
echo -e "To run migration on ECS:"
echo -e "  ${BLUE}./scripts/run_cdi_migration_ecs.sh --all${NC}"
