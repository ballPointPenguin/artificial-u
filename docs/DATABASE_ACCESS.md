# Remote Database Access

This guide explains how to securely connect to your RDS database from your laptop using the bastion host and AWS Systems Manager Session Manager.

## Quick Start

### Prerequisites

1. **AWS CLI**: [Install AWS CLI v2](https://aws.amazon.com/cli/)
2. **Session Manager Plugin**:

   ```bash
   # macOS
   brew install sessionmanagerplugin

   # Windows (Chocolatey)
   choco install sessionmanagerplugin

   # Linux (Ubuntu/Debian)
   sudo apt install session-manager-plugin
   ```

3. **Database Client** (one of):
   - `psql` (PostgreSQL CLI)
   - [BeeKeeper Studio](https://www.beekeeperstudio.io/) (GUI)
   - [DBeaver](https://dbeaver.io/) (GUI)
   - Any PostgreSQL client

### Connect to the Database

**Step 1: Start the tunnel** (Terminal 1)

```bash
./scripts/db-tunnel.sh
```

This will:

- Look up your bastion instance and RDS endpoint from CloudFormation
- Start your bastion if it's stopped
- Create an encrypted tunnel to your database
- Keep running until you press Ctrl+C

**Step 2: Connect** (Terminal 2)

```bash
# Using psql
psql -h localhost -U postgres -d artificial_u

# Then enter your database password when prompted
# (Check AWS Secrets Manager for credentials)
```

Or connect with BeeKeeper Studio:

- **Host**: `localhost`
- **Port**: `5434`
- **Database**: `artificial_u`
- **Username**: Check AWS Secrets Manager
- **Password**: Check AWS Secrets Manager

## How It Works

```text
Your Laptop          Bastion Host (EC2)       VPC              RDS Database
┌─────────────┐      ┌──────────────────┐    ┌────────────────┐
│ psql        │ --→  │ AWS Systems Mgr  │ →  │ Private VPC    │
│ (localhost) │      │ (SSH tunneling)  │    │ Security Group │
└─────────────┘      └──────────────────┘    └────────────────┘
   :5434                  Session Mgr               :5432
     ↓                      Plugin                    ↓
  Port 5434              Port Forwarding          RDS Instance
   Local                  Encrypted Tunnel          Private
```

**Benefits:**

- ✅ **No SSH keys**: Uses AWS IAM authentication
- ✅ **Secure**: Encrypted tunnel through AWS infrastructure
- ✅ **Database stays private**: Not exposed on the public internet
- ✅ **Audit logging**: All connections logged in CloudTrail
- ✅ **Ephemeral access**: Permissions controlled by IAM

## Getting Database Credentials

Your database credentials are stored in AWS Secrets Manager:

```bash
# List all secrets
aws secretsmanager list-secrets --region us-east-1

# Get the RDS database secret (created automatically by CDK)
aws secretsmanager get-secret-value \
  --secret-id rds-db-credentials/cluster-<ID> \
  --region us-east-1 \
  --query SecretString \
  --output text | jq .

# Or find it in the AWS Console:
# Secrets Manager → Search for "rds" or "database"
```

The secret contains:

```json
{
  "username": "postgres",
  "password": "your-generated-password",
  "host": "...",
  "port": 5432,
  "dbname": "artificial_u"
}
```

## Troubleshooting

### "Session Manager plugin not found"

Install the Session Manager plugin (see Prerequisites above).

### "Could not find Bastion instance"

Make sure:

1. Your CDK stack has been deployed: `cdk deploy`
2. You're in the correct AWS account and region
3. The stack shows "CREATE_COMPLETE" or "UPDATE_COMPLETE"

### "Tunnel connection refused"

Try these steps:

1. Ensure the bastion host is running
2. Check that the bastion security group allows outbound traffic
3. Verify the RDS security group allows inbound from the bastion
4. Check that your IAM user/role has EC2 and RDS permissions

### "Could not find RDS endpoint"

Make sure the RDS instance is fully initialized:

```bash
aws rds describe-db-instances \
  --db-instance-identifier cdkstack-database \
  --region us-east-1 \
  --query 'DBInstances[0].DBInstanceStatus'
```

Should show: `available`

### "Access denied" when connecting to database

This usually means the database credentials are wrong:

1. Get the correct credentials from Secrets Manager (see above)
2. Make sure you're connecting to the right database: `artificial_u`
3. Username should be: `postgres` (unless changed)

### Tunnel works but psql says "could not connect"

Try troubleshooting:

```bash
# Check if port 5434 is listening locally
lsof -i :5434

# Try connecting with verbose output
psql -h localhost -U postgres -d artificial_u -v on_error_stop=on

# Or test the connection directly
nc -zv localhost 5434
```

## Advanced: Manual Tunnel with AWS CLI

If the script doesn't work, you can create the tunnel manually:

```bash
# Get instance and endpoint IDs
BASTION_ID=$(aws ec2 describe-instances \
  --region us-east-1 \
  --filters "Name=tag:aws:cloudformation:stack-name,Values=CdkStack" \
  --query "Reservations[0].Instances[0].InstanceId" \
  --output text)

RDS_ENDPOINT=$(aws rds describe-db-instances \
  --region us-east-1 \
  --query "DBInstances[0].Endpoint.Address" \
  --output text)

# Create tunnel
aws ssm start-session \
  --target "$BASTION_ID" \
  --region us-east-1 \
  --document-name AWS-StartPortForwardingSession \
  --parameters "localPortNumber=5434,remotePortNumber=5432,remoteHost=$RDS_ENDPOINT"
```

## Cost Considerations

- **Bastion host**: t4g.micro = ~$3-5/month (eligible for free tier)
- **Data transfer**: Minimal cost for local tunneling
- **Session Manager**: No additional charge

Total cost: Essentially free if within free tier, otherwise ~$5/month.

## Security Best Practices

1. **Rotate credentials regularly**: Update your database password in Secrets Manager
2. **Restrict IAM permissions**: Only your IAM user should be able to start sessions
3. **Monitor CloudTrail**: All session manager connections are logged
4. **Use short-lived sessions**: Close your tunnel when done (Ctrl+C)
5. **Never commit database passwords**: Keep credentials in Secrets Manager

## Related Documentation

- [AWS Systems Manager Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)
- [Port Forwarding Through Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html#session-manager-plugin-port-forwarding)
- [RDS Security Groups](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.DBSecurityGroup.html)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
