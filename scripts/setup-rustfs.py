#!/usr/bin/env python3
"""Setup RustFS local S3 server for Canvas Code Correction development.

This script:
1. Checks if RustFS is running (default localhost:9000, configurable via RUSTFS_ENDPOINT)
2. Creates 'test-assets' bucket if it doesn't exist (configurable via RUSTFS_BUCKET_NAME)
3. Uploads a test asset file for integration tests
4. Registers a Prefect S3 block named 'local-rustfs'

Configuration via environment variables:
- RUSTFS_ENDPOINT: S3 endpoint URL (default: http://localhost:9000)
- RUSTFS_ACCESS_KEY: Access key (default: rustfsadmin)
- RUSTFS_SECRET_KEY: Secret key (default: rustfsadmin)
- RUSTFS_BUCKET_NAME: Bucket name (default: test-assets)

Prerequisites:
- RustFS running (run 'uv run poe s3' in another terminal)
- Prefect server running (run 'uv run poe prefect' or docker-compose up)
"""

from __future__ import annotations

import os
import sys

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, EndpointConnectionError


def get_rustfs_config():
    """Return RustFS configuration from environment variables with defaults."""
    return {
        "endpoint_url": os.getenv("RUSTFS_ENDPOINT", "http://localhost:9000"),
        "aws_access_key_id": os.getenv("RUSTFS_ACCESS_KEY", "rustfsadmin"),
        "aws_secret_access_key": os.getenv("RUSTFS_SECRET_KEY", "rustfsadmin"),
        "bucket_name": os.getenv("RUSTFS_BUCKET_NAME", "test-assets"),
        "prefix": os.getenv("RUSTFS_PREFIX", "dev"),
    }


def check_rustfs_available() -> bool:
    """Check if RustFS S3 endpoint is reachable."""
    config = get_rustfs_config()
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=config["endpoint_url"],
            aws_access_key_id=config["aws_access_key_id"],
            aws_secret_access_key=config["aws_secret_access_key"],
            config=Config(signature_version="s3v4"),
        )
        s3.list_buckets()
        print(f"✓ RustFS is reachable at {config['endpoint_url']}")
        return True
    except (EndpointConnectionError, ClientError) as e:
        print(f"✗ RustFS not reachable: {e}")
        print("  Start RustFS with: uv run poe s3")
        print(f"  Configure endpoint via RUSTFS_ENDPOINT (current: {config['endpoint_url']})")
        return False


def ensure_bucket_exists(bucket_name: str) -> bool:
    """Create bucket if it doesn't exist."""
    config = get_rustfs_config()
    s3 = boto3.client(
        "s3",
        endpoint_url=config["endpoint_url"],
        aws_access_key_id=config["aws_access_key_id"],
        aws_secret_access_key=config["aws_secret_access_key"],
        config=Config(signature_version="s3v4"),
    )
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"✓ Bucket '{bucket_name}' already exists")
        return True
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            try:
                s3.create_bucket(Bucket=bucket_name)
                print(f"✓ Created bucket '{bucket_name}'")
                return True
            except ClientError as create_err:
                print(f"✗ Failed to create bucket: {create_err}")
                return False
        else:
            print(f"✗ Error checking bucket: {e}")
            return False


def upload_test_asset(bucket_name: str, prefix: str = "dev") -> None:
    """Upload a test asset file for integration tests."""
    config = get_rustfs_config()
    s3 = boto3.client(
        "s3",
        endpoint_url=config["endpoint_url"],
        aws_access_key_id=config["aws_access_key_id"],
        aws_secret_access_key=config["aws_secret_access_key"],
        config=Config(signature_version="s3v4"),
    )

    test_content = b"# Test grader asset\n# This file is used for integration tests\n"
    key = f"{prefix}/test.txt" if prefix else "test.txt"

    try:
        s3.put_object(Bucket=bucket_name, Key=key, Body=test_content)
        print(f"✓ Uploaded test asset to '{bucket_name}/{key}'")
    except ClientError as e:
        print(f"✗ Failed to upload test asset: {e}")


def register_prefect_block() -> bool:
    """Register Prefect S3 block for local RustFS."""
    try:
        from prefect.blocks.core import Block
        from prefect_aws import AwsClientParameters, AwsCredentials, S3Bucket
        from pydantic import SecretStr

        # Check if block already exists
        try:
            block = S3Bucket.load("local-rustfs")
            print("✓ Prefect S3 block 'local-rustfs' already exists")
            return True
        except ValueError:
            # Block doesn't exist, create it
            pass

        config = get_rustfs_config()
        # Create AwsCredentials with endpoint_url in aws_client_parameters
        credentials = AwsCredentials(
            aws_access_key_id=config["aws_access_key_id"],
            aws_secret_access_key=SecretStr(config["aws_secret_access_key"]),
            region_name="us-east-1",
            aws_client_parameters=AwsClientParameters(
                endpoint_url=config["endpoint_url"],
            ),
        )

        block = S3Bucket(
            bucket_name=config["bucket_name"],
            credentials=credentials,
        )
        block.save("local-rustfs", overwrite=True)
        print(f"✓ Registered Prefect S3 block 'local-rustfs' for bucket {config['bucket_name']}")
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
    prefect_api_url = os.getenv("PREFECT_API_URL", "http://localhost:4200/api")
    try:
        import httpx

        response = httpx.get(f"{prefect_api_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"✓ Prefect server is reachable at {prefect_api_url}")
            return True
        else:
            print(f"✗ Prefect server returned status {response.status_code}")
            return False
    except ImportError:
        print("⚠ Could not check Prefect server (httpx not available)")
        return True  # Continue anyway
    except Exception as e:
        print(f"✗ Prefect server not reachable: {e}")
        print("  Start Prefect server with: uv run poe prefect")
        print("  Or set PREFECT_API_URL environment variable")
        return False


def main() -> int:
    print("Setting up RustFS for Canvas Code Correction development")
    print("=" * 60)

    # Check prerequisites
    if not check_rustfs_available():
        return 1

    if not check_prefect_server():
        print("⚠ Continuing without Prefect server check...")

    # Get configuration
    config = get_rustfs_config()
    bucket_name = config["bucket_name"]
    prefix = config["prefix"]

    # Setup S3 bucket
    if not ensure_bucket_exists(bucket_name):
        return 1

    # Upload test asset
    upload_test_asset(bucket_name, prefix=prefix)

    # Register Prefect block
    if not register_prefect_block():
        print("⚠ Failed to register Prefect block")
        print("  You can register it manually with:")
        print("  prefect block register -f scripts/rustfs-s3-block.yaml")
        print("  Or create block via Prefect UI at http://localhost:4200")

    print("=" * 60)
    print("Setup complete!")
    print("\nNext steps:")
    print("1. Run integration tests: uv run pytest -m integration")
    print("2. Configure a course: uv run ccc configure-course <course-slug> \\")
    print(f"   --assets-block local-rustfs --s3-prefix {prefix}")
    print("3. Run correction flow: uv run ccc run-once <assignment-id>")

    return 0


if __name__ == "__main__":
    sys.exit(main())
