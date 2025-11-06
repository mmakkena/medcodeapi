# Nuvii Backend Deployment Guide

This guide covers deploying the Nuvii backend to AWS using Terraform and GitHub Actions.

## Architecture Overview

The deployment uses:
- **AWS ECS Fargate**: Serverless container orchestration
- **AWS ECR**: Docker image registry
- **AWS RDS PostgreSQL**: Managed database
- **AWS ElastiCache Redis**: Managed cache
- **Application Load Balancer**: Traffic distribution and SSL termination
- **AWS Secrets Manager**: Secure credential storage
- **CloudWatch**: Logging and monitoring

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **Terraform** (v1.0+) installed
4. **GitHub repository** with the code
5. **Domain name** (optional but recommended for SSL)

## Step 1: AWS Initial Setup

### 1.1 Create an SSL Certificate

```bash
# Request a certificate in AWS Certificate Manager (ACM)
aws acm request-certificate \
  --domain-name api.yourdomain.com \
  --validation-method DNS \
  --region us-east-1

# Note the certificate ARN for terraform.tfvars
```

Validate the certificate by adding the DNS records shown in ACM.

### 1.2 Create S3 Bucket for Terraform State (Optional)

```bash
aws s3api create-bucket \
  --bucket nuvii-terraform-state \
  --region us-east-1

aws s3api put-bucket-versioning \
  --bucket nuvii-terraform-state \
  --versioning-configuration Status=Enabled
```

## Step 2: Configure Terraform

### 2.1 Navigate to Infrastructure Directory

```bash
cd infrastructure/terraform
```

### 2.2 Create terraform.tfvars

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
# AWS Configuration
aws_region   = "us-east-1"
project_name = "nuvii"
environment  = "production"

# Database Configuration
db_name           = "nuvii_db"
db_username       = "nuvii_admin"
db_password       = "YOUR_STRONG_PASSWORD_HERE"
db_instance_class = "db.t3.micro"

# Redis Configuration
redis_node_type = "cache.t3.micro"

# ECS Configuration
ecs_service_desired_count = 2
ecs_task_cpu              = "512"
ecs_task_memory           = "1024"

# Secrets
secret_key        = "YOUR_RANDOM_SECRET_KEY_HERE"
stripe_secret_key = "sk_live_YOUR_STRIPE_KEY"

# SSL Certificate ARN (from Step 1.1)
ssl_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/xxxxx"
```

### 2.3 Initialize and Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply the infrastructure
terraform apply
```

This will create:
- VPC with public and private subnets
- ECS cluster and service
- RDS PostgreSQL database
- ElastiCache Redis cluster
- Application Load Balancer
- Security groups
- ECR repository
- CloudWatch logs

**Save the outputs:**

```bash
terraform output > ../terraform-outputs.txt
```

## Step 3: Configure GitHub Secrets

Navigate to your GitHub repository → Settings → Secrets and variables → Actions

Add the following secrets:

| Secret Name | Description | How to Get |
|------------|-------------|------------|
| `AWS_ACCESS_KEY_ID` | AWS access key | IAM user with deployment permissions |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | IAM user credentials |

### 3.1 Create IAM User for GitHub Actions

```bash
# Create IAM policy
cat > github-actions-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecs:DescribeTaskDefinition",
        "ecs:RegisterTaskDefinition",
        "ecs:UpdateService",
        "ecs:DescribeServices",
        "iam:PassRole"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Create IAM user
aws iam create-user --user-name github-actions-deployer

# Attach policy
aws iam put-user-policy \
  --user-name github-actions-deployer \
  --policy-name GithubActionsDeployPolicy \
  --policy-document file://github-actions-policy.json

# Create access keys
aws iam create-access-key --user-name github-actions-deployer
```

## Step 4: Initial Manual Deployment

Before GitHub Actions can deploy, we need to push the first image:

```bash
# Navigate to backend directory
cd ../../backend

# Get ECR login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <ECR_REGISTRY_URL>

# Build and push initial image
ECR_REGISTRY=$(terraform -chdir=../infrastructure/terraform output -raw ecr_repository_url)

docker build -t $ECR_REGISTRY:latest .
docker push $ECR_REGISTRY:latest
```

## Step 5: Configure DNS

Point your domain to the ALB:

```bash
# Get ALB DNS name
terraform -chdir=infrastructure/terraform output alb_dns_name
```

Create a CNAME record:
- **Name**: `api.yourdomain.com`
- **Type**: CNAME
- **Value**: `<ALB_DNS_NAME>` (from terraform output)

## Step 6: Trigger Deployment

Now push your code to trigger automatic deployment:

```bash
git add .
git commit -m "Initial deployment setup"
git push origin main
```

GitHub Actions will:
1. Run tests
2. Build Docker image
3. Push to ECR
4. Deploy to ECS

## Step 7: Verify Deployment

```bash
# Check the endpoint
curl https://api.yourdomain.com/health

# Expected response:
# {
#   "status": "healthy",
#   "database": "connected",
#   "redis": "connected"
# }
```

## Monitoring and Logs

### CloudWatch Logs

```bash
# View logs
aws logs tail /ecs/nuvii --follow --region us-east-1
```

### ECS Service Status

```bash
# Check service
aws ecs describe-services \
  --cluster nuvii-cluster \
  --services nuvii-backend-service \
  --region us-east-1
```

## Scaling

### Manual Scaling

```bash
# Update desired count in terraform.tfvars
ecs_service_desired_count = 4

# Apply changes
terraform apply
```

### Auto-scaling (Optional)

Add to `ecs.tf`:

```hcl
resource "aws_appautoscaling_target" "ecs" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.backend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_cpu" {
  name               = "${var.project_name}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
```

## Database Migrations

Migrations run automatically on container startup via the Dockerfile CMD:

```dockerfile
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

### Manual Migration

```bash
# SSH into a running container
aws ecs execute-command \
  --cluster nuvii-cluster \
  --task <TASK_ID> \
  --container nuvii-backend \
  --interactive \
  --command "/bin/sh"

# Run migrations
alembic upgrade head
```

## Rollback

```bash
# Revert to previous task definition
aws ecs update-service \
  --cluster nuvii-cluster \
  --service nuvii-backend-service \
  --task-definition nuvii-backend-task:<PREVIOUS_REVISION>
```

## Cost Optimization

### Development Environment

For development/staging, use smaller instances:

```hcl
# terraform.tfvars
db_instance_class = "db.t3.micro"       # ~$13/month
redis_node_type   = "cache.t3.micro"    # ~$12/month
ecs_task_cpu      = "256"
ecs_task_memory   = "512"
ecs_service_desired_count = 1
```

### Production Environment

```hcl
db_instance_class = "db.t3.small"       # ~$26/month
redis_node_type   = "cache.t3.small"    # ~$24/month
ecs_task_cpu      = "512"
ecs_task_memory   = "1024"
ecs_service_desired_count = 2
```

## Troubleshooting

### Container Won't Start

```bash
# Check ECS events
aws ecs describe-services \
  --cluster nuvii-cluster \
  --services nuvii-backend-service \
  --query 'services[0].events[0:5]'

# Check CloudWatch logs
aws logs tail /ecs/nuvii --since 30m
```

### Database Connection Issues

```bash
# Verify security group rules
aws ec2 describe-security-groups \
  --group-ids <RDS_SECURITY_GROUP_ID>

# Test from ECS task
aws ecs execute-command \
  --cluster nuvii-cluster \
  --task <TASK_ID> \
  --container nuvii-backend \
  --interactive \
  --command "psql -h <RDS_ENDPOINT> -U nuvii_admin -d nuvii_db"
```

### High Costs

```bash
# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=nuvii-backend-service \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average
```

## Cleanup

To destroy all infrastructure:

```bash
cd infrastructure/terraform

# Disable deletion protection first
terraform apply -var="environment=development"

# Destroy everything
terraform destroy
```

**Warning**: This will delete all data including databases!

## Security Best Practices

1. **Enable encryption at rest** for RDS and ECS volumes
2. **Use AWS Secrets Manager** for all sensitive data
3. **Enable VPC Flow Logs** for network monitoring
4. **Set up CloudTrail** for audit logging
5. **Use AWS WAF** on the ALB for additional security
6. **Enable GuardDuty** for threat detection
7. **Implement backup strategy** for RDS (automated backups enabled by default)
8. **Review IAM policies** regularly
9. **Enable MFA** on AWS root and IAM accounts
10. **Use separate AWS accounts** for dev/staging/prod

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourorg/nuvii/issues
- Documentation: https://docs.nuvii.ai
- Email: support@nuvii.ai
