# CI/CD Quick Reference Guide

This is a quick reference for the Nuvii backend CI/CD pipelines.

## 🚀 Quick Start

### First-Time Setup

1. **Set GitHub Secrets** (Settings → Secrets → Actions)
   ```
   AWS_ACCESS_KEY_ID
   AWS_SECRET_ACCESS_KEY
   DB_PASSWORD
   APP_SECRET_KEY
   STRIPE_SECRET_KEY
   SSL_CERTIFICATE_ARN
   ```

2. **Deploy Infrastructure**
   - Go to Actions → "Infrastructure Deployment"
   - Run workflow → Select "apply"
   - Wait ~15 minutes

3. **Deploy Backend**
   - Push backend code to main branch
   - Automatic deployment begins
   - Check status in Actions tab

## 📊 Two Separate Pipelines

### Pipeline 1: Infrastructure (Terraform)
- **File**: `.github/workflows/infrastructure-deploy.yml`
- **Manages**: VPC, ECS, RDS, Redis, Load Balancer
- **Runs when**: Changes to `infrastructure/terraform/**`
- **Manual control**: Yes (plan/apply/destroy)

### Pipeline 2: Backend Application
- **File**: `.github/workflows/backend-deploy.yml`
- **Manages**: Docker image, ECS deployment
- **Runs when**: Changes to `backend/**`
- **Manual control**: Yes (workflow_dispatch)

## 🔄 Common Workflows

### Deploy New Backend Feature
```bash
# 1. Create feature branch
git checkout -b feature/new-endpoint

# 2. Make changes to backend
vim backend/app/api/v1/new_endpoint.py

# 3. Commit and push
git add backend/
git commit -m "feat: add new endpoint"
git push origin feature/new-endpoint

# 4. Create PR
# Tests and linting run automatically

# 5. After PR approval and merge
# Automatic deployment to production
```

### Scale Infrastructure
```bash
# 1. Update Terraform variables
vim infrastructure/terraform/terraform.tfvars
# Change: ecs_service_desired_count = 4

# 2. Commit and push
git add infrastructure/
git commit -m "feat: scale to 4 tasks"
git push origin main

# 3. Review and approve in GitHub Actions
# Infrastructure updates automatically
```

### Manual Deployment

**Infrastructure:**
1. Go to GitHub → Actions
2. Select "Infrastructure Deployment"
3. Click "Run workflow"
4. Choose action: `plan` | `apply` | `destroy`

**Backend:**
1. Go to GitHub → Actions
2. Select "Backend Application Deployment"
3. Click "Run workflow"

## 📋 Workflow Statuses

### ✅ Success Indicators

**Infrastructure:**
- All Terraform validations pass
- Plan shows expected changes
- Apply completes without errors
- Outputs are generated

**Backend:**
- Tests pass (pytest)
- Linting passes (Black, Flake8)
- Docker build succeeds
- ECS deployment reaches steady state
- Health checks pass

### ❌ Failure Indicators

**Infrastructure:**
- Terraform validation errors
- Resource quota exceeded
- Permission denied
- Resource conflicts

**Backend:**
- Test failures
- Linting errors
- Docker build fails
- ECS deployment timeout
- Health check failures

## 🔍 Debugging

### Check Infrastructure Status
```bash
# Verify ECS cluster
aws ecs describe-clusters --clusters nuvii-cluster

# Check RDS database
aws rds describe-db-instances --region us-east-1

# View Terraform state
cd infrastructure/terraform
terraform state list
```

### Check Backend Deployment
```bash
# View ECS service status
aws ecs describe-services \
  --cluster nuvii-cluster \
  --services nuvii-backend-service

# Check container logs
aws logs tail /ecs/nuvii --follow

# List running tasks
aws ecs list-tasks \
  --cluster nuvii-cluster \
  --service-name nuvii-backend-service
```

### Test Endpoints
```bash
# Health check
curl https://api.nuvii.ai/health

# API docs
curl https://api.nuvii.ai/docs

# Specific endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.nuvii.ai/api/v1/icd10/search?query=diabetes
```

## 🔄 Rollback

### Rollback Backend (Fast)
```bash
# Option 1: Revert commit
git revert <commit-sha>
git push origin main

# Option 2: Use previous ECS task definition
aws ecs update-service \
  --cluster nuvii-cluster \
  --service nuvii-backend-service \
  --task-definition nuvii-backend-task:<previous-revision>
```

### Rollback Infrastructure
```bash
# Revert Terraform changes
git revert <infrastructure-commit-sha>
git push origin main

# Then run workflow: Actions → Infrastructure → apply
```

## 🎯 Best Practices

### ✅ DO
- Create PRs for all changes
- Wait for CI checks before merging
- Review Terraform plans carefully
- Test locally before pushing
- Use feature branches
- Write descriptive commit messages
- Monitor deployments in CloudWatch

### ❌ DON'T
- Push directly to main
- Skip tests or linting
- Ignore Terraform plan warnings
- Deploy without reviewing changes
- Commit secrets or credentials
- Force push to main branch
- Ignore deployment errors

## 📊 Monitoring

### GitHub Actions Dashboard
- View all workflow runs
- Check success/failure rates
- Download logs for debugging

### AWS CloudWatch
```bash
# Real-time logs
aws logs tail /ecs/nuvii --follow

# Filter errors
aws logs filter-pattern /ecs/nuvii --filter-pattern "ERROR"

# View metrics
# Go to AWS Console → CloudWatch → Metrics → ECS
```

### ECS Service Metrics
- CPU utilization
- Memory utilization
- Task count
- Health check status

## 🔒 Security

### GitHub Secrets Required
| Secret | Purpose | Example |
|--------|---------|---------|
| `AWS_ACCESS_KEY_ID` | AWS authentication | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS authentication | `wJal...` |
| `DB_PASSWORD` | RDS password | `SecurePass123!` |
| `APP_SECRET_KEY` | JWT signing | Random 32-char string |
| `STRIPE_SECRET_KEY` | Stripe API | `sk_live_...` |
| `SSL_CERTIFICATE_ARN` | HTTPS cert | `arn:aws:acm:...` |

### Environment Protection

Configure in: Repository → Settings → Environments

**production:**
- Required reviewers: 1
- Deployment branch: main only

**production-infrastructure:**
- Required reviewers: 2
- Wait timer: 5 minutes
- Deployment branch: main only

## 💰 Cost Tracking

### View Current Costs
```bash
# AWS Cost Explorer
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

### Estimated Monthly Costs
- **Development**: ~$100-150/month
- **Production**: ~$150-300/month
- **High traffic**: ~$300-500/month

### Cost Optimization
- Scale down ECS tasks when not needed
- Use smaller RDS/Redis instances for dev
- Set up auto-scaling for production
- Monitor and clean up unused resources

## 📞 Support

### Self-Service
1. Check workflow logs in GitHub Actions
2. Review CloudWatch logs
3. Check this guide and README files
4. Search existing GitHub issues

### Get Help
- Create GitHub issue with logs
- Email: devops@nuvii.ai
- Slack: #deployments channel

## 📚 Additional Resources

- [Detailed Workflows Documentation](.github/workflows/README.md)
- [Full Deployment Guide](DEPLOYMENT.md)
- [Infrastructure Overview](infrastructure/README.md)
- [Backend API Documentation](backend/README.md)

---

## 🎓 Learning Resources

### GitHub Actions
- [Official Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)

### Terraform
- [AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)

### AWS ECS
- [ECS Developer Guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/)
- [Fargate Documentation](https://docs.aws.amazon.com/AmazonECS/latest/userguide/what-is-fargate.html)

---

**Last Updated**: 2024
**Maintainer**: DevOps Team
