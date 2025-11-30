#!/bin/bash
# Database Tunnel Helper
#
# This script creates a secure SSH tunnel through the bastion host to your RDS database
# using AWS Systems Manager Session Manager. No SSH keys required!
#
# Prerequisites:
#   - AWS CLI configured with appropriate credentials
#   - Session Manager plugin installed (run: brew install sessionmanagerplugin)
#   - psql, BeeKeeper Studio, DBeaver, or similar database client
#
# Usage:
#   ./scripts/db-tunnel.sh
#
# Then in another terminal:
#   psql -h localhost -U postgres -d artificial_u

# Don't exit on first error - we'll handle errors explicitly
set +e

REGION="us-east-1"
STACK_NAME="CdkStack"
LOCAL_PORT="5434"
REMOTE_PORT="5432"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}            Database Tunnel via Session Manager${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
    echo "   https://aws.amazon.com/cli/"
    exit 1
fi

# Check if Session Manager plugin is installed
if ! command -v session-manager-plugin &> /dev/null; then
    echo -e "${RED}❌ Session Manager plugin not found.${NC}"
    echo -e "${YELLOW}Install it with:${NC}"
    echo "   brew install sessionmanagerplugin  # macOS"
    echo "   choco install sessionmanagerplugin # Windows"
    echo "   sudo apt install session-manager-plugin  # Linux"
    echo ""
    exit 1
fi

# Check AWS credentials
echo -e "${YELLOW}🔐 Checking AWS credentials...${NC}"
AWS_IDENTITY=$(aws sts get-caller-identity --region "$REGION" 2>&1)
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ AWS credentials not configured or expired.${NC}"
    echo ""
    echo -e "${YELLOW}Error details:${NC}"
    echo "   $AWS_IDENTITY"
    echo ""
    echo -e "${YELLOW}Possible fixes:${NC}"
    echo "   1. Run: aws configure"
    echo "   2. Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
    echo "   3. Or configure SSO: aws sso login --profile your-profile"
    echo "   4. Or set AWS_PROFILE: export AWS_PROFILE=your-profile"
    echo ""
    exit 1
fi

AWS_ACCOUNT=$(echo "$AWS_IDENTITY" | grep -o '"Account": "[^"]*"' | cut -d'"' -f4)
AWS_USER=$(echo "$AWS_IDENTITY" | grep -o '"Arn": "[^"]*"' | cut -d'"' -f4 | awk -F'/' '{print $NF}')
echo -e "${GREEN}✅ Authenticated as: ${AWS_USER} (Account: ${AWS_ACCOUNT})${NC}"
echo ""

# Get stack resources
echo -e "${YELLOW}🔍 Looking up CloudFormation stack resources...${NC}"

# Try to get bastion ID with error capture
BASTION_RESULT=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='BastionInstanceId'].OutputValue" \
  --output text 2>&1)
BASTION_EXIT_CODE=$?

if [ $BASTION_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}❌ Failed to query CloudFormation stack.${NC}"
    echo ""
    echo -e "${YELLOW}Error details:${NC}"
    echo "   $BASTION_RESULT"
    echo ""

    # Check if stack exists at all
    STACK_EXISTS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" 2>&1)
    if echo "$STACK_EXISTS" | grep -q "does not exist"; then
        echo -e "${YELLOW}The CloudFormation stack '$STACK_NAME' does not exist.${NC}"
        echo ""
        echo -e "${YELLOW}To deploy the stack:${NC}"
        echo "   cd cdk && cdk deploy"
    elif echo "$STACK_EXISTS" | grep -q "ExpiredToken\|InvalidClientTokenId"; then
        echo -e "${YELLOW}Your AWS credentials have expired or are invalid.${NC}"
        echo "   Try: aws sso login"
    else
        echo -e "${YELLOW}Check that:${NC}"
        echo "   1. The stack '$STACK_NAME' exists in region '$REGION'"
        echo "   2. You have permission to describe CloudFormation stacks"
        echo "   3. Your AWS credentials are valid"
    fi
    echo ""
    exit 1
fi

BASTION_ID="$BASTION_RESULT"

# Get RDS endpoint
RDS_RESULT=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='DatabaseEndpoint'].OutputValue" \
  --output text 2>&1)
RDS_EXIT_CODE=$?

if [ $RDS_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}❌ Failed to get RDS endpoint from CloudFormation.${NC}"
    echo "   Error: $RDS_RESULT"
    exit 1
fi

RDS_ENDPOINT="$RDS_RESULT"

if [ -z "$BASTION_ID" ] || [ "$BASTION_ID" == "None" ]; then
    echo -e "${RED}❌ Could not find Bastion instance ID in stack outputs.${NC}"
    echo ""
    echo -e "${YELLOW}The stack exists but may not have a bastion host configured.${NC}"
    echo ""
    echo -e "${YELLOW}Check available stack outputs:${NC}"
    echo "   aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION \\"
    echo "     --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' --output table"
    echo ""
    echo -e "${YELLOW}Expected output key: 'BastionInstanceId'${NC}"
    echo ""
    echo -e "${YELLOW}If missing, you may need to:${NC}"
    echo "   1. Update your CDK stack to include the bastion host"
    echo "   2. Run: cd cdk && cdk deploy"
    exit 1
fi

if [ -z "$RDS_ENDPOINT" ] || [ "$RDS_ENDPOINT" == "None" ]; then
    echo -e "${RED}❌ Could not find RDS endpoint in stack outputs.${NC}"
    echo ""
    echo -e "${YELLOW}Check available stack outputs:${NC}"
    echo "   aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION \\"
    echo "     --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' --output table"
    echo ""
    echo -e "${YELLOW}Expected output key: 'DatabaseEndpoint'${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found resources:${NC}"
echo "   Bastion Instance: $BASTION_ID"
echo "   RDS Endpoint:     $RDS_ENDPOINT"
echo ""

# Check if bastion is running
echo -e "${YELLOW}🔄 Checking Bastion status...${NC}"
INSTANCE_RESULT=$(aws ec2 describe-instances \
  --instance-ids "$BASTION_ID" \
  --region "$REGION" \
  --query "Reservations[0].Instances[0].State.Name" \
  --output text 2>&1)
INSTANCE_EXIT_CODE=$?

if [ $INSTANCE_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}❌ Failed to check bastion instance status.${NC}"
    echo ""
    echo -e "${YELLOW}Error details:${NC}"
    echo "   $INSTANCE_RESULT"
    echo ""
    if echo "$INSTANCE_RESULT" | grep -q "InvalidInstanceID"; then
        echo -e "${YELLOW}The instance ID '$BASTION_ID' does not exist.${NC}"
        echo "   The bastion may have been terminated."
        echo "   Try redeploying: cd cdk && cdk deploy"
    elif echo "$INSTANCE_RESULT" | grep -q "UnauthorizedOperation"; then
        echo -e "${YELLOW}You don't have permission to describe EC2 instances.${NC}"
        echo "   Check your IAM permissions."
    fi
    exit 1
fi

INSTANCE_STATE="$INSTANCE_RESULT"

if [ "$INSTANCE_STATE" != "running" ]; then
    echo -e "${YELLOW}⚠️  Bastion is in state: $INSTANCE_STATE${NC}"
    if [ "$INSTANCE_STATE" == "stopped" ]; then
        echo -e "${YELLOW}Starting bastion instance...${NC}"
        START_RESULT=$(aws ec2 start-instances --instance-ids "$BASTION_ID" --region "$REGION" 2>&1)
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Failed to start bastion instance.${NC}"
            echo "   Error: $START_RESULT"
            exit 1
        fi
        echo -e "${YELLOW}Waiting for bastion to start (this may take a moment)...${NC}"
        aws ec2 wait instance-running --instance-ids "$BASTION_ID" --region "$REGION"
        echo -e "${GREEN}✅ Bastion started${NC}"
    else
        echo -e "${RED}❌ Bastion is in an unexpected state: $INSTANCE_STATE${NC}"
        echo ""
        echo -e "${YELLOW}If the instance is terminated, redeploy:${NC}"
        echo "   cd cdk && cdk deploy"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Bastion is running${NC}"
fi

# Check if local port is already in use
if lsof -Pi :$LOCAL_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}❌ Port $LOCAL_PORT is already in use.${NC}"
    echo ""
    echo -e "${YELLOW}Check what's using it:${NC}"
    echo "   lsof -i :$LOCAL_PORT"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "   1. Kill the process using the port"
    echo "   2. Edit LOCAL_PORT in this script to use a different port"
    exit 1
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🚀 Creating tunnel...${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Tunnel Details:${NC}"
echo "   Local:  localhost:$LOCAL_PORT"
echo "   Remote: $RDS_ENDPOINT:$REMOTE_PORT"
echo ""
echo -e "${YELLOW}To connect, in another terminal run:${NC}"
echo "   ${GREEN}psql -h localhost -U postgres -d artificial_u${NC}"
echo ""
echo -e "${YELLOW}Database credentials:${NC}"
echo "   - Username and password are in AWS Secrets Manager"
echo "   - Or check your deployment documentation"
echo ""
echo -e "${YELLOW}To close this tunnel, press ${RED}Ctrl+C${YELLOW}${NC}"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Create the tunnel (runs in foreground until Ctrl+C)
# The session will output errors directly if it fails
aws ssm start-session \
  --target "$BASTION_ID" \
  --region "$REGION" \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters "{\"portNumber\":[\"$REMOTE_PORT\"],\"localPortNumber\":[\"$LOCAL_PORT\"],\"host\":[\"$RDS_ENDPOINT\"]}"

TUNNEL_EXIT_CODE=$?

# If we get here, the tunnel has ended
echo ""
if [ $TUNNEL_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}❌ Tunnel session ended with an error (exit code: $TUNNEL_EXIT_CODE).${NC}"
    echo ""
    echo -e "${YELLOW}Common issues:${NC}"
    echo "   - TargetNotConnected: Wait 1-2 minutes for SSM agent to start"
    echo "   - AccessDeniedException: Check your IAM permissions for ssm:StartSession"
    echo "   - Session timeout: The bastion may have been stopped"
    echo ""
    echo -e "${YELLOW}Try running again or check AWS Console for more details.${NC}"
    exit 1
else
    echo -e "${GREEN}Tunnel closed.${NC}"
fi

