# AWS Parameter Store Migration Guide

## Overview

This guide explains how to migrate from environment variable-based secrets to AWS Systems Manager Parameter Store for the Nuvii backend application.

## Why Parameter Store?

- **Centralized Secrets Management**: All secrets stored in one secure location
- **Encryption at Rest**: Secrets encrypted using AWS KMS
- **Access Control**: Fine-grained IAM permissions for secret access
- **Audit Trail**: CloudTrail logs all parameter access
- **Version History**: Automatic versioning of parameter changes
- **No Code Changes Required**: Application reads from Parameter Store transparently

## Region Configuration

All Parameter Store parameters are configured for the **us-east-2** (Ohio) region.

## Parameter Naming Convention

Parameters follow this structure:
```
/{APP_NAME}/{ENVIRONMENT}/{PARAMETER_NAME}
```

Example:
```
/nuvii/production/SECRET_KEY
/nuvii/production/STRIPE_SECRET_KEY
/nuvii/production/DATABASE_PASSWORD
```

## Setup Instructions

### 1. Prerequisites

- AWS CLI installed and configured
- AWS credentials with SSM permissions
- Environment variables set locally for migration

Required AWS IAM permissions:
- `ssm:PutParameter`
- `ssm:GetParameter`
- `ssm:GetParameters`
- `ssm:GetParametersByPath`
- `kms:Decrypt` (for SecureString parameters)

### 2. Upload Secrets to Parameter Store

Use the provided script to upload your secrets:

```bash
cd backend/scripts
chmod +x upload-secrets-to-parameter-store.sh
./upload-secrets-to-parameter-store.sh
```

The script will:
1. Prompt for each required secret
2. Create parameters with SecureString encryption
3. Set proper tags (Environment, ManagedBy, Application)
4. Handle overwrites if parameters already exist

#### Manual Upload

If you prefer to upload manually:

```bash
# Set your configuration
export AWS_REGION=us-east-2
export ENVIRONMENT=production
export APP_NAME=nuvii

# Upload secrets (replace YOUR_VALUE with actual secret)
aws ssm put-parameter \
  --name "/${APP_NAME}/${ENVIRONMENT}/SECRET_KEY" \
  --value "YOUR_SECRET_KEY" \
  --type "SecureString" \
  --region $AWS_REGION \
  --tags Key=Environment,Value=$ENVIRONMENT Key=ManagedBy,Value=Terraform

aws ssm put-parameter \
  --name "/${APP_NAME}/${ENVIRONMENT}/STRIPE_SECRET_KEY" \
  --value "YOUR_STRIPE_SECRET_KEY" \
  --type "SecureString" \
  --region $AWS_REGION \
  --tags Key=Environment,Value=$ENVIRONMENT Key=ManagedBy,Value=Terraform

aws ssm put-parameter \
  --name "/${APP_NAME}/${ENVIRONMENT}/DATABASE_PASSWORD" \
  --value "YOUR_DB_PASSWORD" \
  --type "SecureString" \
  --region $AWS_REGION \
  --tags Key=Environment,Value=$ENVIRONMENT Key=ManagedBy,Value=Terraform
```

### 3. Verify Parameter Upload

List all parameters:
```bash
aws ssm get-parameters-by-path \
  --path "/nuvii/production" \
  --with-decryption \
  --region us-east-2
```

Get specific parameter:
```bash
aws ssm get-parameter \
  --name "/nuvii/production/SECRET_KEY" \
  --with-decryption \
  --region us-east-2
```

### 4. Update Application Configuration

The application configuration has been updated to automatically read from Parameter Store.

#### Backend Configuration (`backend/app/config.py`)

```python
class Settings(BaseSettings):
    # Enable Parameter Store (default: True for non-development)
    USE_PARAMETER_STORE: bool = True

    # AWS Configuration
    AWS_REGION: str = "us-east-2"
    ENVIRONMENT: str = "production"
    APP_NAME: str = "nuvii"
```

#### Parameter Store Integration (`backend/app/parameter_store.py`)

Features:
- **Caching**: LRU cache (128 parameters) for performance
- **Fallback**: Falls back to environment variables if Parameter Store unavailable
- **Error Handling**: Graceful degradation if AWS credentials not configured
- **Automatic Decryption**: SecureString parameters automatically decrypted

Example usage:
```python
from app.parameter_store import get_parameter_store

# Get Parameter Store instance
ps = get_parameter_store()

# Get single parameter
secret_key = ps.get_parameter("SECRET_KEY")

# Get all parameters
all_params = ps.get_all_parameters()
```

### 5. Deploy Infrastructure Changes

The Terraform infrastructure has been updated with IAM permissions for Parameter Store access.

#### IAM Permissions Added

The ECS task role now has these permissions:

```hcl
# SSM Parameter Store read permissions
- ssm:GetParameter
- ssm:GetParameters
- ssm:GetParametersByPath

# KMS decryption for SecureString parameters
- kms:Decrypt (via SSM service)
```

Resource scope: `/nuvii/production/*`

#### Deploy Changes

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Review changes
terraform plan

# Apply changes
terraform apply
```

### 6. GitHub Actions Configuration

The GitHub Actions workflows already pass secrets via environment variables. No changes required.

However, you can optionally update workflows to use Parameter Store directly by removing secret environment variables and letting the application fetch them at runtime.

## Migration Checklist

- [ ] Install AWS CLI and configure credentials
- [ ] Run upload script: `./backend/scripts/upload-secrets-to-parameter-store.sh`
- [ ] Verify parameters in AWS Console or via CLI
- [ ] Deploy updated Terraform infrastructure (IAM permissions)
- [ ] Test application locally with `USE_PARAMETER_STORE=true`
- [ ] Deploy updated application to ECS
- [ ] Monitor CloudWatch logs for Parameter Store access
- [ ] Remove deprecated environment variables from deployment configs (optional)

## Environment-Specific Configuration

### Development Environment

By default, Parameter Store is **disabled** in development:

```bash
# .env.development
USE_PARAMETER_STORE=false
ENVIRONMENT=development

# Use local environment variables
SECRET_KEY=dev-secret-key
STRIPE_SECRET_KEY=sk_test_...
```

### Production Environment

Parameter Store is **enabled** by default:

```bash
# ECS Task Definition (no secrets in environment variables)
USE_PARAMETER_STORE=true
ENVIRONMENT=production
AWS_REGION=us-east-2
APP_NAME=nuvii
```

## Troubleshooting

### Issue: Application can't connect to Parameter Store

**Symptoms**: Errors like `ClientError: AccessDeniedException`

**Solution**:
1. Verify IAM permissions are deployed: `terraform apply`
2. Check ECS task role has Parameter Store policy attached
3. Verify region is set correctly: `AWS_REGION=us-east-2`

### Issue: Parameter not found

**Symptoms**: `ParameterNotFound` exception

**Solution**:
1. Verify parameter exists:
   ```bash
   aws ssm get-parameter --name "/nuvii/production/SECRET_KEY" --region us-east-2
   ```
2. Check parameter path matches naming convention
3. Ensure `ENVIRONMENT` and `APP_NAME` are set correctly

### Issue: Application falls back to environment variables

**Symptoms**: Warning logs: "Falling back to environment variable"

**Solution**:
1. This is expected behavior when Parameter Store is unavailable
2. Verify `USE_PARAMETER_STORE=true` is set
3. Check AWS credentials are available in ECS environment
4. Review CloudWatch logs for specific errors

### Issue: Slow application startup

**Symptoms**: Increased startup time after Parameter Store migration

**Solution**:
1. This is expected - initial Parameter Store fetch adds 100-500ms
2. Caching reduces subsequent lookups to <1ms
3. Consider pre-warming cache by calling `get_all_parameters()` at startup

## Security Best Practices

1. **Use SecureString**: Always use `SecureString` type for sensitive parameters
2. **Least Privilege**: Grant only necessary IAM permissions
3. **Rotate Secrets**: Regularly rotate sensitive credentials
4. **Enable CloudTrail**: Monitor Parameter Store access in CloudTrail
5. **Use KMS**: Consider using customer-managed KMS keys for additional control
6. **Tag Parameters**: Use consistent tagging for cost tracking and access control

## Cost Considerations

AWS Systems Manager Parameter Store pricing (us-east-2):

- **Standard Parameters**: Free (up to 10,000 parameters)
- **Advanced Parameters**: $0.05 per parameter per month
- **API Calls**:
  - Standard throughput: Free (up to 40 TPS)
  - Higher throughput: $0.05 per 10,000 requests

For Nuvii's use case (< 20 parameters, < 1,000 requests/day), Parameter Store is effectively **free**.

## Monitoring

### CloudWatch Metrics

Monitor these metrics in CloudWatch:

- `SSM.GetParameter.Count` - Number of parameter retrievals
- `SSM.GetParameter.Errors` - Failed parameter retrievals
- Application logs: "Parameter Store" entries

### CloudTrail Logs

Review Parameter Store access in CloudTrail:

```bash
# Filter CloudTrail events for Parameter Store
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=GetParameter \
  --region us-east-2
```

## Rollback Procedure

If you need to rollback to environment variables:

1. Set `USE_PARAMETER_STORE=false` in application config
2. Redeploy application with environment variables in ECS task definition
3. No infrastructure changes required (IAM permissions are harmless)

## Additional Resources

- [AWS Parameter Store Documentation](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
- [AWS Parameter Store Best Practices](https://docs.aws.amazon.com/systems-manager/latest/userguide/parameter-store-best-practices.html)
- [Terraform AWS SSM Parameter](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssm_parameter)

## Support

For issues or questions:
1. Check CloudWatch logs: `/ecs/nuvii`
2. Review this documentation
3. Contact DevOps team

---

**Last Updated**: 2025-11-06
**AWS Region**: us-east-2
**Application**: Nuvii Backend API
**Managed By**: Terraform
