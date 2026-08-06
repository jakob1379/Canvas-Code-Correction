from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from canvas_code_correction.storage.rustfs_provisioning import (
    RustfsProvisioningError,
    RustfsStorageConfig,
    build_bucket_name,
    delete_stale_objects,
    upload_directory_with_credentials,
)

STORAGE = RustfsStorageConfig(
    endpoint_url="http://localhost:9000",
    region_name="us-east-1",
    aws_access_key_id="SHAREDKEY",
    aws_secret_access_key="SHAREDSECRET",  # noqa: S106
)


def test_build_bucket_name_truncates_long_values() -> None:
    long_name = "ccc-assets-" + ("abc123" * 20)

    bucket_name = build_bucket_name(long_name)

    assert len(bucket_name) <= 63
    assert bucket_name.startswith("ccc-assets-")


def _client_listing(*pages: list[str]) -> MagicMock:
    client = MagicMock()
    client.get_paginator.return_value.paginate.return_value = [
        {"Contents": [{"Key": key} for key in page]} for page in pages
    ]
    client.delete_objects.return_value = {}
    return client


@patch("canvas_code_correction.storage.rustfs_provisioning.build_s3_client")
def test_delete_stale_objects_keeps_fresh_keys_across_pages(mock_client: MagicMock) -> None:
    client = _client_listing(["a/keep.sh", "a/stale1.sh"], ["a/keep2.sh", "a/stale2.sh"])
    mock_client.return_value = client

    deleted = delete_stale_objects(
        STORAGE,
        "bucket",
        "a",
        keep={"a/keep.sh", "a/keep2.sh"},
    )

    assert deleted == 2
    assert [
        obj["Key"]
        for call in client.delete_objects.call_args_list
        for obj in call.kwargs["Delete"]["Objects"]
    ] == ["a/stale1.sh", "a/stale2.sh"]


@patch("canvas_code_correction.storage.rustfs_provisioning.build_s3_client")
def test_delete_stale_objects_raises_on_delete_errors(mock_client: MagicMock) -> None:
    client = _client_listing(["a/stale.sh"])
    client.delete_objects.return_value = {"Errors": [{"Key": "a/stale.sh", "Code": "AccessDenied"}]}
    mock_client.return_value = client

    with pytest.raises(RustfsProvisioningError, match="failed to delete 1 stale object"):
        delete_stale_objects(STORAGE, "bucket", "a", keep=set())


@patch("canvas_code_correction.storage.rustfs_provisioning.S3Bucket")
def test_upload_directory_with_credentials_wraps_prefect_aws_errors(
    mock_s3_bucket: MagicMock,
    tmp_path: Path,
) -> None:
    work_package_root = tmp_path / "pkg"
    work_package_root.mkdir()
    mock_bucket = MagicMock()
    mock_bucket.put_directory.side_effect = RuntimeError("upload failed")
    mock_s3_bucket.return_value = mock_bucket

    with pytest.raises(RustfsProvisioningError, match="failed to upload directory"):
        upload_directory_with_credentials(
            STORAGE,
            bucket_name="ccc-assets-course-123",
            local_path=work_package_root,
            to_path="graders/course-123/assignments/1",
        )
