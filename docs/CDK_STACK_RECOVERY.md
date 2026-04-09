# CloudFormation Stack Recovery Guide

When your CDK stack gets stuck in `UPDATE_ROLLBACK_FAILED` or another blocked state, follow this guide to recover.

## Understanding Stack States

The deployment workflow now checks for these problematic states before attempting deployment:

- **`UPDATE_ROLLBACK_FAILED`**: A previous update failed and rollback also failed. This is the most common stuck state.
- **`DELETE_IN_PROGRESS` / `DELETE_FAILED`**: Stack is being deleted or deletion failed.
- **`CREATE_IN_PROGRESS` / `UPDATE_IN_PROGRESS`**: Stack operation is still in progress (shouldn't happen in normal workflows).
- **`DELETE_COMPLETE`**: Stack was deleted but may still be referenced.

## Manual Recovery Steps

### 1. Check Stack Status (AWS CLI)

```bash
aws cloudformation describe-stacks \
  --stack-name CdkStack \
  --region us-east-1 \
  --query 'Stacks[0].StackStatus' \
  --output text
```

### 2. View Stack Events

To understand what caused the failure:

```bash
aws cloudformation describe-stack-events \
  --stack-name CdkStack \
  --region us-east-1 \
  --query 'StackEvents[0:10]' \
  --output table
```

Or use the AWS Console:

1. Navigate to **CloudFormation** > **Stacks** > **CdkStack**
2. Click the **Events** tab
3. Look for entries with **Status Reason** showing errors

### 3. Resolve Based on State

#### If Stack is in `UPDATE_ROLLBACK_FAILED`

**Option A: Continue Rollback (AWS CLI)**

```bash
aws cloudformation continue-update-rollback \
  --stack-name CdkStack \
  --region us-east-1
```

**Option B: Continue Rollback (AWS Console)**

1. Go to CloudFormation > Stacks > CdkStack
2. Click **Stack Actions** dropdown
3. Select **Continue Update Rollback**
4. Confirm the action

After continuing rollback, the stack should return to its previous stable state (`UPDATE_ROLLBACK_COMPLETE`).

#### If Stack is in `DELETE_FAILED`

You may need to delete problematic resources manually, then retry:

```bash
# Force delete the stack, optionally retaining specific resources
aws cloudformation delete-stack \
  --stack-name CdkStack \
  --region us-east-1
```

Or delete with retained resources:

```bash
aws cloudformation delete-stack \
  --stack-name CdkStack \
  --region us-east-1 \
  --retain-resources ResourceLogicalId1 ResourceLogicalId2
```

#### If Stack is in `UPDATE_ROLLBACK_COMPLETE`

This is a stable state but indicates a previous failed update. Before redeploying:

1. Review what caused the previous failure
2. Ensure all prerequisites are met (secrets in SSM Parameter Store, etc.)
3. Try deploying again with `cdk deploy`

### 4. Verify Recovery

After manual intervention, verify the stack is in a good state:

```bash
aws cloudformation describe-stacks \
  --stack-name CdkStack \
  --region us-east-1 \
  --query 'Stacks[0].[StackStatus,CreationTime,LastUpdatedTime]' \
  --output table
```

Expected states after recovery:

- `CREATE_COMPLETE`
- `UPDATE_COMPLETE`
- `UPDATE_ROLLBACK_COMPLETE`

### 5. Retry Deployment

Once the stack is in a stable state, retry your deployment:

```bash
cd cdk
cdk deploy --require-approval never
```

Or push to `prod` branch to trigger GitHub Actions workflow.

## Common Root Causes

### Database Issues

- **Cause**: RDS database creation/modification exceeds CloudFormation timeout
- **Fix**: Extend timeout or check RDS logs for specific errors
- **Prevention**: Increase `health_check_grace_period` in CDK stack

### Missing Secrets

- **Cause**: SSM Parameter Store values don't exist
- **Fix**: Create all required parameters in the AWS Console
- **Required Parameters**:
  - `/artificial-u/prod/ANTHROPIC_API_KEY`
  - `/artificial-u/prod/ELEVENLABS_API_KEY`
  - `/artificial-u/prod/MISTRAL_API_KEY`
  - `/artificial-u/prod/GOOGLE_API_KEY`
  - `/artificial-u/prod/OPENAI_API_KEY`
  - `/artificial-u/prod/AUTH0_DOMAIN`
  - `/artificial-u/prod/AUTH0_AUDIENCE`

### Security Group/VPC Issues

- **Cause**: VPC or security group configuration conflicts
- **Fix**: Review VPC settings and ensure subnets are properly configured
- **Check**: Run `aws ec2 describe-vpcs` and `aws ec2 describe-security-groups`

### Container Image Build Failures

- **Cause**: Docker build context or Dockerfile issue during ECR push
- **Fix**: Build locally first to verify: `docker build -f Dockerfile.api .`

### Insufficient IAM Permissions

- **Cause**: GitHub Actions role lacks necessary permissions
- **Fix**: Verify IAM role has sufficient CloudFormation and service permissions

## Prevention

The new pre-deploy check in `.github/workflows/deploy.yml` now automatically:

1. Detects stuck stacks before attempting deployment
2. Provides clear error messages with recovery steps
3. Prevents wasting CI/CD minutes on failed deployments

To manually check before pushing to prod:

```bash
aws cloudformation describe-stacks \
  --stack-name CdkStack \
  --region us-east-1 \
  --query 'Stacks[0].StackStatus' \
  --output text
```

## Additional Resources

- [AWS CloudFormation Troubleshooting](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/troubleshooting.html)
- [Continue Update Rollback API](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_ContinueUpdateRollback.html)
- [Stack Status Codes](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-describing-stacks.html)
