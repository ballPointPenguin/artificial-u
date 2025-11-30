# Database Tunnel - Quick Start

## TL;DR

```bash
# Install (one time)
brew install sessionmanagerplugin

# Connect
./scripts/db-tunnel.sh

# In another terminal
psql -h localhost -U postgres -d artificial_u
```

## Prerequisites

- [x] AWS CLI installed
- [x] Session Manager plugin: `brew install sessionmanagerplugin`
- [x] CDK stack deployed: `cd cdk && cdk deploy`
- [x] psql or BeeKeeper Studio installed

## Usage

### Step 1: Start Tunnel (Terminal 1)

```bash
./scripts/db-tunnel.sh
```

Output should show:

```text
✅ Found resources:
   Bastion Instance: i-0123456789abcdef
   RDS Endpoint:     cdkstack-database-xxxxx.us-east-1.rds.amazonaws.com

🚀 Creating tunnel...
   Tunnel Details:
      Local:  localhost:5434
      Remote: cdkstack-database-xxxxx:5432
```

### Step 2: Connect (Terminal 2)

#### Option A: psql

```bash
psql -h localhost -U postgres -d artificial_u
# Enter password when prompted
```

#### Option B: BeeKeeper Studio

1. New Connection
2. Select PostgreSQL
3. Fill in:
   - Host: `localhost`
   - Port: `5434`
   - Database: `artificial_u`
   - Username: `postgres`
   - Password: (from AWS Secrets Manager)
4. Click Test
5. Click Save

#### Option C: DBeaver

1. Database → New Database Connection
2. Select PostgreSQL, Click Next
3. Fill in same details as BeeKeeper Studio
4. Test Connection
5. Finish

## Common Issues

### "Could not find Bastion instance"

```bash
# Make sure stack is deployed
cd cdk && cdk deploy
```

### "Session Manager plugin not found"

```bash
# Install it
brew install sessionmanagerplugin
```

### "Access denied" to database

```bash
# Get database password from Secrets Manager
aws secretsmanager list-secrets --region us-east-1 | grep -i rds
```

### "psql: could not translate host name"

- Make sure tunnel is still running in Terminal 1
- Try: `nc -zv localhost 5434`

## Cleanup

Press `Ctrl+C` in Terminal 1 to close the tunnel. Bastion instance will stop automatically after 60 minutes.

## Full Documentation

See `docs/DATABASE_ACCESS.md` for complete guide with troubleshooting.
