# Infrastructure

This directory contains infrastructure-as-code for deploying the Nuvii backend to AWS.

## Quick Start

### Automated Setup

Run the interactive setup script:

```bash
cd infrastructure
./setup.sh
```

This will guide you through:
1. SSL certificate creation
2. Terraform configuration
3. Infrastructure deployment
4. Initial Docker image push

### Manual Setup

See [DEPLOYMENT.md](../DEPLOYMENT.md) for detailed manual setup instructions.

## Directory Structure

```
infrastructure/
├── terraform/
│   ├── main.tf              # VPC and networking
│   ├── ecs.tf               # ECS cluster and services
│   ├── rds.tf               # PostgreSQL and Redis
│   ├── alb.tf               # Load balancer and security groups
│   ├── variables.tf         # Input variables
│   ├── outputs.tf           # Output values
│   └── terraform.tfvars.example  # Example configuration
├── setup.sh                 # Automated setup script
└── README.md               # This file
```

## What Gets Created

The Terraform configuration creates:

- **Networking**: VPC, subnets, internet gateway, NAT gateway, route tables
- **Compute**: ECS Fargate cluster and service
- **Database**: RDS PostgreSQL instance
- **Cache**: ElastiCache Redis cluster
- **Load Balancer**: Application Load Balancer with SSL
- **Security**: Security groups, IAM roles, Secrets Manager
- **Monitoring**: CloudWatch log groups
- **Container Registry**: ECR repository

## Cost Estimate

### Minimal Configuration (Development)

- ECS Fargate (2 tasks, 0.25 vCPU, 0.5 GB): ~$15/month
- RDS db.t3.micro: ~$13/month
- ElastiCache cache.t3.micro: ~$12/month
- ALB: ~$20/month
- NAT Gateway: ~$32/month
- Data transfer: ~$10/month

**Total: ~$102/month**

### Recommended Configuration (Production)

- ECS Fargate (2 tasks, 0.5 vCPU, 1 GB): ~$30/month
- RDS db.t3.small: ~$26/month
- ElastiCache cache.t3.small: ~$24/month
- ALB: ~$20/month
- NAT Gateway: ~$32/month
- Data transfer: ~$20/month

**Total: ~$152/month**

## Prerequisites

- AWS Account
- AWS CLI configured
- Terraform 1.0+
- Docker
- Domain name (optional but recommended)

## Configuration

### Environment Variables

For automated deployment, you can set:

```bash
export AWS_REGION=us-east-1
export TF_VAR_db_password=your_password
export TF_VAR_secret_key=your_secret
```

### terraform.tfvars

Copy and edit the example:

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

## Deployment

### Using Terraform Directly

```bash
cd terraform

# Initialize
terraform init

# Plan
terraform plan

# Apply
terraform apply

# Get outputs
terraform output
```

### Using the Setup Script

```bash
./setup.sh
```

## Updates

To update the infrastructure:

```bash
cd terraform

# Make changes to .tf files

# Review changes
terraform plan

# Apply changes
terraform apply
```

## Scaling

### Vertical Scaling (Instance Size)

Edit `terraform.tfvars`:

```hcl
db_instance_class = "db.t3.medium"
redis_node_type   = "cache.t3.medium"
ecs_task_cpu      = "1024"
ecs_task_memory   = "2048"
```

### Horizontal Scaling (Task Count)

Edit `terraform.tfvars`:

```hcl
ecs_service_desired_count = 4
```

Then apply:

```bash
terraform apply
```

## Monitoring

### CloudWatch Logs

```bash
aws logs tail /ecs/nuvii --follow
```

### ECS Service Status

```bash
aws ecs describe-services \
  --cluster nuvii-cluster \
  --services nuvii-backend-service
```

### RDS Metrics

Access via AWS Console → RDS → Monitoring

## Backup and Restore

### Database Backups

Automated backups are configured with 7-day retention.

Manual snapshot:

```bash
aws rds create-db-snapshot \
  --db-instance-identifier nuvii-postgres \
  --db-snapshot-identifier nuvii-backup-$(date +%Y%m%d)
```

### Restore

```bash
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier nuvii-postgres-restored \
  --db-snapshot-identifier nuvii-backup-20240101
```

## Troubleshooting

### Terraform State Issues

```bash
# List resources
terraform state list

# Show resource
terraform state show aws_ecs_service.backend

# Import existing resource
terraform import aws_ecs_service.backend nuvii-cluster/nuvii-backend-service
```

### Failed Deployments

```bash
# Check ECS events
aws ecs describe-services \
  --cluster nuvii-cluster \
  --services nuvii-backend-service \
  --query 'services[0].events[0:10]'
```

### Container Issues

```bash
# Execute into container
aws ecs execute-command \
  --cluster nuvii-cluster \
  --task TASK_ID \
  --container nuvii-backend \
  --interactive \
  --command "/bin/sh"
```

## Security

### Best Practices

1. ✅ Encryption at rest enabled
2. ✅ Encryption in transit (SSL/TLS)
3. ✅ Private subnets for databases
4. ✅ Security groups with minimal access
5. ✅ Secrets in AWS Secrets Manager
6. ✅ IAM roles with least privilege

### Additional Security (Recommended)

- Enable AWS WAF on ALB
- Enable GuardDuty
- Enable CloudTrail
- Enable VPC Flow Logs
- Use AWS Config for compliance

## Cleanup

To destroy all infrastructure:

```bash
cd terraform
terraform destroy
```

⚠️ **Warning**: This will permanently delete all resources and data!

## Support

For issues:
- Check [DEPLOYMENT.md](../DEPLOYMENT.md)
- GitHub Issues: https://github.com/yourorg/nuvii/issues
- Email: support@nuvii.ai
