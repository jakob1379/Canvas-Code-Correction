"""Shared fixtures for integration tests."""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import boto3
import pytest
import requests
from botocore.client import Config
from botocore.exceptions import ClientError, EndpointConnectionError

_MOCK_BUCKET = None  # global reference for debugging


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
    except Exception:
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


@pytest.fixture(autouse=True)
def clean_bucket(s3_client, rustfs_config: dict[str, str], ensure_test_bucket: str):
    """Delete all objects in the test bucket before each test."""
    bucket_name = ensure_test_bucket
    # List all objects
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    if "Contents" in response:
        objects = [{"Key": obj["Key"]} for obj in response["Contents"]]
        if objects:
            s3_client.delete_objects(Bucket=bucket_name, Delete={"Objects": objects})
    # Optionally clean up after test as well


@pytest.fixture(autouse=True)
def mock_s3bucket_load(rustfs_config: dict[str, str], s3_client) -> Iterator[None]:  # noqa: C901
    """Mock S3Bucket.load to return a mock bucket that downloads from test RustFS."""
    global _MOCK_BUCKET  # noqa: PLW0603
    bucket_name = rustfs_config["bucket_name"]

    # Create a mock bucket with get_directory method that uses s3_client
    class NoDownloadFolderMock(Mock):
        def __getattr__(self, name: str) -> Any:  # noqa: ANN401
            if name == "download_folder":
                msg = f"'{self.__class__.__name__}' object has no attribute '{name}'"
                raise AttributeError(msg)
            return super().__getattr__(name)

    mock_bucket = NoDownloadFolderMock()
    mock_bucket.bucket_name = bucket_name

    def get_directory_side_effect(local_path: str, from_path: str = "") -> None:
        print(
            f"DEBUG GET_DIRECTORY CALLED: bucket={bucket_name}, "
            f"from_path={from_path!r}, local_path={local_path}",
            file=sys.stderr,
        )
        # Actually download files
        local_path_obj = Path(local_path)
        local_path_obj.mkdir(parents=True, exist_ok=True)
        prefix = from_path.rstrip("/")
        if prefix:
            prefix += "/"
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if "Contents" in response:
            for obj in response["Contents"]:
                key = obj["Key"]
                if key.endswith("/"):
                    continue
                relative_key = key[len(prefix) :] if prefix and key.startswith(prefix) else key
                if not relative_key:
                    continue
                local_file = local_path_obj / relative_key
                local_file.parent.mkdir(parents=True, exist_ok=True)
                s3_client.download_file(bucket_name, key, str(local_file))

    mock_bucket.get_directory = Mock(side_effect=get_directory_side_effect)

    _MOCK_BUCKET = mock_bucket  # store for debugging

    with patch("canvas_code_correction.workspace.S3Bucket.load") as mock_load:

        def load_side_effect(block_name: str) -> Mock:
            print(
                f"DEBUG: S3Bucket.load called with block {block_name!r}",
                file=sys.stderr,
            )
            return mock_bucket

        mock_load.side_effect = load_side_effect
        print("DEBUG: S3Bucket.load patched", file=sys.stderr)
        yield

    # After test, print call info
    if mock_bucket.get_directory.called:
        print(
            f"DEBUG: get_directory was called {mock_bucket.get_directory.call_count} times",
            file=sys.stderr,
        )
    else:
        print("DEBUG: get_directory was NOT called", file=sys.stderr)
