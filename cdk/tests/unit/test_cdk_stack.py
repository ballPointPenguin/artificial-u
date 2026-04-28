import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk.cdk_stack import CdkStack


def test_stack_synthesizes():
    """Test that the stack synthesizes successfully."""
    app = core.App()
    stack = CdkStack(app, "cdk")
    template = assertions.Template.from_stack(stack)

    # Assert that critical resources exist
    template.resource_count_is("AWS::EC2::VPC", 1)
    template.resource_count_is("AWS::ECS::Cluster", 1)
    template.resource_count_is("AWS::RDS::DBInstance", 1)
    template.resource_count_is("AWS::S3::Bucket", 6)  # 5 app buckets + 1 frontend bucket
    template.resource_count_is("AWS::CloudFront::Distribution", 1)
    template.resource_count_is("AWS::WAFv2::WebACL", 1)
    template.resource_count_is("AWS::Route53::HostedZone", 1)
    template.resource_count_is("AWS::EC2::VpcEndpoint", 0)  # Verify we're using public endpoints
