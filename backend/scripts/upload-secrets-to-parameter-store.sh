#!/bin/bash

set -e

# Upload Secrets to AWS Systems Manager Parameter Store
# This script uploads application secrets from .env file to Parameter Store

# Configuration
AWS_REGION="${AWS_REGION:-us-east-2}"
ENVIRONMENT="${ENVIRONMENT:-production}"
APP_NAME="${APP_NAME:-nuvii}"
PARAMETER_PREFIX="/${APP_NAME}/${ENVIRONMENT}"

echo "======================================"
echo "Upload Secrets to Parameter Store"
echo "======================================"
echo ""
echo "Region: $AWS_REGION"
echo "Environment: $ENVIRONMENT"
echo "Parameter Prefix: $PARAMETER_PREFIX"
echo ""

# Check if AWS CLI is configured
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed"
    exit 1
fi

# Verify AWS credentials
echo "Verifying AWS credentials..."
aws sts get-caller-identity > /dev/null || {
    echo "❌ AWS credentials not configured"
    exit 1
}
echo "✅ AWS credentials verified"
echo ""

# Function to create/update parameter
create_parameter() {
    local param_name=$1
    local param_value=$2
    local param_type=${3:-SecureString}
    local description=${4:-""}

    echo "Creating parameter: $param_name"

    aws ssm put-parameter \
        --name "$param_name" \
        --value "$param_value" \
        --type "$param_type" \
        --description "$description" \
        --region "$AWS_REGION" \
        --overwrite \
        --tier Standard \
        --no-cli-pager || {
        echo "❌ Failed to create parameter: $param_name"
        return 1
    }

    echo "✅ Created: $param_name"
}

# Prompt for secrets
echo "Please provide the following secrets:"
echo ""

read -sp "SECRET_KEY (JWT secret): " SECRET_KEY
echo ""

read -sp "JWT_SECRET_KEY: " JWT_SECRET_KEY
echo ""

read -p "DATABASE_URL (e.g., postgresql://user:pass@host:5432/db): " DATABASE_URL

read -p "REDIS_URL (e.g., redis://host:6379/0): " REDIS_URL

read -sp "STRIPE_SECRET_KEY: " STRIPE_SECRET_KEY
echo ""

read -sp "STRIPE_WEBHOOK_SECRET: " STRIPE_WEBHOOK_SECRET
echo ""

read -p "STRIPE_PUBLISHABLE_KEY: " STRIPE_PUBLISHABLE_KEY

read -p "CORS_ORIGINS (comma-separated): " CORS_ORIGINS

echo ""
echo "======================================"
echo "Uploading to Parameter Store..."
echo "======================================"
echo ""

# Upload secrets (SecureString - encrypted at rest)
create_parameter "${PARAMETER_PREFIX}/SECRET_KEY" "$SECRET_KEY" "SecureString" "Application secret key for JWT"
create_parameter "${PARAMETER_PREFIX}/JWT_SECRET_KEY" "$JWT_SECRET_KEY" "SecureString" "JWT signing key"
create_parameter "${PARAMETER_PREFIX}/DATABASE_URL" "$DATABASE_URL" "SecureString" "PostgreSQL database connection string"
create_parameter "${PARAMETER_PREFIX}/REDIS_URL" "$REDIS_URL" "SecureString" "Redis connection string"
create_parameter "${PARAMETER_PREFIX}/STRIPE_SECRET_KEY" "$STRIPE_SECRET_KEY" "SecureString" "Stripe API secret key"
create_parameter "${PARAMETER_PREFIX}/STRIPE_WEBHOOK_SECRET" "$STRIPE_WEBHOOK_SECRET" "SecureString" "Stripe webhook secret"
create_parameter "${PARAMETER_PREFIX}/STRIPE_PUBLISHABLE_KEY" "$STRIPE_PUBLISHABLE_KEY" "String" "Stripe publishable key"

# Upload non-sensitive configuration (String - not encrypted)
create_parameter "${PARAMETER_PREFIX}/CORS_ORIGINS" "$CORS_ORIGINS" "String" "Allowed CORS origins"
create_parameter "${PARAMETER_PREFIX}/APP_NAME" "${APP_NAME}" "String" "Application name"
create_parameter "${PARAMETER_PREFIX}/ENVIRONMENT" "${ENVIRONMENT}" "String" "Environment name"
create_parameter "${PARAMETER_PREFIX}/JWT_ALGORITHM" "HS256" "String" "JWT algorithm"
create_parameter "${PARAMETER_PREFIX}/ACCESS_TOKEN_EXPIRE_MINUTES" "30" "String" "JWT token expiration in minutes"
create_parameter "${PARAMETER_PREFIX}/RATE_LIMIT_PER_MINUTE" "60" "String" "Rate limit per minute"
create_parameter "${PARAMETER_PREFIX}/RATE_LIMIT_PER_DAY" "10000" "String" "Rate limit per day"
create_parameter "${PARAMETER_PREFIX}/API_KEY_PREFIX" "mk_" "String" "API key prefix"

echo ""
echo "======================================"
echo "✅ All parameters uploaded successfully!"
echo "======================================"
echo ""
echo "Parameters created at: $PARAMETER_PREFIX/*"
echo ""
echo "To view parameters:"
echo "  aws ssm get-parameters-by-path --path $PARAMETER_PREFIX --region $AWS_REGION"
echo ""
echo "To delete all parameters (if needed):"
echo "  aws ssm delete-parameters --names \$(aws ssm get-parameters-by-path --path $PARAMETER_PREFIX --query 'Parameters[].Name' --output text --region $AWS_REGION) --region $AWS_REGION"
echo ""
