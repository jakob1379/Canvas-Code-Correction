"""RustFS-backed S3 provisioning helpers for shared environment storage access."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from botocore.exceptions import ClientError, EndpointConnectionError
from prefect_aws import AwsClientParameters, AwsCredentials
from prefect_aws.s3 import S3Bucket
from pydantic import SecretStr

if TYPE_CHECKING:
    from collections.abc import MutableMapping
    from pathlib import Path

DEFAULT_AWS_REGION = "us-east-1"
BUCKET_NAME_LIMIT = 63


class RustfsProvisioningError(RuntimeError):
    """Raised when RustFS S3 provisioning fails."""


@dataclass(frozen=True)
class RustfsStorageConfig:
    """Shared S3 configuration used for setup-time RustFS operations."""

    endpoint_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
    region_name: str = DEFAULT_AWS_REGION


def build_bucket_name(block_name: str) -> str:
    """Return a valid S3-compatible bucket name from a generated block name."""
    bucket_name = block_name.lower()
    if len(bucket_name) <= BUCKET_NAME_LIMIT:
        return bucket_name
    digest = hashlib.sha256(bucket_name.encode("utf-8")).hexdigest()[:8]
    return f"{bucket_name[:54]}-{digest}"


def build_credentials(storage: RustfsStorageConfig) -> AwsCredentials:
    """Return the prefect-aws credentials block for a RustFS endpoint."""
    return AwsCredentials(
        aws_access_key_id=storage.aws_access_key_id,
        aws_secret_access_key=SecretStr(storage.aws_secret_access_key),
        region_name=storage.region_name,
        aws_client_parameters=AwsClientParameters(
            endpoint_url=storage.endpoint_url,
            config={"signature_version": "s3v4"},
        ),
    )


def build_s3_client(storage: RustfsStorageConfig) -> Any:  # noqa: ANN401 - botocore client
    """Return a boto3 S3 client pointed at the RustFS endpoint."""
    return build_credentials(storage).get_s3_client()


def seed_ambient_storage_env(environ: MutableMapping[str, str]) -> dict[str, str]:
    """Mirror operator-set ``RUSTFS_*`` credentials into the ``AWS_*`` names boto3 reads.

    Only mirrors values that are actually present, and never overwrites an existing
    ``AWS_*`` value, so an IAM role or ``~/.aws`` profile still wins when ``RUSTFS_*``
    is unset. Returns the variables it set.
    """
    access_key = environ.get("RUSTFS_ACCESS_KEY")
    secret_key = environ.get("RUSTFS_SECRET_KEY")
    if not access_key or not secret_key:
        return {}

    region = environ.get("AWS_REGION") or environ.get("AWS_DEFAULT_REGION") or DEFAULT_AWS_REGION
    applied: dict[str, str] = {}
    for key, value in (
        ("AWS_ACCESS_KEY_ID", access_key),
        ("AWS_SECRET_ACCESS_KEY", secret_key),
        ("AWS_REGION", region),
        ("AWS_DEFAULT_REGION", region),
    ):
        if key not in environ:
            environ[key] = value
            applied[key] = value
    return applied


def _bucket_owner_kwargs(endpoint_url: str) -> dict[str, str]:
    bucket_owner = os.getenv("AWS_BUCKET_OWNER")
    if bucket_owner and "amazonaws.com" in endpoint_url:
        return {"ExpectedBucketOwner": bucket_owner}
    return {}


def create_course_bucket(storage: RustfsStorageConfig, bucket_name: str) -> None:
    """Create the course bucket if it does not already exist."""
    client = build_s3_client(storage)
    owner_kwargs = _bucket_owner_kwargs(storage.endpoint_url)
    try:
        client.head_bucket(Bucket=bucket_name, **owner_kwargs)
    except EndpointConnectionError as exc:
        msg = f"could not reach S3 endpoint {storage.endpoint_url}: {exc}"
        raise RustfsProvisioningError(msg) from exc
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code not in {"404", "NoSuchBucket", "NotFound"}:
            msg = f"failed checking bucket {bucket_name}: {exc}"
            raise RustfsProvisioningError(msg) from exc
    else:
        return

    create_kwargs: dict[str, object] = {"Bucket": bucket_name, **owner_kwargs}
    if "amazonaws.com" in storage.endpoint_url and storage.region_name != DEFAULT_AWS_REGION:
        create_kwargs["CreateBucketConfiguration"] = {
            "LocationConstraint": storage.region_name,
        }

    try:
        client.create_bucket(**create_kwargs)
    except ClientError as exc:
        msg = f"failed to create bucket {bucket_name}: {exc}"
        raise RustfsProvisioningError(msg) from exc


def verify_course_runtime_access(
    storage: RustfsStorageConfig,
    bucket_name: str,
    *,
    expected_prefix: str | None = None,
) -> None:
    """Verify the shared runtime credential can access the bucket."""
    client = build_s3_client(storage)
    list_kwargs: dict[str, object] = {"Bucket": bucket_name, "MaxKeys": 1}
    if expected_prefix:
        list_kwargs["Prefix"] = expected_prefix.strip("/") + "/"
    try:
        client.list_objects_v2(**list_kwargs)
    except ClientError as exc:
        msg = f"shared RustFS credential could not access bucket {bucket_name}: {exc}"
        raise RustfsProvisioningError(msg) from exc


def delete_stale_objects(
    storage: RustfsStorageConfig,
    bucket_name: str,
    prefix: str,
    *,
    keep: set[str],
) -> int:
    """Delete objects under ``prefix`` that are not in ``keep``, returning the count.

    Callers upload first and prune afterwards, so an upload that fails part way
    never leaves the prefix empty.
    """
    client = build_s3_client(storage)
    normalized_prefix = f"{prefix.strip('/')}/"
    deleted = 0
    try:
        for page in client.get_paginator("list_objects_v2").paginate(
            Bucket=bucket_name,
            Prefix=normalized_prefix,
        ):
            stale = [
                {"Key": obj["Key"]} for obj in page.get("Contents", []) if obj["Key"] not in keep
            ]
            if not stale:
                continue
            response = client.delete_objects(Bucket=bucket_name, Delete={"Objects": stale})
            errors = response.get("Errors", [])
            if errors:
                msg = f"failed to delete {len(errors)} stale object(s): {errors[0]}"
                raise RustfsProvisioningError(msg)
            deleted += len(stale)
    except ClientError as exc:
        msg = f"failed pruning s3://{bucket_name}/{normalized_prefix}: {exc}"
        raise RustfsProvisioningError(msg) from exc
    return deleted


def upload_directory_with_credentials(
    storage: RustfsStorageConfig,
    *,
    bucket_name: str,
    local_path: Path,
    to_path: str,
) -> int:
    """Upload a local directory tree using the shared RustFS S3 credential."""
    s3_block = S3Bucket(bucket_name=bucket_name, credentials=build_credentials(storage))
    try:
        return cast("int", s3_block.put_directory(local_path=str(local_path), to_path=to_path))
    except Exception as exc:  # pragma: no cover - prefect_aws boundary
        msg = f"failed to upload directory {local_path} to s3://{bucket_name}/{to_path}: {exc}"
        raise RustfsProvisioningError(msg) from exc
