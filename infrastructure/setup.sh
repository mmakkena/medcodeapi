#!/bin/bash
set -e

echo "======================================"
echo "Nuvii Backend AWS Deployment Setup"
echo "======================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    echo "   https://aws.amazon.com/cli/"
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed. Please install it first."
    echo "   https://www.terraform.io/downloads"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Get user inputs
echo "Please provide the following information:"
echo ""

read -p "AWS Region (default: us-east-1): " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}

read -p "Project Name (default: nuvii): " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-nuvii}

read -p "Environment (production/staging/development): " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-production}

read -p "Domain name for API (e.g., api.yourdomain.com): " DOMAIN_NAME

echo ""
echo "Database Configuration:"
read -p "Database Name (default: nuvii_db): " DB_NAME
DB_NAME=${DB_NAME:-nuvii_db}

read -p "Database Username (default: nuvii_admin): " DB_USERNAME
DB_USERNAME=${DB_USERNAME:-nuvii_admin}

read -sp "Database Password: " DB_PASSWORD
echo ""

echo ""
echo "Application Secrets:"
read -sp "Application Secret Key (leave empty to generate): " SECRET_KEY
echo ""

if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(openssl rand -base64 32)
    echo "✅ Generated secret key"
fi

read -p "Stripe Secret Key: " STRIPE_SECRET_KEY

echo ""
echo "======================================"
echo "Step 1: Creating SSL Certificate"
echo "======================================"

if [ -n "$DOMAIN_NAME" ]; then
    echo "Requesting SSL certificate for $DOMAIN_NAME..."

    CERT_ARN=$(aws acm request-certificate \
        --domain-name "$DOMAIN_NAME" \
        --validation-method DNS \
        --region "$AWS_REGION" \
        --query 'CertificateArn' \
        --output text)

    echo "✅ Certificate requested: $CERT_ARN"
    echo ""
    echo "⚠️  IMPORTANT: You need to validate this certificate!"
    echo "   1. Go to AWS Certificate Manager console"
    echo "   2. Find the certificate: $CERT_ARN"
    echo "   3. Add the DNS validation records to your domain"
    echo "   4. Wait for validation (this may take a few minutes)"
    echo ""
    read -p "Press Enter once you've validated the certificate..."
else
    echo "⚠️  No domain provided. You'll need to set up SSL manually."
    read -p "Enter your SSL Certificate ARN: " CERT_ARN
fi

echo ""
echo "======================================"
echo "Step 2: Creating Terraform Configuration"
echo "======================================"

cd terraform

cat > terraform.tfvars <<EOF
# AWS Configuration
aws_region   = "$AWS_REGION"
project_name = "$PROJECT_NAME"
environment  = "$ENVIRONMENT"

# Database Configuration
db_name           = "$DB_NAME"
db_username       = "$DB_USERNAME"
db_password       = "$DB_PASSWORD"
db_instance_class = "db.t3.micro"

# Redis Configuration
redis_node_type = "cache.t3.micro"

# ECS Configuration
ecs_service_desired_count = 2
ecs_task_cpu              = "512"
ecs_task_memory           = "1024"

# Secrets
secret_key        = "$SECRET_KEY"
stripe_secret_key = "$STRIPE_SECRET_KEY"

# SSL Certificate ARN
ssl_certificate_arn = "$CERT_ARN"
EOF

echo "✅ terraform.tfvars created"

echo ""
echo "======================================"
echo "Step 3: Initializing Terraform"
echo "======================================"

terraform init

echo ""
echo "======================================"
echo "Step 4: Planning Infrastructure"
echo "======================================"

terraform plan -out=tfplan

echo ""
echo "======================================"
echo "Step 5: Deploying Infrastructure"
echo "======================================"
echo "⚠️  This will create AWS resources and incur costs!"
read -p "Do you want to proceed? (yes/no): " PROCEED

if [ "$PROCEED" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi

terraform apply tfplan

echo ""
echo "======================================"
echo "Step 6: Saving Outputs"
echo "======================================"

terraform output > ../terraform-outputs.txt
ECR_REPO=$(terraform output -raw ecr_repository_url)
ALB_DNS=$(terraform output -raw alb_dns_name)

echo "✅ Outputs saved to terraform-outputs.txt"
echo ""
echo "ECR Repository: $ECR_REPO"
echo "ALB DNS Name: $ALB_DNS"

echo ""
echo "======================================"
echo "Step 7: Building and Pushing Initial Image"
echo "======================================"

cd ../../backend

echo "Logging into ECR..."
aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin "$ECR_REPO"

echo "Building Docker image..."
docker build -t "$ECR_REPO:latest" .

echo "Pushing image to ECR..."
docker push "$ECR_REPO:latest"

echo ""
echo "======================================"
echo "✅ Deployment Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Configure DNS: Point $DOMAIN_NAME to $ALB_DNS (CNAME record)"
echo "2. Add GitHub Secrets for CI/CD:"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo "3. Push code to trigger automatic deployment"
echo ""
echo "API Endpoints:"
echo "  - Health: https://$DOMAIN_NAME/health"
echo "  - Docs: https://$DOMAIN_NAME/docs"
echo ""
echo "Monitoring:"
echo "  - CloudWatch Logs: /ecs/$PROJECT_NAME"
echo "  - ECS Console: https://console.aws.amazon.com/ecs/v2/clusters/$PROJECT_NAME-cluster"
echo ""
echo "For detailed instructions, see DEPLOYMENT.md"
echo ""
