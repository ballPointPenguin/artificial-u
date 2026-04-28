"""
Shared boto3 client/session helpers.

boto3 client construction loads service models and credential providers, so keep
clients process-local and reusable instead of rebuilding them per service instance.
"""

from functools import lru_cache
from typing import Any, Optional

import boto3
from botocore.client import Config


@lru_cache(maxsize=8)
def get_boto3_session(
    *,
    region_name: Optional[str],
    aws_access_key_id: Optional[str],
    aws_secret_access_key: Optional[str],
) -> Any:
    kwargs = {"region_name": region_name}
    if aws_access_key_id and aws_secret_access_key:
        kwargs["aws_access_key_id"] = aws_access_key_id
        kwargs["aws_secret_access_key"] = aws_secret_access_key
    return boto3.session.Session(**kwargs)


@lru_cache(maxsize=16)
def get_s3_client(
    *,
    endpoint_url: Optional[str],
    region_name: Optional[str],
    aws_access_key_id: Optional[str],
    aws_secret_access_key: Optional[str],
    signature_version: Optional[str],
) -> Any:
    session = get_boto3_session(
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )

    kwargs = {
        "region_name": region_name,
    }
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    if signature_version:
        kwargs["config"] = Config(signature_version=signature_version)

    return session.client("s3", **kwargs)


@lru_cache(maxsize=4)
def get_cloudwatch_client(*, region_name: Optional[str]) -> Any:
    session = get_boto3_session(
        region_name=region_name,
        aws_access_key_id=None,
        aws_secret_access_key=None,
    )
    return session.client("cloudwatch", region_name=region_name)
