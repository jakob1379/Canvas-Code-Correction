"""Pytest fixtures for end-to-end tests with docker-compose services."""

import os

import boto3
import pytest
import requests
from botocore.client import Config
from botocore.exceptions import ClientError, EndpointConnectionError
from prefect.client.orchestration import get_client
from requests.exceptions import RequestException


def is_rustfs_available() -> bool:
    """Check if RustFS S3 endpoint is reachable."""
    endpoint = os.getenv("RUSTFS_ENDPOINT", "http://localhost:9000")
    access_key = os.getenv("RUSTFS_ACCESS_KEY", "rustfsadmin")
    secret_key = os.getenv("RUSTFS_SECRET_KEY", "rustfsadmin")
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
        )
        s3.list_buckets()
        return True
    except (EndpointConnectionError, ClientError):
        return False


def is_prefect_server_available() -> bool:
    """Check if Prefect server is reachable."""
    prefect_api_url = os.getenv("PREFECT_API_URL", "http://localhost:4200/api")
    try:
        response = requests.get(f"{prefect_api_url}/health", timeout=5)
        return response.status_code == 200
    except RequestException:
        return False


@pytest.fixture(scope="session")
def rustfs_config() -> dict[str, str]:
    """Return RustFS configuration from environment variables."""
    return {
        "endpoint_url": os.getenv("RUSTFS_ENDPOINT", "http://localhost:9000"),
        "aws_access_key_id": os.getenv("RUSTFS_ACCESS_KEY", "rustfsadmin"),
        "aws_secret_access_key": os.getenv("RUSTFS_SECRET_KEY", "rustfsadmin"),
        "bucket_name": os.getenv("RUSTFS_BUCKET_NAME", "test-assets"),
        "prefix": os.getenv("RUSTFS_PREFIX", "dev"),
    }


@pytest.fixture(scope="session")
def rustfs_available(rustfs_config: dict[str, str]) -> bool:
    """Check if RustFS is available, skip test if not."""
    if not is_rustfs_available():
        pytest.skip("RustFS not available")
    return True


@pytest.fixture(scope="session")
def prefect_server_available() -> bool:
    """Check if Prefect server is available, skip test if not."""
    if not is_prefect_server_available():
        pytest.skip("Prefect server not available")
    return True


@pytest.fixture(scope="session")
def prefect_client(prefect_server_available: bool):
    """Get Prefect client configured for the local server."""
    client = get_client()
    return client


@pytest.fixture(scope="session")
def ensure_local_rustfs_block(
    prefect_server_available: bool,
    rustfs_config: dict[str, str],
):
    """Ensure the local RustFS Prefect block exists."""
    from prefect_aws import AwsClientParameters, AwsCredentials, S3Bucket
    from pydantic import SecretStr

    try:
        S3Bucket.load("local-rustfs")
        return True
    except ValueError:
        pass

    credentials = AwsCredentials(
        aws_access_key_id=rustfs_config["aws_access_key_id"],
        aws_secret_access_key=SecretStr(rustfs_config["aws_secret_access_key"]),
        region_name="us-east-1",
        aws_client_parameters=AwsClientParameters(endpoint_url=rustfs_config["endpoint_url"]),
    )
    block = S3Bucket(bucket_name=rustfs_config["bucket_name"], credentials=credentials)
    block.save("local-rustfs", overwrite=True)
    return True


@pytest.fixture(scope="session")
def s3_client(rustfs_config: dict[str, str], rustfs_available: bool):
    """Get boto3 S3 client configured for RustFS."""
    client = boto3.client(
        "s3",
        endpoint_url=rustfs_config["endpoint_url"],
        aws_access_key_id=rustfs_config["aws_access_key_id"],
        aws_secret_access_key=rustfs_config["aws_secret_access_key"],
        config=Config(signature_version="s3v4"),
    )
    return client


@pytest.fixture(scope="session")
def ensure_test_bucket(s3_client, rustfs_config: dict[str, str]) -> str:
    """Ensure test bucket exists and return bucket name."""
    bucket_name = rustfs_config["bucket_name"]
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            s3_client.create_bucket(Bucket=bucket_name)
    return bucket_name
