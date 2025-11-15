import aws_cdk as cdk
from aws_cdk import (
    RemovalPolicy,
    Stack,
)
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_iam as iam
from aws_cdk import aws_rds as rds
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_route53_targets as route53_targets
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3_deployment
from aws_cdk import aws_ssm as ssm
from constructs import Construct


class CdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        domain_name = "artificial-u.com"
        site_domain = f"www.{domain_name}"

        # 1. Create Route 53 Hosted Zone to manage the domain
        hosted_zone = route53.PublicHostedZone(self, "HostedZone", zone_name=domain_name)

        # 2. Create ACM Certificate for the custom domain
        # Note: For CloudFront, the certificate must be in the us-east-1 region.
        # This stack must be deployed to us-east-1 to work correctly.
        certificate = acm.Certificate(
            self,
            "SiteCertificate",
            domain_name=domain_name,
            subject_alternative_names=[site_domain],
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        # 1. Create the VPC for our infrastructure
        vpc = ec2.Vpc(self, "Vpc", max_azs=2)

        # 1b. Create a Bastion host for secure RDS access via Systems Manager Session Manager
        bastion = ec2.BastionHostLinux(
            self,
            "Bastion",
            vpc=vpc,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T4G, ec2.InstanceSize.MICRO),
            machine_image=ec2.AmazonLinuxImage(
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2023,
                cpu_type=ec2.AmazonLinuxCpuType.ARM_64,
            ),
        )

        # 2. Create the ECS Cluster to host our services
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        # 3. Create the RDS PostgreSQL Database
        db_cluster = rds.DatabaseInstance(
            self,
            "Database",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_17_6),
            vpc=vpc,
            database_name="artificial_u",
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE4_GRAVITON, ec2.InstanceSize.SMALL
            ),
            # Create final backup before deletion
            removal_policy=RemovalPolicy.SNAPSHOT,
            # Required for this instance class
            allocated_storage=20,
        )

        # 4. Create S3 Buckets for application storage (replacing MinIO)
        # Audio, lectures, and images buckets are publicly readable for web interface
        audio_bucket = s3.Bucket(
            self,
            "AudioBucket",
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
        )
        lectures_bucket = s3.Bucket(
            self,
            "LecturesBucket",
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
        )
        images_bucket = s3.Bucket(
            self,
            "ImagesBucket",
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
        )
        exports_bucket = s3.Bucket(
            self,
            "ExportsBucket",
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
        )
        content_logs_bucket = s3.Bucket(
            self,
            "ContentLogsBucket",
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
        )

        # 5. Define the Docker image from the local Dockerfile for the API
        api_image = ecr_assets.DockerImageAsset(
            self,
            "ApiImage",
            directory="..",  # Build context is now the repo root
            file="Dockerfile.api",
            platform=ecr_assets.Platform.LINUX_AMD64,
        )

        # Define application secrets to be fetched from SSM Parameter Store
        app_secrets = {
            "ANTHROPIC_API_KEY": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self, "AnthropicApiKey", "/artificial-u/prod/ANTHROPIC_API_KEY"
                )
            ),
            "ELEVENLABS_API_KEY": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self, "ElevenLabsApiKey", "/artificial-u/prod/ELEVENLABS_API_KEY"
                )
            ),
            "GOOGLE_API_KEY": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self, "GoogleApiKey", "/artificial-u/prod/GOOGLE_API_KEY"
                )
            ),
            "OPENAI_API_KEY": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self, "OpenAiApiKey", "/artificial-u/prod/OPENAI_API_KEY"
                )
            ),
            "AUTH0_DOMAIN": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self, "Auth0Domain", "/artificial-u/prod/AUTH0_DOMAIN"
                )
            ),
            "AUTH0_AUDIENCE": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self, "Auth0Audience", "/artificial-u/prod/AUTH0_AUDIENCE"
                )
            ),
            # Pass DB connection details as individual secrets
            "DB_HOST": ecs.Secret.from_secrets_manager(db_cluster.secret, "host"),
            "DB_PORT": ecs.Secret.from_secrets_manager(db_cluster.secret, "port"),
            "DB_USER": ecs.Secret.from_secrets_manager(db_cluster.secret, "username"),
            "DB_PASSWORD": ecs.Secret.from_secrets_manager(db_cluster.secret, "password"),
            "DB_NAME": ecs.Secret.from_secrets_manager(db_cluster.secret, "dbname"),
        }

        # Environment variables for the API container
        app_environment = {
            "AUTH0_ALG": "RS256",
            "COURSE_GENERATION_MODEL": "gpt-5-nano",
            "DEPARTMENT_GENERATION_MODEL": "gpt-5-nano",
            "ENV": "production",
            "GUNICORN_THREADS": "8",
            "GUNICORN_TIMEOUT": "120",
            "GUNICORN_WORKERS": "2",
            "IMAGE_GENERATION_MODEL": "imagen-4.0-generate-001",
            "LECTURE_GENERATION_MODEL": "claude-sonnet-4-5-20250929",
            "LECTURE_SUMMARY_MODEL": "gpt-5-nano",
            "LOG_LEVEL": "INFO",
            "PROFESSOR_GENERATION_MODEL": "gpt-5-nano",
            "STORAGE_TYPE": "s3",
            "TOPICS_GENERATION_MODEL": "gemini-2.5-flash",
            "TTS_VOICE_MODEL": "eleven_flash_v2_5",
            "STORAGE_AUDIO_BUCKET": audio_bucket.bucket_name,
            "STORAGE_IMAGES_BUCKET": images_bucket.bucket_name,
            "STORAGE_LECTURES_BUCKET": lectures_bucket.bucket_name,
            "STORAGE_EXPORTS_BUCKET": exports_bucket.bucket_name,
            "STORAGE_CONTENT_LOGS_BUCKET": content_logs_bucket.bucket_name,
            "STORAGE_REGION": self.region,
            "CORS_ORIGINS": f"https://{domain_name},https://{site_domain}",
        }

        # 6. Create the Fargate Service with a public Load Balancer
        # Note: The ALB needs to be internet-facing for CloudFront to reach it
        # CloudFront cannot connect to internal (VPC-only) load balancers
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "ApiService",
            cluster=cluster,
            cpu=1024,
            memory_limit_mib=2048,
            desired_count=1,
            task_image_options={
                "image": ecs.ContainerImage.from_docker_image_asset(api_image),
                "container_port": 8000,
                "secrets": app_secrets,
                "environment": app_environment,
            },
            public_load_balancer=True,  # Must be public for CloudFront to reach it
            listener_port=80,
            health_check_grace_period=cdk.Duration.seconds(300),
        )

        # 7. Configure Health Check for the API service
        fargate_service.target_group.configure_health_check(
            path="/api/v1/health",
            port="traffic-port",  # Use the same port as the target receives traffic on
            timeout=cdk.Duration.seconds(30),
            healthy_threshold_count=2,
            unhealthy_threshold_count=3,
            interval=cdk.Duration.seconds(60),
        )

        # 8. Grant permissions
        # - Allow the bastion host to connect to the database
        db_cluster.connections.allow_default_port_from(bastion, "Bastion to RDS")
        # - Allow the service to connect to the database
        db_cluster.connections.allow_default_port_from(
            fargate_service.service, "API to DB connection"
        )
        # - Grant S3 read/write permissions to the task role
        s3_policy = iam.PolicyStatement(
            actions=["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"],
            resources=[
                audio_bucket.bucket_arn,
                f"{audio_bucket.bucket_arn}/*",
                lectures_bucket.bucket_arn,
                f"{lectures_bucket.bucket_arn}/*",
                images_bucket.bucket_arn,
                f"{images_bucket.bucket_arn}/*",
                exports_bucket.bucket_arn,
                f"{exports_bucket.bucket_arn}/*",
                content_logs_bucket.bucket_arn,
                f"{content_logs_bucket.bucket_arn}/*",
            ],
        )
        fargate_service.task_definition.add_to_task_role_policy(s3_policy)

        # --- Frontend Infrastructure ---

        # 9. Create S3 bucket for the frontend static assets
        frontend_bucket = s3.Bucket(
            self,
            "FrontendBucket",
            # The bucket is private. CloudFront will access it via Origin Access Identity.
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
        )

        # 10. (removed) Origin Access Identity is now created automatically by S3BucketOrigin

        # 11. (moved below) Deploy frontend assets after the CloudFront distribution is created

        # 12. Create a CloudFront distribution
        distribution = cloudfront.Distribution(
            self,
            "Distribution",
            certificate=certificate,
            domain_names=[domain_name, site_domain],
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_identity(frontend_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            # Route API calls to the internal ALB
            additional_behaviors={
                "/api/*": cloudfront.BehaviorOptions(
                    origin=origins.LoadBalancerV2Origin(
                        fargate_service.load_balancer,
                        protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
                    ),
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
                    # Forward headers, cookies, etc. needed by the API
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER,
                )
            },
            default_root_object="index.html",
            # Custom error response for SPA routing
            # When S3 returns 404 (e.g., for /professors), serve index.html instead
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=cdk.Duration.seconds(0),
                ),
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=cdk.Duration.seconds(0),
                ),
            ],
        )

        # 11 (cont.). Deploy the frontend assets and invalidate CloudFront
        # Split deployment so that assets can be cached long-term while index.html stays non-cacheable
        s3_deployment.BucketDeployment(
            self,
            "DeployWebAppAssets",
            sources=[
                s3_deployment.Source.asset(
                    "../web/dist",
                    exclude=["index.html"],
                )
            ],
            destination_bucket=frontend_bucket,
            prune=False,  # Don't prune to avoid removing index.html
            distribution=distribution,
            distribution_paths=["/assets/*", "/favicon.ico"],
            cache_control=[
                s3_deployment.CacheControl.from_string("public,max-age=31536000,immutable"),
            ],
        )

        s3_deployment.BucketDeployment(
            self,
            "DeployWebAppIndex",
            sources=[
                s3_deployment.Source.asset(
                    "../web/dist",
                    exclude=["assets", "favicon.ico"],
                )
            ],
            destination_bucket=frontend_bucket,
            prune=False,  # Don't prune to avoid removing assets
            distribution=distribution,
            distribution_paths=[
                "/",
                "/index.html",
                "/sw.js",  # Service worker must be invalidated for PWA updates
                "/workbox-*.js",  # Workbox runtime files
                "/manifest.json",  # PWA manifest
                "/registerSW.js",  # SW registration script (if generated)
            ],
            cache_control=[
                s3_deployment.CacheControl.from_string("no-cache, no-store, must-revalidate"),
            ],
        )

        # 13. Create Route 53 records to point the domain to CloudFront
        route53.ARecord(
            self,
            "SiteAliasRecord",
            zone=hosted_zone,
            record_name=domain_name,
            target=route53.RecordTarget.from_alias(route53_targets.CloudFrontTarget(distribution)),
        )
        route53.ARecord(
            self,
            "WwwSiteAliasRecord",
            zone=hosted_zone,
            record_name=site_domain,
            target=route53.RecordTarget.from_alias(route53_targets.CloudFrontTarget(distribution)),
        )

        # 14. Output the nameservers to be configured in the domain registrar
        cdk.CfnOutput(
            self,
            "NameServers",
            value=cdk.Fn.join(",", hosted_zone.hosted_zone_name_servers),
            description="Name servers for the hosted zone. Update these at your domain registrar (Hover).",
        )

        # 15. Output the bastion instance ID for database access
        cdk.CfnOutput(
            self,
            "BastionInstanceId",
            value=bastion.instance_id,
            description=(
                "Bastion host instance ID for secure RDS access via Session Manager. "
                "Use ./scripts/db-tunnel.sh to connect."
            ),
        )
        cdk.CfnOutput(
            self,
            "DatabaseEndpoint",
            value=db_cluster.db_instance_endpoint_address,
            description="RDS database endpoint (used by db-tunnel.sh).",
        )
