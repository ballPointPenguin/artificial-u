# Bastion Host Setup Summary

This document summarizes the changes made to enable secure remote database access.

## What Was Added

### 1. CDK Stack Changes (`cdk/cdk/cdk_stack.py`)

**Bastion Host Instance** (lines 47-57):

- Created a t4g.micro EC2 instance in the VPC
- Uses Amazon Linux 2023 (latest stable)
- Automatically configured with Systems Manager permissions
- Cost: ~$3-5/month (eligible for free tier)

**Security Group Rule** (lines 211-213):

- Allows bastion host to connect to RDS database on port 5432
- Keeps database in private VPC
- No direct public exposure

**Stack Outputs** (lines 356-367):

- `BastionInstanceId`: Instance ID for reference
- `DatabaseEndpoint`: RDS endpoint for scripting

### 2. Helper Script (`scripts/db-tunnel.sh`)

A smart helper script that:

- ✅ Checks prerequisites (AWS CLI, Session Manager plugin)
- ✅ Looks up bastion instance ID and RDS endpoint from CloudFormation
- ✅ Starts the bastion if it's stopped
- ✅ Creates an encrypted tunnel through Systems Manager
- ✅ Provides clear instructions and error messages
- ✅ Works with any PostgreSQL client

### 3. Documentation

**`docs/DATABASE_ACCESS.md`** - Complete guide including:

- Quick start instructions
- Connection examples for psql, BeeKeeper Studio, DBeaver
- How it works (architecture diagram)
- Troubleshooting section
- Security best practices
- Cost considerations

**`docs/BASTION_SETUP.md`** - This file (summary of changes)

## Next Steps

### 1. Deploy the Updated Stack

```bash
cd cdk
cdk deploy --require-approval never
```

This will:

- Create the bastion EC2 instance
- Output the instance ID and database endpoint
- Take about 5-10 minutes

### 2. Install Prerequisites

```bash
# macOS
brew install sessionmanagerplugin

# Verify AWS CLI is installed
aws --version
```

### 3. Connect to Your Database

```bash
# Terminal 1: Start tunnel
./scripts/db-tunnel.sh

# Terminal 2: Connect with psql
psql -h localhost -U postgres -d artificial_u
```

## Architecture

```text
┌─────────────────┐
│  Your Laptop    │
│                 │
│  psql/BeeKeeper │◄─┐
│ (localhost:5434)│  │
└────────┬────────┘  │ Tunnel
         │           │ (Session Manager)
         └───────────►─┐
                       │
                ┌──────┴──────┐
                │   Bastion   │ (EC2 t4g.micro)
                │   Instance  │
                └──────┬──────┘
                       │ (Private VPC)
                       │
                ┌──────▼──────────────┐
                │  Private VPC        │
                │                     │
                │  ┌────────────────┐ │
                │  │ RDS Database   │ │
                │  │ (artificial_u) │ │
                │  └────────────────┘ │
                └─────────────────────┘
```

## Security Features

| Feature | Benefit |
|---------|---------|
| **IAM Authentication** | No SSH keys required |
| **Encrypted Tunnel** | Data in transit encrypted |
| **Private Database** | Not exposed on public internet |
| **Session Manager** | AWS manages access control |
| **CloudTrail Logging** | All connections audited |
| **Security Groups** | Multiple layers of protection |

## Cost Breakdown

| Component | Cost | Notes |
|-----------|------|-------|
| Bastion (t4g.micro) | ~$3-5/mo | Eligible for free tier |
| Session Manager | Free | No additional charge |
| Data transfer | Minimal | Same region = no egress cost |
| RDS Database | Separate | Not changed |
| **Total** | **~$5/mo** | Within free tier if available |

## File Changes Summary

```text
Modified:
  cdk/cdk/cdk_stack.py
    - Added bastion host (15 lines)
    - Added security group rule (3 lines)
    - Added stack outputs (12 lines)

Created:
  scripts/db-tunnel.sh (143 lines)
  docs/DATABASE_ACCESS.md (Comprehensive guide)
  docs/BASTION_SETUP.md (This file)
```

## Testing the Connection

### Quick Test

```bash
./scripts/db-tunnel.sh
# In another terminal:
psql -h localhost -U postgres -d artificial_u
```

### Test with BeeKeeper Studio

1. Launch BeeKeeper Studio
2. Create new connection
3. Host: `localhost`, Port: `5434`
4. Username: `postgres` (or check Secrets Manager)
5. Database: `artificial_u`

### Test with DBeaver

1. New Database Connection
2. Select PostgreSQL
3. Host: `localhost`, Port: `5434`
4. Database: `artificial_u`
5. Fill in credentials from Secrets Manager

## Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| "Session Manager plugin not found" | `brew install sessionmanagerplugin` |
| "Could not find Bastion instance" | Run `cdk deploy` first |
| "Connection refused" | Wait for bastion to start (~2 min) |
| "Access denied" | Check database credentials in Secrets Manager |
| "Port already in use" | Change LOCAL_PORT in db-tunnel.sh |

## Related Documentation

- [AWS Systems Manager Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)
- [Database Access Guide](./DATABASE_ACCESS.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [CDK Stack Recovery](./CDK_STACK_RECOVERY.md)
