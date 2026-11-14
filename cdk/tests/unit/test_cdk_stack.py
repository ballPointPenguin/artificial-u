import aws_cdk as core
import aws_cdk.assertions as assertions
import pytest

from cdk.cdk_stack import CdkStack


@pytest.fixture(scope="module")
def template():
    """Synthesize the stack offline.

    The stack does context lookups, which need an account and region; placeholder values
    are enough because lookups return dummy data when nothing is deployed.
    """
    app = core.App()
    stack = CdkStack(app, "cdk", env=core.Environment(account="123456789012", region="us-east-1"))
    return assertions.Template.from_stack(stack)


def test_stack_synthesizes(template):
    """Test that the stack synthesizes successfully."""
    # Assert that critical resources exist
    template.resource_count_is("AWS::EC2::VPC", 1)
    template.resource_count_is("AWS::ECS::Cluster", 1)
    template.resource_count_is("AWS::RDS::DBInstance", 1)
    template.resource_count_is("AWS::S3::Bucket", 6)  # 5 app buckets + 1 frontend bucket
    template.resource_count_is("AWS::CloudFront::Distribution", 1)
    template.resource_count_is("AWS::WAFv2::WebACL", 1)
    template.resource_count_is("AWS::Route53::HostedZone", 1)
    template.resource_count_is("AWS::EC2::VpcEndpoint", 0)  # Verify we're using public endpoints


def _distribution_config(template):
    distributions = template.find_resources("AWS::CloudFront::Distribution")
    return next(iter(distributions.values()))["Properties"]["DistributionConfig"]


def test_api_errors_are_not_rewritten_to_the_spa_shell(template):
    """No distribution-wide error responses: they would turn API 403/404s into index.html."""
    assert "CustomErrorResponses" not in _distribution_config(template)


def test_spa_fallback_runs_only_on_the_frontend_behavior(template):
    config = _distribution_config(template)
    template.resource_count_is("AWS::CloudFront::Function", 1)

    default_events = [
        association["EventType"]
        for association in config["DefaultCacheBehavior"].get("FunctionAssociations", [])
    ]
    assert default_events == ["viewer-request"]

    # API, share pages and PWA files must reach their origin with the path unchanged
    with_functions = [
        behavior["PathPattern"]
        for behavior in config["CacheBehaviors"]
        if behavior.get("FunctionAssociations")
    ]
    assert with_functions == []
