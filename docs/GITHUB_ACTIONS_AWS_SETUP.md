# GitHub Actions AWS Setup for ECS Deployment

This guide explains how to set up AWS IAM credentials for GitHub Actions to deploy to ECS.

## Overview

GitHub Actions needs AWS credentials to:
- Push Docker images to ECR (Elastic Container Registry)
- Update ECS task definitions
- Deploy new versions to ECS services
- Monitor deployment status

## Step-by-Step Setup

### 1. Create IAM User in AWS Console

1. Go to AWS Console → IAM → Users
2. Click "Add users"
3. User name: `github-actions-deployer`
4. Select "Access key - Programmatic access"
5. Click "Next: Permissions"

### 2. Attach Policy

You have two options:

#### Option A: Use Custom Policy (Recommended - Least Privilege)

1. Click "Attach policies directly"
2. Click "Create policy"
3. Choose "JSON" tab
4. Copy and paste the policy from `github-actions-iam-policy.json`
5. Click "Next: Tags" → "Next: Review"
6. Name: `GitHubActionsECSDeployPolicy`
7. Click "Create policy"
8. Go back to user creation and attach this policy

#### Option B: Use AWS Managed Policies (Simpler but broader permissions)

Attach these AWS managed policies:
- `AmazonEC2ContainerRegistryPowerUser`
- `AmazonECS_FullAccess`

**Note:** Option A is more secure as it follows the principle of least privilege.

### 3. Complete User Creation

1. Click "Next: Tags" (optional)
2. Click "Next: Review"
3. Click "Create user"
4. **IMPORTANT:** Save the credentials shown on the success page:
   - Access key ID
   - Secret access key

   ⚠️ You won't be able to see the secret access key again!

### 4. Add Secrets to GitHub Repository

1. Go to your GitHub repository
2. Click "Settings" → "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Add two secrets:

   **Secret 1:**
   - Name: `AWS_ACCESS_KEY_ID`
   - Value: [Your access key ID from step 3]

   **Secret 2:**
   - Name: `AWS_SECRET_ACCESS_KEY`
   - Value: [Your secret access key from step 3]

### 5. Verify Setup

1. Push a commit to the `main` branch that modifies backend code
2. Go to GitHub → Actions tab
3. Watch the workflow run
4. The "Configure AWS credentials" step should succeed

## Permission Breakdown

### ECR Permissions
- `ecr:GetAuthorizationToken` - Login to ECR
- `ecr:BatchCheckLayerAvailability` - Check if image layers exist
- `ecr:GetDownloadUrlForLayer` - Download existing layers
- `ecr:BatchGetImage` - Pull images
- `ecr:PutImage` - Push images
- `ecr:InitiateLayerUpload` - Start upload
- `ecr:UploadLayerPart` - Upload image layers
- `ecr:CompleteLayerUpload` - Finish upload

### ECS Permissions
- `ecs:DescribeClusters` - Verify cluster exists
- `ecs:DescribeServices` - Check service status
- `ecs:DescribeTaskDefinition` - Get current task definition
- `ecs:DescribeTasks` - Check task status
- `ecs:ListTasks` - List running tasks
- `ecs:RegisterTaskDefinition` - Create new task definition version
- `ecs:UpdateService` - Deploy new task definition
- `ecs:DeregisterTaskDefinition` - Clean up old versions

### IAM Permissions
- `iam:PassRole` - Allow ECS to assume task execution role
  - Required for ECS to pull images from ECR
  - Required for ECS to write logs to CloudWatch

### CloudWatch Logs Permissions
- `logs:CreateLogGroup` - Create log group if needed
- `logs:CreateLogStream` - Create log streams
- `logs:PutLogEvents` - Write application logs
- `logs:DescribeLogStreams` - Query logs for debugging

## Security Best Practices

1. **Rotate credentials regularly** (every 90 days)
2. **Use separate IAM users** for different environments (staging/production)
3. **Enable MFA** on the root AWS account
4. **Monitor CloudTrail logs** for unexpected API calls
5. **Restrict by IP** if possible (add IP condition to policy)
6. **Consider OIDC instead** - GitHub now supports AWS OIDC for temporary credentials

## Troubleshooting

### "Credentials could not be loaded"
- Check that secrets are named exactly: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- Verify secrets are set in the repository (not organization-level)
- Check that the workflow uses `${{ secrets.AWS_ACCESS_KEY_ID }}`

### "Access Denied" errors
- Verify the IAM user has the required policy attached
- Check the policy has the correct permissions for your specific resources
- Ensure the region matches (`us-east-2`)

### "Cannot assume role"
- Verify the `iam:PassRole` permission is configured
- Check that the ECS task execution role exists
- Ensure the condition in the PassRole statement is correct

## Advanced: OIDC Setup (Recommended for Production)

For better security, consider using GitHub OIDC instead of static credentials:

1. Create an OIDC identity provider in AWS IAM
2. Create an IAM role with trust policy for GitHub
3. Update workflow to use `aws-actions/configure-aws-credentials@v4` with `role-to-assume`

See: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services

## Resources

- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [GitHub Actions Security](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [ECS Task Execution Role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html)
