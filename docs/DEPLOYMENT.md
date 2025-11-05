# Deployment

This document outlines the deployment process for the Artificial University stack to Amazon Web Services (AWS) using the AWS Cloud Development Kit (CDK).

## Architecture Overview

The AWS infrastructure is defined as code using the Python CDK and consists of the following core components:

- **Amazon VPC**: A dedicated Virtual Private Cloud (VPC) to host all network-isolated resources.
- **Amazon RDS**: A managed PostgreSQL database instance (db.t4g.small) for the application's data persistence.
- **Amazon S3**:
  - Three private buckets for application data storage: `audio`, `lectures`, and `images`, replacing the self-hosted MinIO.
  - One public bucket configured for static website hosting for the SolidJS frontend.
- **Amazon ECS on AWS Fargate**: A serverless compute engine to run the FastAPI backend container without managing servers.
- **Application Load Balancer (ALB)**: An internet-facing ALB that fronts the ECS service. The ALB must be public for CloudFront to reach it, as CloudFront cannot connect to internal (VPC-only) load balancers.
- **Amazon CloudFront**: A global Content Delivery Network (CDN) that provides the public entry point to the application. It is configured with two origins:
    1. The frontend S3 bucket (default behavior) to serve the web application.
    2. The public ALB to route `/api/*` requests to the backend ECS service.
- **AWS Secrets Manager & SSM Parameter Store**: For securely managing database credentials and other application secrets.
- **Amazon ECR**: A private container registry to store the backend Docker image.

This architecture ensures a scalable, secure, and maintainable deployment. The frontend and backend are decoupled, with CloudFront acting as the single point of public access, routing traffic appropriately.

---

## Prerequisites

Before deploying, ensure you have the following installed and configured:

1. **AWS CLI**: Installed and configured with credentials for your AWS account.

    ```bash
    aws configure
    ```

2. **Node.js and npm**: Required to install the CDK CLI.
3. **AWS CDK CLI**:

    ```bash
    npm install -g aws-cdk
    ```

4. **Python 3.13+ and Hatch**: For managing the Python environment. [[memory:6174773]]
5. **Docker**: The CDK will use Docker to build the API container image locally before pushing it to ECR.

---

## Deployment Steps

The entire deployment process is managed by the CDK.

### 1. Bootstrap your AWS Environment

If you've never used CDK in this AWS account and region before, you need to bootstrap it. This one-time command provisions the necessary resources for CDK to perform deployments.

```bash
cdk bootstrap
```

### 2. Install Dependencies

Navigate to the `cdk/` directory and install the required Python packages.

```bash
cd cdk
pip install -r requirements.txt
```

### 3. (Optional) Synthesize the CloudFormation Template

You can preview the AWS resources that the CDK will create by running `cdk synth`. This generates a CloudFormation template.

```bash
cdk synth
```

### 4. Deploy the Stack

Deploy the infrastructure to your AWS account. The CDK will build the Docker image, upload it to ECR, and provision all the AWS resources defined in the stack.

```bash
cdk deploy
```

The command will display progress and ask for confirmation before making changes. Once complete, it will output the CloudFront distribution's domain name, which is the public URL for your application.

### 5. Post-Deployment: Configure Secrets

The CDK stack expects several secrets to be present in AWS SSM Parameter Store for the backend application to function correctly. You must create these parameters in the same AWS region where you deployed the stack.

Create the following SSM Parameters of type `String`:

- `/artificial-u/test/ANTHROPIC_API_KEY`
- `/artificial-u/test/ELEVENLABS_API_KEY`
- `/artificial-u/test/GOOGLE_API_KEY`
- `/artificial-u/test/OPENAI_API_KEY`
- `/artificial-u/test/AUTH0_DOMAIN`
- `/artificial-u/test/AUTH0_AUDIENCE`

You can create them using the AWS Management Console or the AWS CLI:

```bash
aws ssm put-parameter --name "/artificial-u/test/OPENAI_API_KEY" --value "your-api-key" --type "String"
```

After setting the secrets, you may need to restart the ECS service for the new values to be injected into the running containers. You can do this from the ECS console by updating the service and forcing a new deployment.

---

## CI/CD Automation with GitHub Actions

This repository includes a GitHub Actions workflow file at `.github/workflows/deploy.yml` that automates the deployment process. On every push to the `prod` branch, the workflow will automatically build the frontend, build the container image, and deploy the CDK stack.

### CI/CD Prerequisites

To enable the workflow to securely authenticate with your AWS account, you need to:

1. **Configure an OIDC identity provider in AWS IAM.** This establishes a trust relationship between your AWS account and GitHub Actions. [Follow the official AWS guide for this one-time setup.](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html)

2. **Create an IAM Role for GitHub Actions.** This role will have the permissions necessary to deploy your CDK stack. Attach the `AdministratorAccess` policy for simplicity, or create a more fine-grained policy for production. The key is to configure the role's trust policy to allow GitHub's OIDC provider to assume it.

    **Example Trust Policy:**

    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Federated": "arn:aws:iam::YOUR_AWS_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
                },
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": "repo:your-github-org/your-repo-name:*"
                    }
                }
            }
        ]
    }
    ```

    Replace `YOUR_AWS_ACCOUNT_ID`, `your-github-org`, and `your-repo-name`.

3. **Create GitHub Secrets.** In your GitHub repository settings, go to `Secrets and variables` > `Actions` and create the following repository secrets:
   - `AWS_ROLE_ARN`: The ARN of the IAM role you just created
   - `VITE_AUTH0_DOMAIN`: Your Auth0 domain (e.g., `your-domain.auth0.com`)
   - `VITE_AUTH0_CLIENT_ID`: Your Auth0 application client ID
   - `VITE_AUTH0_AUDIENCE`: Your Auth0 API audience/identifier

Once these steps are complete, any push to `prod` will automatically trigger a deployment.

---

## Using a Custom Domain (e.g., artificial-u.com)

To associate your application with a custom domain, you need to perform a few manual steps after the initial deployment.

**Important Note on AWS Region**: To use an ACM certificate with CloudFront, the certificate must be created in the **us-east-1 (N. Virginia)** region. For simplicity, this guide assumes your entire CDK stack is deployed to `us-east-1`. Please ensure your AWS profile and CI/CD pipeline are configured for this region.

### 1. Deploy the Stack

Run `cdk deploy`. After a successful deployment, the CDK will output a list of nameservers. It will look something like this:

```txt
Outputs:
CdkStack.NameServers = ns-123.awsdns-01.com,ns-456.awsdns-02.net,ns-789.awsdns-03.org,ns-1011.awsdns-04.co.uk
```

### 2. Update Your Domain Registrar

Log in to your domain registrar (e.g., Hover, GoDaddy) and find the DNS management section for your domain. Change the existing nameservers to the four nameservers provided by the CDK output.

**Note**: DNS changes can take up to 48 hours to propagate across the internet, but it's often much faster.

Once the DNS changes have propagated, your website will be live at your custom domain, complete with HTTPS.

---

## Troubleshooting

### 502 Bad Gateway Errors

If you're experiencing 502 errors when accessing the API through CloudFront, follow these diagnostic steps:

#### 1. Check ECS Task Status

```bash
# List running tasks
aws ecs list-tasks --cluster <ClusterName> --service-name <ServiceName>

# Describe task to see status
aws ecs describe-tasks --cluster <ClusterName> --tasks <TaskArn>
```

Look for the `lastStatus` (should be `RUNNING`) and `healthStatus` (should be `HEALTHY`).

#### 2. View Container Logs

```bash
# View logs for the API service
aws logs tail /aws/ecs/<ServiceName> --follow

# Or use the ECS console to view logs for individual tasks
```

Common issues in logs:

- Database connection failures (check DB security groups)
- Missing environment variables or secrets
- Application startup errors

#### 3. Check ALB Target Health

```bash
# Get target group ARN
TG_ARN=$(aws elbv2 describe-target-groups \
  --query 'TargetGroups[?contains(TargetGroupName, `ApiService`)].TargetGroupArn' \
  --output text)

# Check target health
aws elbv2 describe-target-health --target-group-arn $TG_ARN
```

If targets are `unhealthy`, the health check is failing. Common causes:

- Container not listening on the expected port (8000)
- Health check path returning non-200 status
- Security group rules blocking ALB → ECS communication
- Application failing to start within the grace period

#### 4. Force New Deployment

After fixing configuration issues, force a new deployment to restart tasks:

```bash
aws ecs update-service --cluster <ClusterName> --service <ServiceName> --force-new-deployment
```

### Direct URL Access Returns 404

If accessing routes like `/professors` directly returns a 404 or shows an S3 error, the CloudFront custom error responses are not configured. This has been fixed in the latest CDK stack.

After deploying the fix, you may need to invalidate the CloudFront cache:

```bash
# Get distribution ID
DIST_ID=$(aws cloudfront list-distributions \
  --query 'DistributionList.Items[?Aliases.Items[?contains(@, `artificial-u.com`)]].Id' \
  --output text)

# Create invalidation
aws cloudfront create-invalidation \
  --distribution-id $DIST_ID \
  --paths "/*"
```

---

## Destroying the Stack

To tear down all the resources created by the CDK, run the following command from the `cdk/` directory. This is useful for cleaning up development or test environments.

```bash
cdk destroy
```

This will remove all the resources, including the database and S3 buckets, as they are configured with a `RemovalPolicy.DESTROY`.
