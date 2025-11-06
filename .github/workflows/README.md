# CI/CD Workflows

This directory contains separate CI/CD pipelines for infrastructure and application deployment.

## Workflows Overview

### 1. Infrastructure Deployment (`infrastructure-deploy.yml`)

**Purpose**: Deploy and manage AWS infrastructure using Terraform

**Triggers:**
- Push to `main` branch with changes in `infrastructure/terraform/**`
- Pull requests with infrastructure changes (runs plan only)
- Manual trigger via workflow_dispatch with options: `plan`, `apply`, or `destroy`

**Jobs:**
- `terraform-validate`: Validates Terraform syntax and formatting
- `terraform-plan`: Creates execution plan (PRs and manual runs)
- `terraform-apply`: Applies infrastructure changes (main branch only)
- `terraform-destroy`: Destroys infrastructure (manual only, requires approval)

**Required Secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `DB_PASSWORD`
- `APP_SECRET_KEY`
- `STRIPE_SECRET_KEY`
- `SSL_CERTIFICATE_ARN`

**Environments:**
- `production-infrastructure`: Required for apply operations
- `production-infrastructure-destroy`: Required for destroy operations

---

### 2. Backend Application Deployment (`backend-deploy.yml`)

**Purpose**: Build, test, and deploy the FastAPI backend application

**Triggers:**
- Push to `main` branch with changes in `backend/**`
- Pull requests with backend changes (runs tests and linting only)
- Manual trigger via workflow_dispatch

**Jobs:**
- `test`: Runs pytest with PostgreSQL and Redis services
- `lint`: Checks code quality with Black and Flake8 (PRs only)
- `build-and-deploy`: Builds Docker image, pushes to ECR, deploys to ECS (main only)
- `notify-on-failure`: Sends notifications on deployment failures

**Required Secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

**Environments:**
- `production`: Required for deployment to ECS

---

## Workflow Separation Benefits

### ✅ Safety
- Infrastructure changes require explicit approval
- Application deployments don't accidentally modify infrastructure
- Separate approval gates for infrastructure vs application changes

### ✅ Speed
- Application deployments are faster (no Terraform operations)
- Infrastructure changes don't trigger unnecessary application rebuilds
- Can deploy apps multiple times without touching infrastructure

### ✅ Clarity
- Clear separation of concerns
- Easier to troubleshoot issues
- Better audit trail

---

## Deployment Order

### Initial Setup (First Time)

1. **Deploy Infrastructure First**
   ```bash
   # Option A: Manual workflow trigger
   # Go to Actions → Infrastructure Deployment → Run workflow → Select "apply"

   # Option B: Push infrastructure changes
   git add infrastructure/
   git commit -m "feat: initial infrastructure setup"
   git push origin main
   ```

2. **Deploy Application**
   ```bash
   # Automatically triggers after infrastructure is ready
   git add backend/
   git commit -m "feat: initial backend deployment"
   git push origin main
   ```

### Regular Development

**For backend code changes:**
```bash
git add backend/
git commit -m "feat: add new endpoint"
git push origin main
# Only backend-deploy.yml runs
```

**For infrastructure changes:**
```bash
git add infrastructure/
git commit -m "feat: increase ECS task count"
git push origin main
# Only infrastructure-deploy.yml runs
```

**For both:**
```bash
git add backend/ infrastructure/
git commit -m "feat: scale infrastructure and update app"
git push origin main
# Both workflows run in parallel
```

---

## Pull Request Workflow

### Backend PR
1. Create PR with backend changes
2. Workflow runs:
   - ✅ Tests (pytest)
   - ✅ Linting (Black, Flake8)
3. Review and merge
4. Automatic deployment to production

### Infrastructure PR
1. Create PR with infrastructure changes
2. Workflow runs:
   - ✅ Terraform validate
   - ✅ Terraform plan (posted as comment)
3. Review plan carefully
4. Merge PR
5. Manual approval required for apply

---

## Manual Deployments

### Deploy Infrastructure Manually

Go to GitHub Actions → Infrastructure Deployment → Run workflow

**Options:**
- `plan`: Preview changes without applying
- `apply`: Apply infrastructure changes
- `destroy`: Destroy all infrastructure (use with caution!)

### Deploy Backend Manually

Go to GitHub Actions → Backend Application Deployment → Run workflow

---

## Environment Protection Rules

### Recommended Settings

#### For `production` environment:
- ✅ Required reviewers: 1-2 people
- ✅ Wait timer: 0 minutes (can add delay if needed)
- ✅ Restrict to `main` branch only

#### For `production-infrastructure` environment:
- ✅ Required reviewers: 2+ people (infrastructure is critical)
- ✅ Wait timer: 5 minutes (gives time to cancel)
- ✅ Restrict to `main` branch only

#### For `production-infrastructure-destroy` environment:
- ✅ Required reviewers: All admins
- ✅ Wait timer: 30 minutes
- ✅ Custom deployment protection rules
- ✅ Restrict to workflow_dispatch only

### How to Configure

1. Go to Repository Settings → Environments
2. Create each environment listed above
3. Add protection rules
4. Add required reviewers

---

## Monitoring Deployments

### View Workflow Status
```bash
# Using GitHub CLI
gh run list --workflow=backend-deploy.yml
gh run list --workflow=infrastructure-deploy.yml

# View specific run
gh run view <run-id>
```

### Check Deployment Logs
```bash
# CloudWatch logs
aws logs tail /ecs/nuvii --follow

# ECS service events
aws ecs describe-services \
  --cluster nuvii-cluster \
  --services nuvii-backend-service \
  --query 'services[0].events[0:10]'
```

---

## Rollback Procedures

### Rollback Application Deployment

**Option 1: Revert via Git**
```bash
git revert <commit-sha>
git push origin main
# Automatic redeployment with previous code
```

**Option 2: Redeploy Previous Image**
```bash
# Get previous task definition revision
aws ecs describe-task-definition \
  --task-definition nuvii-backend-task \
  --query 'taskDefinition.revision'

# Update service to use previous revision
aws ecs update-service \
  --cluster nuvii-cluster \
  --service nuvii-backend-service \
  --task-definition nuvii-backend-task:<previous-revision>
```

**Option 3: Manual Workflow Trigger**
```bash
# Checkout previous commit and trigger workflow
git checkout <previous-commit-sha>
# Manually trigger workflow from GitHub Actions UI
```

### Rollback Infrastructure Changes

```bash
# Revert Terraform changes
cd infrastructure/terraform

# Revert to previous state
git revert <infrastructure-commit-sha>
git push origin main

# Or manually run terraform apply with reverted code
```

---

## Troubleshooting

### Infrastructure Deployment Fails

1. Check Terraform plan output in workflow logs
2. Verify all secrets are set correctly
3. Check AWS service quotas
4. Review CloudTrail for permission issues

```bash
# Check if resources exist
terraform state list

# Verify AWS credentials
aws sts get-caller-identity
```

### Backend Deployment Fails

1. Check Docker build logs
2. Verify ECR repository exists
3. Check ECS service events
4. Review CloudWatch logs

```bash
# Check ECS service status
aws ecs describe-services \
  --cluster nuvii-cluster \
  --services nuvii-backend-service

# View recent container logs
aws logs tail /ecs/nuvii --since 30m
```

### Tests Failing in CI

```bash
# Run tests locally with same services
cd backend
docker-compose up -d db redis
pytest -v

# Check test coverage
pytest --cov=app tests/
```

---

## Cost Optimization

### Prevent Unnecessary Runs

Both workflows use path filters to only run when relevant files change:

**Infrastructure workflow** only runs for:
- `infrastructure/terraform/**`
- `.github/workflows/infrastructure-deploy.yml`

**Backend workflow** only runs for:
- `backend/**`
- `.github/workflows/backend-deploy.yml`

### Reduce AWS Costs

```bash
# Stop ECS services when not needed
aws ecs update-service \
  --cluster nuvii-cluster \
  --service nuvii-backend-service \
  --desired-count 0

# Destroy infrastructure for development
# Go to Actions → Infrastructure Deployment → destroy
```

---

## Security Best Practices

1. **Secrets Management**
   - ✅ Never commit secrets to repository
   - ✅ Use GitHub Secrets for sensitive values
   - ✅ Rotate AWS credentials regularly

2. **Access Control**
   - ✅ Enable environment protection rules
   - ✅ Require approvals for production deployments
   - ✅ Use separate AWS accounts for dev/staging/prod

3. **Audit Trail**
   - ✅ All deployments are logged in GitHub Actions
   - ✅ Enable AWS CloudTrail
   - ✅ Review deployment history regularly

4. **Branch Protection**
   - ✅ Require PR reviews before merging to main
   - ✅ Require status checks to pass
   - ✅ No direct pushes to main branch

---

## FAQ

**Q: Can I deploy backend without deploying infrastructure?**
A: Yes! The workflows are completely independent. Backend deployments don't touch infrastructure.

**Q: What happens if both workflows run at the same time?**
A: They run in parallel safely. Infrastructure changes don't affect running containers during updates.

**Q: How do I test infrastructure changes before applying?**
A: Create a PR with infrastructure changes. The workflow will run `terraform plan` and post the results as a comment.

**Q: Can I deploy to a different environment?**
A: Yes, you can create additional workflow files for staging/development environments with different configurations.

**Q: How long do deployments take?**
- Infrastructure: 10-15 minutes (first time), 2-5 minutes (updates)
- Backend: 3-5 minutes

**Q: What if I need to rollback quickly?**
A: Use Option 2 from the Rollback section above to immediately switch to a previous task definition revision.

---

## Support

For issues or questions:
- Check workflow logs in GitHub Actions
- Review this documentation
- Create an issue in the repository
- Contact DevOps team

## Related Documentation

- [DEPLOYMENT.md](../../DEPLOYMENT.md) - Full deployment guide
- [infrastructure/README.md](../../infrastructure/README.md) - Infrastructure overview
- [backend/README.md](../../backend/README.md) - Backend documentation
