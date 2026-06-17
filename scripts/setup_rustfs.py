#!/usr/bin/env python3
"""Setup RustFS local S3 server for Canvas Code Correction development.

This script:
1. Checks if RustFS is running (default local endpoint, configurable via RUSTFS_ENDPOINT)
2. Creates 'test-assets' bucket if it doesn't exist (configurable via RUSTFS_BUCKET_NAME)
3. Uploads a test asset file for integration tests
4. Optionally registers a Prefect S3 block named 'local-rustfs' when Prefect is available

Configuration via environment variables:
- RUSTFS_ENDPOINT: S3 endpoint URL (default: local RustFS endpoint)
- RUSTFS_ACCESS_KEY: Access key (default: rustfsadmin)
- RUSTFS_SECRET_KEY: Secret key (default: rustfsadmin)
- RUSTFS_BUCKET_NAME: Bucket name (default: test-assets)

Prerequisites:
- RustFS running (run 'uv run poe s3' in another terminal)
- Prefect server running (run 'uv run poe prefect' or docker-compose up)
"""

import os
import sys
from typing import NamedTuple
from urllib.parse import urlunparse

import boto3
import requests
from botocore.client import Config
from botocore.exceptions import ClientError, EndpointConnectionError

LOCAL_HOST = "localhost"
LOCAL_SCHEME = "http"
DEFAULT_RUSTFS_PORT = "9000"
DEFAULT_PREFECT_PORT = "4200"


def _build_local_url(host: str, port: str, path: str = "") -> str:
    clean_path = path if not path or path.startswith("/") else f"/{path}"
    return urlunparse((LOCAL_SCHEME, f"{host}:{port}", clean_path, "", "", ""))


class RustfsConfig(NamedTuple):
    endpoint_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
    bucket_name: str
    prefix: str


def _default_rustfs_endpoint() -> str:
    host = os.getenv("RUSTFS_HOST", LOCAL_HOST)
    port = os.getenv("RUSTFS_PORT", DEFAULT_RUSTFS_PORT)
    return _build_local_url(host, port)


def _default_prefect_api_url() -> str:
    host = os.getenv("PREFECT_HOST", LOCAL_HOST)
    port = os.getenv("PREFECT_PORT", DEFAULT_PREFECT_PORT)
    return _build_local_url(host, port, "/api")


def get_rustfs_config() -> RustfsConfig:
    """Return RustFS configuration from environment variables with defaults."""
    return RustfsConfig(
        endpoint_url=os.getenv("RUSTFS_ENDPOINT", _default_rustfs_endpoint()),
        aws_access_key_id=os.getenv("RUSTFS_ACCESS_KEY", "rustfsadmin"),
        aws_secret_access_key=os.getenv("RUSTFS_SECRET_KEY", "rustfsadmin"),
        bucket_name=os.getenv("RUSTFS_BUCKET_NAME", "test-assets"),
        prefix=os.getenv("RUSTFS_PREFIX", "dev"),
    )


def get_bucket_owner_kwargs(endpoint_url: str) -> dict[str, str]:
    """Return ExpectedBucketOwner parameter if endpoint is AWS and owner is configured."""
    bucket_owner = os.getenv("AWS_BUCKET_OWNER")
    if bucket_owner and "amazonaws.com" in endpoint_url:
        return {"ExpectedBucketOwner": bucket_owner}
    return {}


def check_rustfs_available() -> bool:
    """Check if RustFS S3 endpoint is reachable."""
    config = get_rustfs_config()
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=config.endpoint_url,
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
            config=Config(signature_version="s3v4"),
        )
        s3.list_buckets()
        print(f"✓ RustFS is reachable at {config.endpoint_url}")
        return True
    except (EndpointConnectionError, ClientError) as e:
        print(f"✗ RustFS not reachable: {e}")
        print("  Start RustFS with: uv run poe s3")
        print(f"  Configure endpoint via RUSTFS_ENDPOINT (current: {config.endpoint_url})")
        return False


def ensure_bucket_exists(bucket_name: str) -> bool:
    """Create bucket if it doesn't exist."""
    config = get_rustfs_config()
    bucket_owner_kwargs = get_bucket_owner_kwargs(config.endpoint_url)
    s3 = boto3.client(
        "s3",
        endpoint_url=config.endpoint_url,
        aws_access_key_id=config.aws_access_key_id,
        aws_secret_access_key=config.aws_secret_access_key,
        config=Config(signature_version="s3v4"),
    )
    try:
        s3.head_bucket(Bucket=bucket_name, **bucket_owner_kwargs)
        print(f"✓ Bucket '{bucket_name}' already exists")
        return True
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            try:
                s3.create_bucket(Bucket=bucket_name, **bucket_owner_kwargs)
                print(f"✓ Created bucket '{bucket_name}'")
                return True
            except ClientError as create_err:
                print(f"✗ Failed to create bucket: {create_err}")
                return False
        else:
            print(f"✗ Error checking bucket: {e}")
            return False


def upload_test_asset(bucket_name: str, prefix: str = "dev") -> bool:
    """Upload a test asset file for integration tests."""
    config = get_rustfs_config()
    bucket_owner_kwargs = get_bucket_owner_kwargs(config.endpoint_url)
    s3 = boto3.client(
        "s3",
        endpoint_url=config.endpoint_url,
        aws_access_key_id=config.aws_access_key_id,
        aws_secret_access_key=config.aws_secret_access_key,
        config=Config(signature_version="s3v4"),
    )

    test_content = b"# Test grader asset\n# This file is used for integration tests\n"
    key = f"{prefix}/test.txt" if prefix else "test.txt"

    try:
        s3.put_object(Bucket=bucket_name, Key=key, Body=test_content, **bucket_owner_kwargs)
        print(f"✓ Uploaded test asset to '{bucket_name}/{key}'")
        return True
    except ClientError as e:
        print(f"✗ Failed to upload test asset: {e}")
        return False


def register_prefect_block() -> bool:
    """Register Prefect S3 block for local RustFS."""
    try:
        from prefect.blocks.core import Block
        from prefect_aws import AwsClientParameters, AwsCredentials, S3Bucket
        from pydantic import SecretStr

        try:
            block = S3Bucket.load("local-rustfs")
            print("✓ Prefect S3 block 'local-rustfs' already exists")
            return True
        except ValueError:
            block = None

        if block is not None:
            return True

        config = get_rustfs_config()
        credentials = AwsCredentials(
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=SecretStr(config.aws_secret_access_key),
            region_name="us-east-1",
            aws_client_parameters=AwsClientParameters(
                endpoint_url=config.endpoint_url,
            ),
        )

        block = S3Bucket(
            bucket_name=config.bucket_name,
            credentials=credentials,
        )
        block.save("local-rustfs", overwrite=True)
        print(f"✓ Registered Prefect S3 block 'local-rustfs' for bucket {config.bucket_name}")
        return True
    except ImportError as e:
        print(f"✗ Failed to import Prefect modules: {e}")
        print("  Ensure prefect and prefect-aws are installed")
        return False
    except Exception as e:
        print(f"✗ Failed to register Prefect block: {e}")
        return False


def check_prefect_server() -> bool:
    """Check if Prefect server is accessible."""
    prefect_api_url = os.getenv("PREFECT_API_URL", _default_prefect_api_url())
    prefect_ui_url = prefect_api_url.removesuffix("/api")
    try:
        response = requests.get(f"{prefect_api_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"✓ Prefect server is reachable at {prefect_api_url}")
            return True
        print(f"✗ Prefect server returned status {response.status_code}")
        return False
    except requests.RequestException as e:
        print(f"✗ Prefect server not reachable: {e}")
        print("  Start Prefect server with: uv run poe prefect")
        print(f"  Or open {prefect_ui_url} and confirm the API at {prefect_api_url}")
        return False


def main() -> int:
    print("Setting up RustFS for Canvas Code Correction development")
    print("=" * 60)

    if not check_rustfs_available():
        return 1

    if not check_prefect_server():
        print("⚠ Continuing without Prefect server check...")

    config = get_rustfs_config()
    bucket_name = config.bucket_name
    prefix = config.prefix

    if not ensure_bucket_exists(bucket_name):
        return 1

    if not upload_test_asset(bucket_name, prefix=prefix):
        print("✗ Setup incomplete: failed to upload the integration test asset")
        return 1

    prefect_block_registered = register_prefect_block()
    if not prefect_block_registered:
        print("⚠ Failed to register Prefect block")
        print("  You can register it manually with:")
        print("  prefect block register -f scripts/rustfs-s3-block.yaml")
        print(
            f"  Or create block via Prefect UI at {_build_local_url(LOCAL_HOST, DEFAULT_PREFECT_PORT)}"
        )

    print("=" * 60)
    if prefect_block_registered:
        print("Setup complete!")
    else:
        print("RustFS setup complete, but Prefect block registration still needs manual follow-up.")
    print("\nNext steps:")
    print("1. Run integration tests: uv run pytest -m integration")
    print("2. Configure a course: uv run ccc course setup")
    print("3. Run correction flow: uv run ccc course run <assignment-id> --course <block>")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
