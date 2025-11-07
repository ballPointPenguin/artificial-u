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

set -e

REGION="us-east-1"
STACK_NAME="CdkStack"
LOCAL_PORT="5432"
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

# Get stack resources
echo -e "${YELLOW}🔍 Looking up CloudFormation stack resources...${NC}"

BASTION_ID=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='BastionInstanceId'].OutputValue" \
  --output text 2>/dev/null)

RDS_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='DatabaseEndpoint'].OutputValue" \
  --output text 2>/dev/null)

if [ -z "$BASTION_ID" ]; then
    echo -e "${RED}❌ Could not find Bastion instance.${NC}"
    echo "   Is the CDK stack deployed? Check with:"
    echo "   aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION"
    exit 1
fi

if [ -z "$RDS_ENDPOINT" ]; then
    echo -e "${RED}❌ Could not find RDS endpoint.${NC}"
    echo "   Is the CDK stack deployed? Check with:"
    echo "   aws cloudformation describe-stack-outputs --stack-name $STACK_NAME --region $REGION"
    exit 1
fi

echo -e "${GREEN}✅ Found resources:${NC}"
echo "   Bastion Instance: $BASTION_ID"
echo "   RDS Endpoint:     $RDS_ENDPOINT"
echo ""

# Check if bastion is running
echo -e "${YELLOW}🔄 Checking Bastion status...${NC}"
INSTANCE_STATE=$(aws ec2 describe-instances \
  --instance-ids "$BASTION_ID" \
  --region "$REGION" \
  --query "Reservations[0].Instances[0].State.Name" \
  --output text 2>/dev/null)

if [ "$INSTANCE_STATE" != "running" ]; then
    echo -e "${YELLOW}⚠️  Bastion is in state: $INSTANCE_STATE${NC}"
    if [ "$INSTANCE_STATE" == "stopped" ]; then
        echo -e "${YELLOW}Starting bastion instance...${NC}"
        aws ec2 start-instances --instance-ids "$BASTION_ID" --region "$REGION" > /dev/null
        echo -e "${YELLOW}Waiting for bastion to start (this may take a moment)...${NC}"
        aws ec2 wait instance-running --instance-ids "$BASTION_ID" --region "$REGION"
        echo -e "${GREEN}✅ Bastion started${NC}"
    else
        echo -e "${RED}❌ Bastion is in an unexpected state: $INSTANCE_STATE${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Bastion is running${NC}"
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

# Create the tunnel
aws ssm start-session \
  --target "$BASTION_ID" \
  --region "$REGION" \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters "{\"portNumber\":[\"$REMOTE_PORT\"],\"localPortNumber\":[\"$LOCAL_PORT\"],\"host\":[\"$RDS_ENDPOINT\"]}"

